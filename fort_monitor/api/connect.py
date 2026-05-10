from __future__ import annotations

import logging
from typing import Any

import aiohttp

from fort_monitor.api.http import FortMonitorHttpClient
from fort_monitor.schemas.config import FortMonitorConfig


class FortMonitorConnect:
    def __init__(self, client: FortMonitorHttpClient | str):
        self._owns_client = isinstance(client, str)
        self._client = self._build_client(client)
        self.logger = logging.getLogger("fort_monitor_connect")

    async def connect(
        self,
        login: str,
        password: str,
        lang: str = "ru-ru",
        timezone: int = 0,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Метод используется для открытия сессии взаимодействия с сервером. Любая сессия взаимодействия может проводиться только поcле авторизации пользователя.

        Ответ: "Ok" - при успешном подключении (Ok - в англ.раскладке) или текст ошибки на языке заданном в параметре lang

        В ответе вернутся cookie и заголовок SessionId в http-headers. К каждому последующему запросу необходимо прикреплять либо http-header, либо cookie

        Args:
            login (str):
            password (str):
            lang (str, optional): Defaults to "ru-ru".
            timezone (int, optional): Defaults to 0.

        Returns:
            tuple[dict[str, str], dict[str, Any]]: Headers and cookies
        """
        self.logger.info("Connect to fort monitor")
        await self._client.open()
        tokens = await self._client.authenticate(
            login=login,
            password=password,
            lang=lang,
            timezone=timezone,
        )
        await self._close_owned_client()
        return tokens.headers, tokens.cookies

    async def ping(self, session: aiohttp.ClientSession | None = None) -> bool:
        """Проверка, активна ли сессия пользователя

        Args:
            session (aiohttp.ClientSession): Клиентская сессия

        Returns:
            bool: Если работает - True. Если нет - False.
        """
        self.logger.info("Check ping info session")
        if session is not None:
            return await self._legacy_ping(session)

        result = await self._client.request_text("GET", "ping")
        return self._is_success_text(result)

    async def disconnect(self, session: aiohttp.ClientSession | None = None) -> None:
        """Метод используется для закрытия текущей сессии пользователя. Ответ: "Ok" - при успешном подключении (Ok - в англ.раскладке) или текст ошибки

        Args:
            session (aiohttp.ClientSession): Клиентская сессия
        """
        self.logger.info("Disconnect from fort monitor")
        if session is not None:
            await self._legacy_disconnect(session)
            return

        await self._client.disconnect()

    def _build_client(self, client: FortMonitorHttpClient | str) -> FortMonitorHttpClient:
        if isinstance(client, FortMonitorHttpClient):
            return client
        return FortMonitorHttpClient(FortMonitorConfig(base_url=client))

    async def _close_owned_client(self) -> None:
        if self._owns_client:
            await self._client.close()

    async def _legacy_ping(self, session: aiohttp.ClientSession) -> bool:
        async with session.get("ping") as response:
            self.logger.info("Status response: %r", response.status)
            response.raise_for_status()
            result = await response.text()
            return self._is_success_text(result)

    async def _legacy_disconnect(self, session: aiohttp.ClientSession) -> None:
        async with session.get("disconnect/") as response:
            self.logger.info("Status response: %r", response.status)
            response.raise_for_status()

    def _is_success_text(self, value: str) -> bool:
        return value.strip().lower() in {"ok", "true", "1"}
