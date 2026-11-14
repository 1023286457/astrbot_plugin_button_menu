"""Button-menu data model, validation and pagination."""

from __future__ import annotations

import math
from typing import Any

DEFAULT_MENU: dict[str, Any] = {
    "title": "淼淼菜单",
    "subtitle": "请点击下方按钮选择功能~",
    "footer": "点击按钮直接触发对应功能",
    "columns": 2,
    "page_size": 8,
    "show_description": True,
    "bot_mode": "all",
    "enabled_bots": [],
    "buttons": [
        {"label": "功能列表", "type": "text", "text": "/功能列表", "description": "查看功能列表"},
        {"label": "使用指南", "type": "text", "text": "/使用指南", "description": "查看使用指南"},
        {"label": "群管面板", "type": "text", "text": "/群管面板", "description": "打开群管面板"},
        {"label": "群管帮助", "type": "text", "text": "/群管帮助", "description": "查看群管帮助"},
        {"label": "运行状态", "type": "text", "text": "/状态", "description": "查看运行状态"},
        {"label": "获取帮助", "type": "text", "text": "/帮助", "description": "获取帮助"},
    ],
}

MAX_BUTTONS = 50
MAX_LABEL = 20
MAX_TEXT = 2000
MAX_DESCRIPTION = 60
ACTION_TYPES = {"text", "image", "link"}


def _text(value: Any, limit: int, default: str = "") -> str:
    text = str(value or "").strip()
    return (text or default)[:limit]


def _int(value: Any, default: int, low: int, high: int) -> int:
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default
    return max(low, min(high, number))


def normalize(raw: Any) -> dict[str, Any]:
    data = raw if isinstance(raw, dict) else {}
    buttons: list[dict[str, Any]] = []
    source = data.get("buttons") if isinstance(data.get("buttons"), list) else []
    for item in source[:MAX_BUTTONS]:
        if not isinstance(item, dict):
            continue
        label = _text(item.get("label"), MAX_LABEL)
        action_type = str(item.get("type") or "text").strip().lower()
        if action_type not in ACTION_TYPES:
            action_type = "text"
        # 兼容 1.0.x 的 command 字段
        text = _text(item.get("text") or item.get("command"), MAX_TEXT)
        url = _text(item.get("url"), 1000)
        image = str(item.get("image") or "")
        if not label:
            label = _text(text or url, MAX_LABEL, "按钮")
        if action_type == "text" and not text:
            continue
        if action_type == "link" and not url:
            continue
        buttons.append(
            {
                "label": label,
                "type": action_type,
                "text": text,
                "url": url,
                "image": image,
                "description": _text(item.get("description"), MAX_DESCRIPTION),
            }
        )
    return {
        "title": _text(data.get("title"), 40, "淼淼菜单"),
        "subtitle": _text(data.get("subtitle"), 80),
        "footer": _text(data.get("footer"), 80),
        "columns": _int(data.get("columns"), 2, 1, 5),
        "page_size": _int(data.get("page_size"), 8, 1, 20),
        "show_description": bool(data.get("show_description", True)),
        "bot_mode": "selected" if data.get("bot_mode") == "selected" else "all",
        "enabled_bots": [
            str(item)[:120]
            for item in (
                data.get("enabled_bots")
                if isinstance(data.get("enabled_bots"), list)
                else []
            )
            if str(item).strip()
        ][:50],
        "buttons": buttons,
    }


def paginate(config: dict[str, Any]) -> dict[str, Any]:
    buttons = config.get("buttons") or []
    columns = _int(config.get("columns"), 2, 1, 5)
    requested = _int(config.get("page_size"), 8, 1, 20)
    total = len(buttons)
    page_size = min(requested, columns * 5)
    pages = max(1, math.ceil(total / page_size)) if total else 1
    if pages > 1:
        page_size = min(page_size, columns * 4)
        pages = max(1, math.ceil(total / page_size))
    chunks = [buttons[index : index + page_size] for index in range(0, total, page_size)] or [[]]
    return {
        "total": total,
        "columns": columns,
        "page_size": page_size,
        "requested_page_size": requested,
        "pages": pages,
        "chunks": chunks,
    }
