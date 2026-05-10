from __future__ import annotations

import json
import logging
from typing import Any, Mapping
from urllib.parse import urljoin

import aiohttp

from fort_monitor.exceptions import (
    FortMonitorApiError,
    FortMonitorAuthenticationError,
    FortMonitorResponseError,
    FortMonitorSessionError,
    FortMonitorTransportError,
)
from fort_monitor.schemas.auth import AuthTokens
from fort_monitor.schemas.config import FortMonitorConfig


class FortMonitorHttpClient:
    """Small aiohttp wrapper with FortMonitor-specific errors and logging."""

    def __init__(
        self,
        config: FortMonitorConfig,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._logger = logger or logging.getLogger("fort_monitor.http")
        self._session: aiohttp.ClientSession | None = None

    @property
    def config(self) -> FortMonitorConfig:
        return self._config

    async def open(self) -> None:
        if self._session and not self._session.closed:
            return

        timeout = aiohttp.ClientTimeout(total=self._config.timeout)
        cookie_jar = aiohttp.CookieJar(unsafe=True)
        self._session = aiohttp.ClientSession(timeout=timeout, cookie_jar=cookie_jar)
        self._logger.debug("FortMonitor HTTP session opened")

    async def authenticate(
        self,
        login: str,
        password: str,
        *,
        lang: str | None = None,
        timezone: int | None = None,
    ) -> AuthTokens:
        payload = self._auth_payload(
            login=login,
            password=password,
            lang=lang,
            timezone=timezone,
        )
        self._logger.info("Authenticating FortMonitor session", extra={"login": login})
        response = await self.request_raw("POST", "connect/", json_body=payload)
        body = (await response.text()).strip()
        self._raise_for_auth_body(body)
        tokens = self._extract_tokens(response)
        self._apply_auth_headers(tokens.headers)
        self._logger.info("FortMonitor session authenticated")
        return tokens

    async def disconnect(self) -> None:
        if not self._session or self._session.closed:
            return

        self._logger.info("Disconnecting FortMonitor session")
        await self.request_text("GET", "disconnect/")

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()
            self._logger.debug("FortMonitor HTTP session closed")

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> Any:
        text = await self.request_text(
            method,
            path,
            params=params,
            json_body=json_body,
            data=data,
        )
        return self._parse_json(text)

    async def request_json_object(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        parsed = await self.request_json(
            method,
            path,
            params=params,
            json_body=json_body,
            data=data,
        )
        if isinstance(parsed, dict):
            return parsed
        message = "FortMonitor JSON response is not an object"
        raise FortMonitorResponseError(message, payload=parsed)

    async def request_text(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> str:
        response = await self.request_raw(
            method,
            path,
            params=params,
            json_body=json_body,
            data=data,
        )
        return await response.text()

    async def request_raw(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json_body: Mapping[str, Any] | None = None,
        data: Mapping[str, Any] | None = None,
    ) -> aiohttp.ClientResponse:
        session = self._require_session()
        url = self._build_url(path)
        self._log_request(method=method, url=url, params=params)
        try:
            response = await session.request(
                method,
                url,
                params=params,
                json=json_body,
                data=data,
            )
        except aiohttp.ClientError as exc:
            raise FortMonitorTransportError(str(exc)) from exc

        await self._raise_for_status(response)
        return response

    def _auth_payload(
        self,
        login: str,
        password: str,
        lang: str | None,
        timezone: int | None,
    ) -> dict[str, str | int]:
        return {
            "login": login,
            "password": password,
            "lang": lang or self._config.lang,
            "timezone": self._config.timezone if timezone is None else timezone,
        }

    def _build_url(self, path: str) -> str:
        return urljoin(self._config.base_url, path.lstrip("/"))

    def _require_session(self) -> aiohttp.ClientSession:
        if self._session and not self._session.closed:
            return self._session
        raise FortMonitorSessionError("FortMonitor HTTP session is not opened")

    def _extract_tokens(self, response: aiohttp.ClientResponse) -> AuthTokens:
        headers: dict[str, str] = {}
        session_id = response.headers.get("SessionId")
        if session_id:
            headers["SessionId"] = session_id

        cookies = {key: value.value for key, value in response.cookies.items()}
        return AuthTokens(headers=headers, cookies=cookies)

    def _apply_auth_headers(self, headers: Mapping[str, str]) -> None:
        session = self._require_session()
        for key, value in headers.items():
            session.headers[key] = value

    def _parse_json(self, text: str) -> Any:
        try:
            return json.loads(text or "{}")
        except json.JSONDecodeError as exc:
            message = "FortMonitor returned a non-JSON response"
            raise FortMonitorResponseError(message, payload=text) from exc

    def _raise_for_auth_body(self, body: str) -> None:
        body = body.replace('"', "").lower()
        if not body or body.lower() == "ok":
            return

        message = "FortMonitor authentication failed"
        raise FortMonitorAuthenticationError(message, payload=body)

    async def _raise_for_status(self, response: aiohttp.ClientResponse) -> None:
        if response.status < 400:
            return

        payload = await response.text()
        message = f"FortMonitor HTTP request failed with status {response.status}"
        if response.status in {401, 403}:
            raise FortMonitorAuthenticationError(
                message,
                status=response.status,
                payload=payload,
            )
        raise FortMonitorApiError(message, status=response.status, payload=payload)

    def _log_request(
        self,
        *,
        method: str,
        url: str,
        params: Mapping[str, Any] | None,
    ) -> None:
        self._logger.debug(
            "FortMonitor HTTP request",
            extra={"method": method, "url": url, "params": dict(params or {})},
        )
