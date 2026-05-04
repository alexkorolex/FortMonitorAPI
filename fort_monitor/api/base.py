from __future__ import annotations

import logging
from types import TracebackType
from typing import Any

from fort_monitor.api.connect import FortMonitorConnect
from fort_monitor.api.http import FortMonitorHttpClient
from fort_monitor.api.objects import FortMonitorObjects
from fort_monitor.schemas.config import FortMonitorConfig


class FortMonitor:
    def __init__(
        self,
        login: str,
        password: str,
        *,
        config: FortMonitorConfig | None = None,
        base_url: str | None = None,
        timeout: float | None = None,
        lang: str | None = None,
        timezone: int | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self.login = login
        self.password = password
        self.config = self._build_config(config, base_url, timeout, lang, timezone)
        self.logger = logger or logging.getLogger("fort_monitor")

        self._http = FortMonitorHttpClient(self.config, self.logger)
        self.fort_monitor_connect = FortMonitorConnect(self._http)
        self.objects = FortMonitorObjects(self._http)

    async def __aenter__(self) -> "FortMonitor":
        return await self.start()

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool:
        if exc is not None:
            self._handle_error("exception inside context", exc_type, exc, tb)

        try:
            await self.close()
        except Exception as close_error:
            self._handle_error("close failed", type(close_error), close_error, None)
            if exc is None:
                raise
        return False

    async def start(self) -> "FortMonitor":
        self.logger.info("FortMonitor: opening session")
        await self._http.open()
        try:
            await self._http.authenticate(self.login, self.password)
        except Exception as exc:
            self._handle_error("connect failed", type(exc), exc, exc.__traceback__)
            await self._http.close()
            raise
        self.logger.info("FortMonitor: session opened")
        return self

    async def close(self) -> None:
        try:
            await self.fort_monitor_connect.disconnect()
        finally:
            await self._http.close()

    async def ping(self) -> bool:
        return await self.fort_monitor_connect.ping()

    async def request_json(self, method: str, path: str, **kwargs: Any) -> Any:
        return await self._http.request_json(method, path, **kwargs)

    async def request_text(self, method: str, path: str, **kwargs: Any) -> str:
        return await self._http.request_text(method, path, **kwargs)

    def _handle_error(
        self,
        message: str,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.logger.error(
            "FortMonitor error: %s",
            message,
            exc_info=(exc_type, exc, tb) if exc_type and exc and tb else None,
        )

    def _build_config(
        self,
        config: FortMonitorConfig | None,
        base_url: str | None,
        timeout: float | None,
        lang: str | None,
        timezone: int | None,
    ) -> FortMonitorConfig:
        if config is not None:
            return config

        defaults = FortMonitorConfig()
        return FortMonitorConfig(
            base_url=base_url or defaults.base_url,
            timeout=timeout if timeout is not None else defaults.timeout,
            lang=lang or defaults.lang,
            timezone=defaults.timezone if timezone is None else timezone,
        )
