"""A small WebUI-configurable button menu for QQ official bots."""

from __future__ import annotations

import asyncio
import hashlib
import re
from typing import Any

from astrbot.api import AstrBotConfig, logger
from astrbot.api.event import AstrMessageEvent, filter
from astrbot.api.star import Context, Star, StarTools, register

from .dashboard import MenuDashboard
from .menu_model import paginate
from .menu_store import MenuStore
from .qq_api import QQMenuAPI

try:
    from astrbot.api.message_components import Json
except ImportError:  # pragma: no cover - older AstrBot
    try:
        from astrbot.core.message.components import Json  # type: ignore
    except ImportError:
        Json = None  # type: ignore[assignment]

PLUGIN_NAME = "astrbot_plugin_button_menu"
PLUGIN_DISPLAY_NAME = "QQ官机按钮菜单"
PLUGIN_VERSION = "1.0.1"
QQ_BOT_PLATFORMS = {
    "qq_official",
    "qq_official_webhook",
}
QQ_STANDARD_BOTS = {"qq_official", "qq_official_webhook"}


@register(
    PLUGIN_NAME,
    "简单么么熊",
    "可视化配置 QQ 官方群聊按钮菜单与预设指令",
    PLUGIN_VERSION,
)
class ButtonMenu(Star):
    def __init__(self, context: Context, config: AstrBotConfig) -> None:
        super().__init__(context)
        self.config = config
        data_dir = StarTools.get_data_dir(PLUGIN_NAME)
        self.store = MenuStore(data_dir / "menu.json")
        self.dashboard = MenuDashboard(self)
        self._patched: dict[str, dict[str, Any]] = {}
        try:
            self.dashboard.register()
        except Exception:
            logger.exception("[%s] 注册按钮菜单 WebUI 失败", PLUGIN_NAME)

    async def terminate(self) -> None:
        for state in self._patched.values():
            client = state.get("client")
            if client is not None:
                setattr(client, "on_interaction_create", state.get("original"))
        self._patched.clear()
        try:
            self.dashboard.unregister()
        except Exception:
            logger.exception("[%s] 注销按钮菜单 WebUI 失败", PLUGIN_NAME)

    def _enabled(self) -> bool:
        return bool(self.config.get("enable_button_menu", True))

    def available_bots(self) -> list[dict[str, str]]:
        """List QQ bot instances that can be selected in the WebUI."""
        result: list[dict[str, str]] = []
        manager = getattr(self.context, "platform_manager", None)
        instances = getattr(manager, "platform_insts", None) or []
        for instance in instances:
            try:
                meta = instance.meta()
                name = str(getattr(meta, "name", "") or "")
                if name not in QQ_BOT_PLATFORMS:
                    continue
                bot_id = str(getattr(meta, "id", "") or "")
                if not bot_id or any(item["id"] == bot_id for item in result):
                    continue
                result.append(
                    {
                        "id": bot_id,
                        "name": str(
                            getattr(meta, "adapter_display_name", "")
                            or name
                        ),
                        "platform": name,
                    }
                )
            except Exception:
                continue
        return result

    def _bot_allowed(self, event: AstrMessageEvent) -> bool:
        config = self.store.load()
        if config.get("bot_mode") != "selected":
            return True
        return event.get_platform_id() in set(config.get("enabled_bots") or [])

    def _platform(self, event: AstrMessageEvent) -> Any:
        return self.context.get_platform_inst(event.get_platform_id())

    def _patch_interactions(self) -> None:
        manager = getattr(self.context, "platform_manager", None)
        for platform in getattr(manager, "platform_insts", None) or []:
            try:
                meta = platform.meta()
                if meta.name not in QQ_BOT_PLATFORMS:
                    continue
                client = getattr(platform, "client", None)
                if client is None or meta.id in self._patched:
                    continue
                original = getattr(client, "on_interaction_create", None)

                async def handler(
                    interaction: Any,
                    pid: str = meta.id,
                    previous: Any = original,
                ) -> None:
                    if await self._handle_menu_interaction(pid, interaction):
                        return
                    if previous is not None:
                        result = previous(interaction)
                        if hasattr(result, "__await__"):
                            await result

                setattr(client, "on_interaction_create", handler)
                self._patched[meta.id] = {"client": client, "original": original}
            except Exception:
                logger.exception("[%s] 挂载按钮回调失败", PLUGIN_NAME)

    async def _handle_menu_interaction(
        self, platform_id: str, interaction: Any
    ) -> bool:
        resolved = getattr(getattr(interaction, "data", None), "resolved", None)
        data = str(getattr(resolved, "button_data", "") or "")
        if not data.startswith("qqmenu:"):
            return False
        platform = self.context.get_platform_inst(platform_id)
        if platform is None or getattr(platform, "client", None) is None:
            return True
        api = QQMenuAPI(platform.client)
        interaction_id = str(getattr(interaction, "id", "") or "")
        if not interaction_id:
            return True

        async def ack(code: int) -> None:
            try:
                await asyncio.wait_for(
                    api.acknowledge_interaction(interaction_id, code), 3
                )
            except Exception:
                logger.exception("[%s] 回应菜单按钮失败", PLUGIN_NAME)

        group = str(getattr(interaction, "group_openid", "") or "")
        sender = str(getattr(interaction, "group_member_openid", "") or "")
        if (
            not group
            or not sender
            or getattr(interaction, "type", None) != 11
            or getattr(interaction, "chat_type", None) != 1
        ):
            await ack(4)
            return True
        if data.startswith("qqmenu_page:"):
            try:
                page = int(data.split(":", 1)[1])
            except (TypeError, ValueError):
                await ack(1)
                return True
            await ack(0)
            config = self.store.load()
            layout = paginate(config)
            card = self._card(config, layout, page)
            try:
                await api.send_group_markdown(
                    group,
                    str(card["markdown"]["content"]),
                    keyboard=card["keyboard"],
                )
            except Exception:
                logger.exception("[%s] 菜单翻页发送失败", PLUGIN_NAME)
            return True
        token = data.split(":", 1)[1]
        button = next(
            (
                item
                for item in self.store.load().get("buttons", [])
                if self._token(item) == token
            ),
            None,
        )
        if button is None:
            await ack(1)
            return True
        await ack(0)
        try:
            await self._send_action(api, group, button)
        except Exception:
            logger.exception("[%s] 发送按钮内容失败", PLUGIN_NAME)
        return True

    async def _send_action(
        self, api: QQMenuAPI, group: str, button: dict[str, Any]
    ) -> None:
        action_type = str(button.get("type") or "text")
        if action_type == "image":
            image = str(button.get("image") or "")
            if "," in image and image.startswith("data:"):
                image = image.split(",", 1)[1]
            if not image:
                raise ValueError("图片内容为空")
            uploaded = await asyncio.wait_for(
                api.upload_group_image(group, "menu-image.png", image), 20
            )
            file_info = (
                str(uploaded.get("file_info") or "")
                if isinstance(uploaded, dict)
                else ""
            )
            if not file_info:
                raise RuntimeError("图片上传没有返回 file_info")
            await asyncio.wait_for(api.send_group_media(group, file_info), 15)
            return
        if action_type == "link":
            content = f"{button.get('label') or '链接'}\n{button.get('url') or ''}".strip()
        else:
            content = str(button.get("text") or "")
        if not content:
            raise ValueError("文本内容为空")
        await api.send_group_text(group, content)

    @staticmethod
    def _page_arg(event: AstrMessageEvent, value: str = "") -> int:
        text = str(value or "").strip()
        if not text:
            match = re.search(r"(?:^|\s)(\d{1,3})\s*$", event.get_message_str())
            text = match.group(1) if match else "1"
        try:
            return max(1, int(text))
        except (TypeError, ValueError):
            return 1

    @staticmethod
    def _token(item: dict[str, Any]) -> str:
        material = "|".join(
            str(item.get(key) or "")
            for key in ("label", "type", "text", "url", "image")
        )
        return hashlib.sha1(material.encode("utf-8")).hexdigest()[:16]

    @classmethod
    def _button(cls, item: dict[str, Any], style: int = 1) -> dict[str, Any]:
        return {
            "id": f"menu-{cls._token(item)}",
            "render_data": {
                "label": str(item.get("label") or "按钮")[:20],
                "visited_label": str(item.get("label") or "按钮")[:20],
                "style": style,
            },
            "action": {
                "type": 1,
                "permission": {"type": 2},
                "data": f"qqmenu:{cls._token(item)}",
                "unsupport_tips": "请更新 QQ 客户端后点击按钮",
            },
        }

    @classmethod
    def _page_button(cls, label: str, page: int, style: int = 1) -> dict[str, Any]:
        return {
            "id": f"menu-page-{page}",
            "render_data": {
                "label": label,
                "visited_label": label,
                "style": style,
            },
            "action": {
                "type": 1,
                "permission": {"type": 2},
                "data": f"qqmenu_page:{page}",
                "unsupport_tips": "请更新 QQ 客户端后点击按钮",
            },
        }

    def _card(self, config: dict[str, Any], layout: dict[str, Any], page: int) -> dict[str, Any]:
        chunks = layout["chunks"]
        total_pages = max(1, int(layout["pages"]))
        page = max(1, min(page, total_pages))
        buttons = chunks[page - 1]
        columns = max(1, min(5, int(layout["columns"])))
        rows: list[dict[str, Any]] = []
        for index in range(0, len(buttons), columns):
            rows.append(
                {
                    "buttons": [
                        self._button(item)
                        for item in buttons[index : index + columns]
                    ]
                }
            )
        if total_pages > 1:
            nav = []
            if page > 1:
                nav.append(self._page_button("上一页", page - 1))
            nav.append(self._page_button(f"{page}/{total_pages}", page, style=0))
            if page < total_pages:
                nav.append(self._page_button("下一页", page + 1))
            rows.append({"buttons": nav})
        rows = rows[:5]
        markdown = [f"## {config['title']}"]
        if config.get("subtitle"):
            markdown.append(config["subtitle"])
        if total_pages > 1:
            markdown.append(f"第 {page}/{total_pages} 页 · 共 {layout['total']} 个功能")
        if config.get("show_description"):
            descriptions = [
                f"- **{item['label']}**：{item['description']}"
                for item in buttons
                if item.get("description")
            ]
            if descriptions:
                markdown.append("\n".join(descriptions))
        if config.get("footer"):
            markdown.append(config["footer"])
        return {
            "msg_type": 2,
            "markdown": {"content": "\n\n".join(markdown)},
            "keyboard": {"content": {"rows": rows}},
        }

    def _text_menu(self, config: dict[str, Any], layout: dict[str, Any], page: int) -> str:
        chunks = layout["chunks"]
        total_pages = max(1, int(layout["pages"]))
        page = max(1, min(page, total_pages))
        lines = [config["title"]]
        if config.get("subtitle"):
            lines.append(config["subtitle"])
        if total_pages > 1:
            lines.append(f"第 {page}/{total_pages} 页 · 共 {layout['total']} 个功能")
        for item in chunks[page - 1]:
            if item.get("type") == "image":
                value = "[图片]"
            elif item.get("type") == "link":
                value = str(item.get("url") or "")
            else:
                value = str(item.get("text") or "")
            description = f" · {item['description']}" if item.get("description") else ""
            lines.append(f"- {item['label']}：{value}{description}")
        if total_pages > 1:
            lines.append(f"翻页：/Astrbot菜单 <页码>（1-{total_pages}）")
        if config.get("footer"):
            lines.append(config["footer"])
        return "\n".join(lines)

    @filter.command("Astrbot菜单")
    async def button_menu_command(
        self, event: AstrMessageEvent, page: str = ""
    ) -> None:
        if not self._enabled():
            yield event.plain_result("Astrbot菜单已关闭。")
            return
        if not self._bot_allowed(event):
            return
        config = self.store.load()
        layout = paginate(config)
        if not config["buttons"]:
            yield event.plain_result("Astrbot菜单还没有配置按钮，请先在 WebUI 中添加。")
            return
        page_number = self._page_arg(event, page)
        card = self._card(config, layout, page_number)
        platform_name = event.get_platform_name()
        if platform_name in QQ_STANDARD_BOTS:
            platform = self._platform(event)
            if platform is not None and getattr(platform, "client", None) is not None:
                self._patch_interactions()
                try:
                    await QQMenuAPI(platform.client).send_group_markdown(
                        event.get_group_id(),
                        str(card["markdown"]["content"]),
                        keyboard=card["keyboard"],
                    )
                    event.stop_event()
                    return
                except Exception:
                    logger.exception(
                        "[%s] 发送按钮菜单失败，降级为文字菜单",
                        PLUGIN_NAME,
                    )
            yield event.plain_result(
                self._text_menu(config, layout, page_number)
            ).use_markdown(True)
            event.stop_event()
            return
        if Json is not None:
            try:
                yield event.chain_result([Json(card)])
                event.stop_event()
                return
            except Exception:
                logger.exception("[%s] 发送按钮卡片失败，降级为文字菜单", PLUGIN_NAME)
        yield event.plain_result(
            self._text_menu(config, layout, page_number)
        ).use_markdown(True)
        event.stop_event()
