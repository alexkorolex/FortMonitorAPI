import logging
from types import TracebackType
from typing import Optional, Type

import aiohttp

from fort_monitor.api.connect import FortMonitorConnect
from fort_monitor.api.objects import FortMonitorObjects


class FortMonitor:
    def __init__(self, login: str, password: str):
        self.host = "https://fort.psmgroup.ru/api/integration/v1/"
        self.login = login
        self.password = password

        self.session: aiohttp.ClientSession | None = None
        self.logger = logging.getLogger("fort_monitor")

        self.fort_monitor_connect = FortMonitorConnect(self.host)
        self.objects: FortMonitorObjects | None = None

    async def __aenter__(self):
        self.logger.info("FortMonitor: start connect")

        try:
            headers, cookies = await self.fort_monitor_connect.connect(
                login=self.login,
                password=self.password,
            )
            self.session = aiohttp.ClientSession(
                base_url=self.host,
                headers=headers,
                cookie_jar=aiohttp.CookieJar(unsafe=True),
                timeout=aiohttp.ClientTimeout(total=30),
            )
            self.session.cookie_jar.update_cookies(cookies)
            self.objects = FortMonitorObjects(self.session)
            self.logger.info("FortMonitor: connected successfully")
            return self

        except Exception as e:
            self._handle_error("connect failed", type(e), e, e.__traceback__)
            raise

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ):
        if exc is not None:
            self._handle_error("exception inside context", exc_type, exc, tb)

        try:
            if self.session and self.fort_monitor_connect:
                self.logger.info("FortMonitor: start disconnect")

                await self.fort_monitor_connect.disconnect(self.session)

                self.logger.info("FortMonitor: disconnected successfully")

        except Exception as disconnect_error:
            self._handle_error(
                "disconnect failed",
                type(disconnect_error),
                disconnect_error,
                disconnect_error.__traceback__,
            )

        finally:
            if self.session and not self.session.closed:
                await self.session.close()

        return False

    def _handle_error(
        self,
        message: str,
        exc_type: Optional[Type[BaseException]],
        exc: Optional[BaseException],
        tb: Optional[TracebackType],
    ):
        self.logger.error(
            "FortMonitor error: %s",
            message,
            exc_info=(exc_type, exc, tb) if exc_type and exc and tb else None,
        )
