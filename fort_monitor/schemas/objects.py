from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


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


@dataclass(slots=True)
class Sensor:
    sid: int
    dt: str
    ico: str
    name: str
    val: str
    st: int
    haveChart: bool


@dataclass(slots=True)
class ObjectInfo:
    oid: str
    Name: str
    IMEI: str
    cid: int
    dt: str
    properties: list
    sensors: list[Sensor]
    result: str

    @classmethod
    def from_dict(cls, data: dict) -> "ObjectInfo":
        return cls(
            oid=data["oid"],
            Name=data["Name"],
            IMEI=data["IMEI"],
            cid=data["cid"],
            dt=data["dt"],
            properties=data["properties"],
            sensors=[Sensor(**row) for row in data["sensors"]],
            result=data["result"],
        )


@dataclass(slots=True)
class ObjectFull:
    oid: str
    Name: str
    IMEI: str
    cid: int
    dt: str
    properties: list
    sensors: list[Sensor]
    result: str
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
    def from_dict(cls, data: dict) -> "ObjectFull":
        return cls(
            oid=data["oid"],
            Name=data["Name"],
            IMEI=data["IMEI"],
            cid=data["cid"],
            dt=data["dt"],
            properties=data["properties"],
            sensors=[Sensor(**row) for row in data["sensors"]],
            result=data["result"],
            parent_id=data["parent_id"],
            name=data["name"],
            address=data["address"],
            obj_icon=data["obj_icon"],
            obj_icon_height=data["obj_icon_height"],
            obj_icon_width=data["obj_icon_width"],
            obj_icon_rotate=data["obj_icon_rotate"],
            status=data["status"],
            lat=data["lat"],
            lon=data["lon"],
            direction=data["direction"],
            move=data["move"],
            block_reason=data["block_reason"],
        )


@dataclass(slots=True)
class TrackInfo:
    oid: int
    coords: list[Coord]
    result: str

    @classmethod
    def from_dict(cls, data: dict) -> "TrackInfo":
        return cls(
            oid=data["oid"],
            coords=[Coord(**row) for row in data["coords"]],
            result=data["result"],
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

    children: Optional[list["TreeNode"]] = None

    @classmethod
    def from_dict(cls, data: dict) -> "TreeNode":
        ch = data["children"]

        return cls(
            id=data["id"],
            parent_id=data["parent_id"],
            real_id=data["real_id"],
            name=data["name"],
            leaf=data["leaf"],
            status=data["status"],
            lat=data.get("lat", 0.0),
            lon=data.get("lon", 0.0),
            children=[cls.from_dict(c) for c in ch] if ch else None,
        )

    @classmethod
    def build_tree(cls, data: dict) -> list["TreeNode"]:
        return [cls.from_dict(n) for n in data["children"]]

    @classmethod
    def build_tree_with_index(cls, data: dict):
        index: dict[int, TreeNode] = {}

        def build(node: dict) -> TreeNode:
            ch = node["children"]

            obj = cls(
                id=node["id"],
                parent_id=node["parent_id"],
                real_id=node["real_id"],
                name=node["name"],
                leaf=node["leaf"],
                status=node["status"],
                lat=node.get("lat", 0.0),
                lon=node.get("lon", 0.0),
                children=None,
            )

            index[obj.real_id] = obj

            if ch:
                obj.children = [build(c) for c in ch]

            return obj

        roots = [build(n) for n in data["children"]]
        return roots, index
