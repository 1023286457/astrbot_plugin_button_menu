"""WebUI API for the button menu editor."""

from __future__ import annotations

from typing import Any

from astrbot.api import logger

from .menu_model import paginate
from .menu_store import MenuStore

PLUGIN_NAME = "astrbot_plugin_button_menu"

try:  # AstrBot 4.26+
    from astrbot.api.web import error_response, json_response, request

    WEB_API_AVAILABLE = True
except Exception as exc:  # pragma: no cover - older hosts
    error_response = None  # type: ignore[assignment]
    json_response = None  # type: ignore[assignment]
    request = None  # type: ignore[assignment]
    WEB_API_AVAILABLE = False
    WEB_API_IMPORT_ERROR = str(exc)


class DashboardError(Exception):
    pass


class MenuDashboard:
    def __init__(self, plugin: Any) -> None:
        self.plugin = plugin
        self.context = plugin.context
        self.prefix = f"/{PLUGIN_NAME}/"

    def register(self) -> bool:
        if not WEB_API_AVAILABLE:
            logger.warning(
                "[%s] 当前 AstrBot 不支持 astrbot.api.web，按钮菜单 WebUI 不可用",
                PLUGIN_NAME,
            )
            return False
        register = getattr(self.context, "register_web_api", None)
        if not callable(register):
            return False
        registered = getattr(self.context, "registered_web_apis", None)
        if isinstance(registered, list):
            registered[:] = [
                item
                for item in registered
                if not str(item[0]).startswith(self.prefix)
            ]
        routes = (
            ("config", self.get_config, ["GET"], "读取按钮菜单配置"),
            ("save", self.save_config, ["POST"], "保存按钮菜单配置"),
        )
        for route, handler, methods, description in routes:
            register(f"{self.prefix}{route}", handler, methods, description)
        return True

    def unregister(self) -> None:
        registered = getattr(self.context, "registered_web_apis", None)
        if isinstance(registered, list):
            registered[:] = [
                item
                for item in registered
                if not str(item[0]).startswith(self.prefix)
            ]

    @staticmethod
    def _error(exc: Exception, fallback: str) -> Any:
        message = str(exc) if isinstance(exc, DashboardError) else fallback
        if not isinstance(exc, DashboardError):
            logger.exception("[button_menu] %s", fallback)
        return error_response(message, status_code=400)

    def _response(self, config: dict[str, Any]) -> dict[str, Any]:
        return {
            "ok": True,
            "config": config,
            "layout": paginate(config),
            "bots": self.plugin.available_bots(),
        }

    async def get_config(self) -> Any:
        try:
            return json_response(self._response(self.plugin.store.load()))
        except Exception as exc:
            return self._error(exc, "读取菜单配置失败")

    async def save_config(self) -> Any:
        try:
            payload = await request.json(default={})
            if not isinstance(payload, dict):
                raise DashboardError("请求格式不正确")
            config = self.plugin.store.save(payload)
            return json_response(self._response(config))
        except Exception as exc:
            return self._error(exc, "保存菜单配置失败")
