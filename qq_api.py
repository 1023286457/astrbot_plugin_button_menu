"""Minimal QQ official group API for sending a keyboard message."""

from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import quote, urlencode

from aiohttp import ClientTimeout
from botpy.http import Route, _handle_response


class QQBotRoute(Route):
    DOMAIN = "api.bot.qq.com"
    SANDBOX_DOMAIN = "sandbox.api.bot.qq.com"


class QQMenuAPI:
    def __init__(self, client: Any) -> None:
        self.client = client

    async def _request(
        self,
        method: str,
        path: str,
        *,
        payload: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> Any:
        if query:
            clean = {key: value for key, value in query.items() if value not in (None, "")}
            if clean:
                path = f"{path}?{urlencode(clean)}"
        route = QQBotRoute(method, path)
        http = self.client.api._http
        await http.check_session()
        route.is_sandbox = http.is_sandbox
        kwargs = {"json": payload} if payload is not None else {}
        async with http._session.request(
            method=route.method,
            url=route.url,
            headers=http._headers,
            timeout=ClientTimeout(total=http.timeout),
            **kwargs,
        ) as response:
            return await _handle_response(response)

    async def send_group_markdown(
        self,
        group_openid: str,
        content: str,
        *,
        keyboard: dict[str, Any] | None = None,
    ) -> Any:
        group_id = quote(group_openid, safe="")
        payload: dict[str, Any] = {
            "msg_type": 2,
            "markdown": {"content": content},
            "msg_seq": secrets.randbelow(9999) + 1,
        }
        if keyboard:
            payload["keyboard"] = keyboard
        return await self._request(
            "POST",
            f"/v2/groups/{group_id}/messages",
            payload=payload,
        )

    async def acknowledge_interaction(
        self, interaction_id: str, code: int = 0
    ) -> Any:
        return await self._request(
            "PUT",
            f"/interactions/{quote(interaction_id, safe='')}",
            payload={"code": code},
        )

    async def send_group_text(self, group_openid: str, content: str) -> Any:
        group_id = quote(group_openid, safe="")
        return await self._request(
            "POST",
            f"/v2/groups/{group_id}/messages",
            payload={
                "content": content,
                "msg_type": 0,
                "msg_seq": secrets.randbelow(9999) + 1,
            },
        )

    async def upload_group_image(
        self, group_openid: str, file_name: str, file_data: str
    ) -> Any:
        group_id = quote(group_openid, safe="")
        return await self._request(
            "POST",
            f"/v2/groups/{group_id}/files",
            payload={
                "file_type": 1,
                "file_name": file_name,
                "file_data": file_data,
                "srv_send_msg": False,
            },
        )

    async def send_group_media(self, group_openid: str, file_info: str) -> Any:
        group_id = quote(group_openid, safe="")
        return await self._request(
            "POST",
            f"/v2/groups/{group_id}/messages",
            payload={
                "msg_type": 7,
                "media": {"file_info": file_info},
                "msg_seq": secrets.randbelow(9999) + 1,
            },
        )
