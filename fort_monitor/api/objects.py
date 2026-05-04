from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Optional

from fort_monitor.api.http import FortMonitorHttpClient
from fort_monitor.exceptions import FortMonitorResponseError
from fort_monitor.schemas.objects import (
    Object,
    ObjectFull,
    ObjectInfo,
    TrackInfo,
    TreeNode,
)


class FortMonitorObjects:
    def __init__(self, client: FortMonitorHttpClient):
        self._client = client
        self.logger = logging.getLogger("fort_monitor_objects")
        self._date_time_format = "%Y-%m-%d %H:%M:%S"

    async def get_tree(self, all: bool = False) -> TreeNode:
        """Метод возвращает сгруппированный в дерево список доступных для пользователя объектов мониторинга.

        Args:
            all (bool, optional): в случае передачи true - будут возвращены объекты и группы всех компаний видимых пользователю, в случае передачи false - только родной компании пользователя. Defaults to False.

        Returns:
            TreeNode: Дерево доступных для пользователя объектов мониторинга
        """
        roots = await self.get_tree_roots(all=all)
        if not roots:
            raise FortMonitorResponseError("FortMonitor returned an empty object tree")
        return roots[0]

    async def get_tree_roots(self, all: bool = False) -> list[TreeNode]:
        self.logger.info("Get object tree", extra={"all_companies": all})
        raw = await self._client.request_json_object(
            "GET",
            "gettree/",
            params={"all": str(all).lower()},
        )
        children = raw.get("children", [])
        if not isinstance(children, list):
            raise FortMonitorResponseError("Invalid gettree response", payload=raw)
        return [TreeNode.from_dict(row) for row in children]

    async def get_objects_list(self, company_id: int = 0) -> list[Object]:
        """Запрос списка доступных объектов

        Args:
            company_id (int, optional): Id компании, для которой вернуть список объектов. 0 - вернуть полный доступный список объектов. Defaults to 0.

        Returns:
            list[Object]: Список объектов компании
        """
        self.logger.info("Get objects list", extra={"company_id": company_id})
        json_data = await self._client.request_json_object(
            "GET",
            "getobjectslist/",
            params={"companyId": company_id},
        )
        self._ensure_success_result(json_data)
        objects: list[dict[str, Any]] = json_data.get("objects", [])
        return [Object.from_dict(row) for row in objects]

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
        self.logger.info("Get object track", extra={"oid": oid})
        data = await self._client.request_json_object(
            "GET",
            "track/",
            params={
                "oid": oid,
                "from": self._format_datetime(start_time),
                "to": self._format_datetime(finish_time),
            },
        )
        self._ensure_success_result(data)
        return TrackInfo.from_dict(data=data)

    async def object_info(self, oid: int, dt: Optional[datetime] = None) -> ObjectInfo:
        """Метод возвращает информацию о состоянии объекта и сконфигурированных для него датчиков

        Args:
            oid (int): уникальный идентификатор объекта в базе данных (см. поле real_id в ответе метода gettree)
            dt (Optional[datetime], optional): необязательный параметр - дата-время в UTC (формат yyyy-MM-dd HH:mm:ss) для которого будет предоставлена информация (чтобы узнать последнюю информацию об объекте, заполнить значением 0001-01-01 00:00:00 или вообще не передавать параметр. Чтобы узнать значение на конкретный момент времени - заполнить нужным значением). Defaults to None.

        Returns:
            ObjectInfo: Информация о состоянии объекта
        """
        self.logger.info("Get object info", extra={"oid": oid})
        params: dict[str, str | int] = {
            "oid": oid,
        }
        if dt:
            params.update({"dt": self._format_datetime(dt)})
        data = await self._client.request_json_object(
            "GET",
            "objectinfo/",
            params=params,
        )
        self._ensure_success_result(data)
        return ObjectInfo.from_dict(data)

    async def full_object_info(self, oid: int) -> ObjectFull:
        """Метод возвращает детальные данные объекта включая датчики, местоположение и свойства объекта.

        Args:
            oid (int): уникальный идентификатор объекта в базе данных

        Returns:
            ObjectFull:  Детальные данные объекта
        """
        self.logger.info("Get full object info", extra={"oid": oid})
        data = await self._client.request_json_object(
            "GET",
            "fullobjinfo/",
            params={"oid": oid},
        )
        self._ensure_success_result(data)
        return ObjectFull.from_dict(data)

    def _format_datetime(self, value: datetime) -> str:
        return value.strftime(self._date_time_format)

    def _ensure_success_result(self, data: dict[str, Any]) -> None:
        result = data.get("result")
        if not isinstance(result, str) or result.lower() == "ok":
            return

        message = "FortMonitor API returned an unsuccessful result"
        raise FortMonitorResponseError(message, payload=data)
