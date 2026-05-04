from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any


@dataclass(slots=True)
class Object:
    id: int
    name: str
    groupId: int
    IMEI: str
    icon: str
    rotateIcon: bool
    iconHeight: int
    iconWidth: int
    status: int
    lat: float
    lon: float
    direction: float
    move: float
    lastData: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Object":
        return cls(
            id=int(data["id"]),
            name=str(data["name"]),
            groupId=int(data["groupId"]),
            IMEI=str(data["IMEI"]),
            icon=str(data["icon"]),
            rotateIcon=bool(data["rotateIcon"]),
            iconHeight=int(data["iconHeight"]),
            iconWidth=int(data["iconWidth"]),
            status=int(data["status"]),
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            direction=float(data["direction"]),
            move=float(data["move"]),
            lastData=str(data["lastData"]),
        )


@dataclass(slots=True)
class Sensor:
    sid: int
    dt: str
    ico: str
    name: str
    val: str
    st: int
    haveChart: bool

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Sensor":
        return cls(
            sid=int(data["sid"]),
            dt=str(data["dt"]),
            ico=str(data["ico"]),
            name=str(data["name"]),
            val=str(data["val"]),
            st=int(data["st"]),
            haveChart=bool(data["haveChart"]),
        )


@dataclass(slots=True)
class ObjectInfo:
    oid: str
    Name: str
    IMEI: str
    cid: int
    dt: str
    properties: list[dict[str, Any]]
    sensors: list[Sensor]
    result: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObjectInfo":
        return cls(
            oid=str(data["oid"]),
            Name=str(data["Name"]),
            IMEI=str(data["IMEI"]),
            cid=int(data["cid"]),
            dt=str(data["dt"]),
            properties=_dict_list(data.get("properties", [])),
            sensors=_sensor_list(data.get("sensors", [])),
            result=str(data.get("result", "")),
        )


@dataclass(slots=True)
class ObjectFull(ObjectInfo):
    parent_id: int
    name: str
    address: str
    obj_icon: str
    obj_icon_height: int
    obj_icon_width: int
    obj_icon_rotate: bool
    status: int
    lat: float
    lon: float
    direction: float
    move: float
    block_reason: int

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ObjectFull":
        info = ObjectInfo.from_dict(data)
        base_values = {item.name: getattr(info, item.name) for item in fields(info)}
        return cls(
            **base_values,
            parent_id=int(data["parent_id"]),
            name=str(data["name"]),
            address=str(data["address"]),
            obj_icon=str(data["obj_icon"]),
            obj_icon_height=int(data["obj_icon_height"]),
            obj_icon_width=int(data["obj_icon_width"]),
            obj_icon_rotate=bool(data["obj_icon_rotate"]),
            status=int(data["status"]),
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            direction=float(data["direction"]),
            move=float(data["move"]),
            block_reason=int(data["block_reason"]),
        )


@dataclass(slots=True)
class Coord:
    tm: str
    lat: float
    lon: float
    dir: float
    dst: float
    st: float
    speed: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Coord":
        return cls(
            tm=str(data["tm"]),
            lat=float(data["lat"]),
            lon=float(data["lon"]),
            dir=float(data["dir"]),
            dst=float(data["dst"]),
            st=float(data["st"]),
            speed=float(data["speed"]),
        )


@dataclass(slots=True)
class TrackInfo:
    oid: int
    coords: list[Coord]
    result: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TrackInfo":
        coords = [Coord.from_dict(row) for row in data.get("coords", [])]
        return cls(oid=int(data["oid"]), coords=coords, result=str(data["result"]))


@dataclass(slots=True)
class TreeNode:
    id: int
    parent_id: int
    real_id: int
    name: str
    leaf: bool
    status: int
    lat: float
    lon: float
    children: list["TreeNode"] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "TreeNode":
        children = [cls.from_dict(row) for row in data.get("children", [])]
        return cls(
            id=int(data["id"]),
            parent_id=int(data["parent_id"]),
            real_id=int(data["real_id"]),
            name=str(data["name"]),
            leaf=bool(data["leaf"]),
            status=int(data["status"]),
            lat=float(data.get("lat", 0.0)),
            lon=float(data.get("lon", 0.0)),
            children=children,
        )

    @classmethod
    def build_tree(cls, data: dict[str, Any]) -> list["TreeNode"]:
        return [cls.from_dict(node) for node in data.get("children", [])]

    @classmethod
    def build_tree_with_index(
        cls,
        data: dict[str, Any],
    ) -> tuple[list["TreeNode"], dict[int, "TreeNode"]]:
        index: dict[int, TreeNode] = {}
        roots = [cls._build_with_index(node, index) for node in data.get("children", [])]
        return roots, index

    @classmethod
    def _build_with_index(
        cls,
        data: dict[str, Any],
        index: dict[int, "TreeNode"],
    ) -> "TreeNode":
        node = cls.from_dict({**data, "children": []})
        index[node.real_id] = node
        node.children = [cls._build_with_index(row, index) for row in data.get("children", [])]
        return node


def _sensor_list(value: Any) -> list[Sensor]:
    if not isinstance(value, list):
        return []
    return [Sensor.from_dict(row) for row in value if isinstance(row, dict)]


def _dict_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]
