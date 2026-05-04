import logging
from datetime import datetime
from typing import Any, Optional

import aiohttp

from fort_monitor.schemas.objects import (
    Object,
    ObjectFull,
    ObjectInfo,
    TrackInfo,
    TreeNode,
)


class FortMonitorObjects:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.logger = logging.getLogger("fort_monitor_objects")
        self.union_format_time = "%Y/%m/%d %H:%M:%S"

    async def get_tree(self, all: bool = False) -> TreeNode:
        """Метод возвращает сгруппированный в дерево список доступных для пользователя объектов мониторинга.

        Args:
            all (bool, optional): в случае передачи true - будут возвращены объекты и группы всех компаний видимых пользователю, в случае передачи false - только родной компании пользователя. Defaults to False.

        Returns:
            TreeNode: Дерево доступных для пользователя объектов мониторинга
        """
        self.logger.info("Get tree info objects")
        async with self.session.get(
            "gettree/",
            params={"all": str(all).lower()},
        ) as response:
            self.logger.info("Status response: %r", response.status)
            response.raise_for_status()
            raw = await response.json()
            data = raw["children"][0]
            tree = TreeNode.from_dict(data)
            return tree

    async def get_objects_list(self, company_id: int = 0) -> list[Object]:
        """Запрос списка доступных объектов

        Args:
            company_id (int, optional): Id компании, для которой вернуть список объектов. 0 - вернуть полный доступный список объектов. Defaults to 0.

        Returns:
            list[Object]: Список объектов компании
        """
        self.logger.info("Get objects list")
        async with self.session.get(
            "getobjectslist/",
            data={"companyId": company_id},
        ) as response:
            self.logger.info("Status response: %r", response.status)
            response.raise_for_status()

            json_data = await response.json()
            objects: list[dict[str, Any]] = json_data.get("objects", [])

            return [Object(**row) for row in objects]

    async def track(
        self, oid: int, start_time: datetime, finish_time: datetime
    ) -> TrackInfo:
        """Метод возвращает трек движения объекта за заданный промежуток времени

        Args:
            oid (int): уникальный идентификатор объекта в базе данных (см. поле real_id в ответе метода gettree)
            start_time (datetime): начало периода возвращаемых данных- дата-время в UTC (формат yyyy-MM-dd HH:mm:ss)
            finish_time (datetime): конец периода возвращаемых данных- дата-время в UTC (формат yyyy-MM-dd HH:mm:ss)

        Returns:
            TrackInfo: Информация о треке движения объекта
        """
        self.logger.info("Get full object info")
        async with self.session.get(
            "track/",
            params={
                "oid": oid,
                "from": start_time.strftime(format=self.union_format_time),
                "to": finish_time.strftime(format=self.union_format_time),
            },
        ) as response:
            self.logger.info("Status response: %r", response.status)
            response.raise_for_status()
            data = await response.json()
            track = TrackInfo.from_dict(data=data)
            return track

    async def object_info(self, oid: int, dt: Optional[datetime] = None) -> ObjectInfo:
        """Метод возвращает информацию о состоянии объекта и сконфигурированных для него датчиков

        Args:
            oid (int): уникальный идентификатор объекта в базе данных (см. поле real_id в ответе метода gettree)
            dt (Optional[datetime], optional): необязательный параметр - дата-время в UTC (формат yyyy-MM-dd HH:mm:ss) для которого будет предоставлена информация (чтобы узнать последнюю информацию об объекте, заполнить значением 0001-01-01 00:00:00 или вообще не передавать параметр. Чтобы узнать значение на конкретный момент времени - заполнить нужным значением). Defaults to None.

        Returns:
            ObjectInfo: Информация о состоянии объекта
        """
        self.logger.info("Get object info")
        params: dict[str, str | int] = {
            "oid": oid,
        }
        if dt:
            params.update({"dt": dt.strftime(format=self.union_format_time)})
        async with self.session.get(
            "objectinfo/",
            params=params,
        ) as response:
            self.logger.info("Status response: %r", response.status)
            response.raise_for_status()
            data = await response.json()
            return ObjectInfo.from_dict(data)

    async def full_object_info(self, oid: int) -> ObjectFull:
        """Метод возвращает детальные данные объекта включая датчики, местоположение и свойства объекта.

        Args:
            oid (int): уникальный идентификатор объекта в базе данных

        Returns:
            ObjectFull:  Детальные данные объекта
        """
        self.logger.info("Get full object info")
        async with self.session.get(
            "fullobjinfo/",
            params={"oid": oid},
        ) as response:
            self.logger.info("Status response: %r", response.status)
            response.raise_for_status()
            data = await response.json()
            return ObjectFull.from_dict(data)
