import logging
from typing import Any

import aiohttp


class FortMonitorConnect:
    def __init__(self, host: str):
        self.host = host
        self.logger = logging.getLogger("fort_monitor_connect")

    async def connect(
        self,
        login: str,
        password: str,
        lang: str = "ru",
        timezone: int = 0,
    ) -> tuple[dict[str, str], dict[str, Any]]:
        """Метод используется для открытия сессии взаимодействия с сервером. Любая сессия взаимодействия может проводиться только поcле авторизации пользователя.

        Ответ: "Ok" - при успешном подключении (Ok - в англ.раскладке) или текст ошибки на языке заданном в параметре lang

        В ответе вернутся cookie и заголовок SessionId в http-headers. К каждому последующему запросу необходимо прикреплять либо http-header, либо cookie

        Args:
            login (str):
            password (str):
            lang (str, optional): Defaults to "ru".
            timezone (int, optional): Defaults to 0.

        Returns:
            tuple[dict[str, str], dict[str, Any]]: Headers and cookies
        """
        data = {
            "login": login,
            "password": password,
            "lang": lang,
            "timezone": timezone,
        }

        self.logger.info("Connect to fort monitor")
        async with aiohttp.ClientSession(base_url=self.host) as session:
            async with session.post("connect/", json=data) as response:
                self.logger.info("Status response: %r", response.status)
                response.raise_for_status()

                headers = {}
                session_id = response.headers.get("SessionId")
                if session_id:
                    headers["SessionId"] = session_id

                cookies = {key: value.value for key, value in response.cookies.items()}
                return headers, cookies

    async def ping(self, session: aiohttp.ClientSession) -> bool:
        """Проверка, активна ли сессия пользователя

        Args:
            session (aiohttp.ClientSession): Клиентская сессия

        Returns:
            bool: Если работает - True. Если нет - False.
        """
        self.logger.info("Check ping info session")

        async with session.get("ping") as response:
            self.logger.info("Status response: %r", response.status)
            response.raise_for_status()

            result = await response.text()
            return bool(result)

    async def disconnect(self, session: aiohttp.ClientSession) -> None:
        """Метод используется для закрытия текущей сессии пользователя. Ответ: "Ok" - при успешном подключении (Ok - в англ.раскладке) или текст ошибки

        Args:
            session (aiohttp.ClientSession): Клиентская сессия
        """
        self.logger.info("Disconnect from fort monitor")
        async with session.get("disconnect/") as response:
            self.logger.info("Status response: %r", response.status)
            response.raise_for_status()
