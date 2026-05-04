# Fort Monitor API

Async Python client for the FortMonitor integration API.

`fort-monitor-api` handles FortMonitor session lifecycle, `SessionId` headers,
cookies, request timeouts, typed response schemas and library-specific
exceptions. The import package is `fort_monitor`.

Swagger documentation for the target FortMonitor server:
<https://fort.psmgroup.ru/swagger/index.html>

FortMonitor API method availability can differ between servers and versions.
Use the Swagger page of the exact server you integrate with.

## Installation

```bash
python -m pip install fort-monitor-api
```

Local wheel installation:

```bash
python -m pip install dist/fort_monitor_api-0.1.0-py3-none-any.whl
```

Development setup:

```bash
uv sync
uv run python -m unittest discover -s tests
```

## Packaging Model

This project uses the modern Python packaging standard: `pyproject.toml` with
the `hatchling` build backend.

There is no `setup.py` or `setup.cfg` because they are not required for modern
PyPI publishing. Package metadata, dependencies, build configuration and the
PyPI long description are configured in `pyproject.toml`.

## Requirements

- Python 3.10+
- aiohttp 3.9+
- FortMonitor API user with access to integration methods

## Quick Start

```python
import asyncio
from datetime import datetime, timezone

from fort_monitor import FortMonitor


async def main() -> None:
    async with FortMonitor("api-login", "api-password") as client:
        objects = await client.objects.get_objects_list()
        first_object = objects[0]

        info = await client.objects.object_info(first_object.id)
        track = await client.objects.track(
            oid=first_object.id,
            start_time=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc),
            finish_time=datetime(2026, 5, 1, 23, 59, tzinfo=timezone.utc),
        )

        print(info.Name)
        print(len(track.coords))


asyncio.run(main())
```

## Configuration

By default the client uses:

```text
https://fort.psmgroup.ru/api/integration/v1/
```

Configure another server, language, timezone or timeout:

```python
from fort_monitor import FortMonitor, FortMonitorConfig

config = FortMonitorConfig(
    base_url="https://your-fortmonitor-host/api/integration/v1/",
    lang="ru",
    timezone=3,
    timeout=20.0,
)

client = FortMonitor("api-login", "api-password", config=config)
```

Short form:

```python
client = FortMonitor(
    "api-login",
    "api-password",
    base_url="https://your-host/api/integration/v1/",
    timeout=15.0,
)
```

## Session Lifecycle

FortMonitor API works with an authenticated session:

1. `connect/` opens the session.
2. Subsequent requests use the returned `SessionId` header and cookies.
3. `disconnect/` closes the session.

The async context manager performs these steps automatically:

```python
async with FortMonitor("login", "password") as client:
    await client.ping()
```

Manual lifecycle is also supported:

```python
client = FortMonitor("login", "password")
await client.start()
try:
    await client.ping()
finally:
    await client.close()
```

## Implemented API

```python
async with FortMonitor("login", "password") as client:
    is_alive = await client.ping()

    roots = await client.objects.get_tree_roots(all=True)
    root = await client.objects.get_tree()
    objects = await client.objects.get_objects_list(company_id=0)

    info = await client.objects.object_info(oid=123)
    full_info = await client.objects.full_object_info(oid=123)
    track = await client.objects.track(
        oid=123,
        start_time=dt_from,
        finish_time=dt_to,
    )
```

## Raw Swagger Requests

For endpoints that are present in Swagger but not yet wrapped by a resource
method, use raw requests. Authentication is still handled by the client.

```python
async with FortMonitor("login", "password") as client:
    payload = await client.request_json(
        "GET",
        "some-endpoint/",
        params={"objectId": 123},
    )
```

For text responses:

```python
text = await client.request_text("GET", "ping")
```

## Schemas

Dataclass schemas live in `fort_monitor.schemas`.

```python
from fort_monitor.schemas import (
    FortMonitorConfig,
    Object,
    ObjectFull,
    ObjectInfo,
    TrackInfo,
    TreeNode,
)
```

The public package root also re-exports the most common entry points:

```python
from fort_monitor import FortMonitor, FortMonitorConfig, FortMonitorError
```

## API Reference

This section is intentionally kept in `README.md` so it is rendered as the
project documentation on PyPI.

### `fort_monitor.FortMonitor`

Main high-level async client. Use this class for normal integrations.

```python
FortMonitor(
    login: str,
    password: str,
    *,
    config: FortMonitorConfig | None = None,
    base_url: str | None = None,
    timeout: float | None = None,
    lang: str | None = None,
    timezone: int | None = None,
    logger: logging.Logger | None = None,
)
```

Constructor parameters:

| Name | Type | Description |
| --- | --- | --- |
| `login` | `str` | FortMonitor API username. |
| `password` | `str` | FortMonitor API password. |
| `config` | `FortMonitorConfig \| None` | Full client configuration. When provided, short options below are ignored. |
| `base_url` | `str \| None` | API base URL, for example `https://host/api/integration/v1/`. |
| `timeout` | `float \| None` | Total HTTP request timeout in seconds. |
| `lang` | `str \| None` | FortMonitor response language passed to `connect/`. |
| `timezone` | `int \| None` | FortMonitor timezone passed to `connect/`. |
| `logger` | `logging.Logger \| None` | Optional logger instance. |

Attributes:

| Name | Type | Description |
| --- | --- | --- |
| `objects` | `FortMonitorObjects` | Resource for monitoring object methods. |
| `config` | `FortMonitorConfig` | Resolved runtime configuration. |
| `login` | `str` | Login passed to the client. |
| `password` | `str` | Password passed to the client. |

Methods:

| Method | Returns | Description |
| --- | --- | --- |
| `async start() -> FortMonitor` | `FortMonitor` | Opens HTTP session and authenticates through `connect/`. |
| `async close() -> None` | `None` | Calls `disconnect/` and closes the HTTP session. |
| `async ping() -> bool` | `bool` | Checks whether the current FortMonitor session is alive. |
| `async request_json(method, path, **kwargs) -> Any` | `Any` | Sends an authenticated request and parses any JSON response. |
| `async request_text(method, path, **kwargs) -> str` | `str` | Sends an authenticated request and returns text. |
| `async with FortMonitor(...)` | `FortMonitor` | Context manager wrapper around `start()` and `close()`. |

`request_json()` and `request_text()` accept the same keyword arguments as the
internal HTTP client: `params`, `json_body` and `data`.

### `fort_monitor.api.FortMonitorObjects`

Resource with FortMonitor monitoring object methods.

| Method | Returns | FortMonitor endpoint | Description |
| --- | --- | --- | --- |
| `async get_tree(all: bool = False)` | `TreeNode` | `GET gettree/` | Returns the first root node from the available object tree. |
| `async get_tree_roots(all: bool = False)` | `list[TreeNode]` | `GET gettree/` | Returns all root nodes from the available object tree. |
| `async get_objects_list(company_id: int = 0)` | `list[Object]` | `GET getobjectslist/` | Returns monitoring objects for a company. `0` means all available objects. |
| `async object_info(oid: int, dt: datetime \| None = None)` | `ObjectInfo` | `GET objectinfo/` | Returns object state and configured sensors. |
| `async full_object_info(oid: int)` | `ObjectFull` | `GET fullobjinfo/` | Returns object state, sensors, location and properties. |
| `async track(oid: int, start_time: datetime, finish_time: datetime)` | `TrackInfo` | `GET track/` | Returns object track points for the time range. |

Datetime values are formatted as `yyyy-MM-dd HH:mm:ss` before sending them to
FortMonitor.

### `fort_monitor.api.FortMonitorConnect`

Low-level session resource. Most users should prefer `FortMonitor`.

| Method | Returns | Description |
| --- | --- | --- |
| `async connect(login: str, password: str, lang: str = "ru", timezone: int = 0)` | `tuple[dict[str, str], dict[str, Any]]` | Opens a FortMonitor session and returns auth headers and cookies. |
| `async ping(session: aiohttp.ClientSession \| None = None)` | `bool` | Checks whether the session is active. |
| `async disconnect(session: aiohttp.ClientSession \| None = None)` | `None` | Closes the FortMonitor session. |

The optional `session` argument exists for backwards compatibility with older
code that created `aiohttp.ClientSession` manually.

### `fort_monitor.api.http.FortMonitorHttpClient`

Low-level HTTP transport. It is primarily an internal extension point for new
resource classes.

| Method | Returns | Description |
| --- | --- | --- |
| `async open()` | `None` | Creates an `aiohttp.ClientSession`. |
| `async authenticate(login, password, *, lang=None, timezone=None)` | `AuthTokens` | Calls `connect/` and stores returned auth headers. |
| `async disconnect()` | `None` | Calls `disconnect/` when a session is opened. |
| `async close()` | `None` | Closes the underlying `aiohttp` session. |
| `async request_json(method, path, *, params=None, json_body=None, data=None)` | `Any` | Sends a request and parses any JSON response. |
| `async request_json_object(method, path, *, params=None, json_body=None, data=None)` | `dict[str, Any]` | Sends a request and requires the response JSON to be an object. |
| `async request_text(method, path, *, params=None, json_body=None, data=None)` | `str` | Sends a request and returns response text. |
| `async request_raw(method, path, *, params=None, json_body=None, data=None)` | `aiohttp.ClientResponse` | Sends a request and returns raw `aiohttp` response. |

### `fort_monitor.schemas.FortMonitorConfig`

Runtime configuration dataclass.

| Field | Type | Default | Description |
| --- | --- | --- | --- |
| `base_url` | `str` | `https://fort.psmgroup.ru/api/integration/v1/` | FortMonitor integration API base URL. |
| `lang` | `str` | `ru` | Language passed to `connect/`. |
| `timezone` | `int` | `0` | Timezone passed to `connect/`. |
| `timeout` | `float` | `30.0` | Total HTTP timeout in seconds. |

`base_url` is normalized with a trailing slash. `timeout` must be greater than
zero.

### `fort_monitor.schemas.AuthTokens`

Authentication data returned by `connect/`.

| Field | Type | Description |
| --- | --- | --- |
| `headers` | `dict[str, str]` | Auth headers, usually containing `SessionId`. |
| `cookies` | `dict[str, str]` | Cookies returned by FortMonitor. |

### Object Schemas

`Object`

| Field | Type |
| --- | --- |
| `id` | `int` |
| `name` | `str` |
| `groupId` | `int` |
| `IMEI` | `str` |
| `icon` | `str` |
| `rotateIcon` | `bool` |
| `iconHeight` | `int` |
| `iconWidth` | `int` |
| `status` | `int` |
| `lat` | `float` |
| `lon` | `float` |
| `direction` | `float` |
| `move` | `float` |
| `lastData` | `str` |

`Sensor`

| Field | Type |
| --- | --- |
| `sid` | `int` |
| `dt` | `str` |
| `ico` | `str` |
| `name` | `str` |
| `val` | `str` |
| `st` | `int` |
| `haveChart` | `bool` |

`ObjectInfo`

| Field | Type |
| --- | --- |
| `oid` | `str` |
| `Name` | `str` |
| `IMEI` | `str` |
| `cid` | `int` |
| `dt` | `str` |
| `properties` | `list[dict[str, Any]]` |
| `sensors` | `list[Sensor]` |
| `result` | `str` |

`ObjectFull` extends `ObjectInfo`.

| Extra field | Type |
| --- | --- |
| `parent_id` | `int` |
| `name` | `str` |
| `address` | `str` |
| `obj_icon` | `str` |
| `obj_icon_height` | `int` |
| `obj_icon_width` | `int` |
| `obj_icon_rotate` | `bool` |
| `status` | `int` |
| `lat` | `float` |
| `lon` | `float` |
| `direction` | `float` |
| `move` | `float` |
| `block_reason` | `int` |

`Coord`

| Field | Type |
| --- | --- |
| `tm` | `str` |
| `lat` | `float` |
| `lon` | `float` |
| `dir` | `float` |
| `dst` | `float` |
| `st` | `float` |
| `speed` | `float` |

`TrackInfo`

| Field | Type |
| --- | --- |
| `oid` | `int` |
| `coords` | `list[Coord]` |
| `result` | `str` |

`TreeNode`

| Field | Type |
| --- | --- |
| `id` | `int` |
| `parent_id` | `int` |
| `real_id` | `int` |
| `name` | `str` |
| `leaf` | `bool` |
| `status` | `int` |
| `lat` | `float` |
| `lon` | `float` |
| `children` | `list[TreeNode]` |

Schema helpers:

| Method | Returns | Description |
| --- | --- | --- |
| `Object.from_dict(data)` | `Object` | Builds `Object` from a FortMonitor response row. |
| `Sensor.from_dict(data)` | `Sensor` | Builds `Sensor` from a FortMonitor response row. |
| `ObjectInfo.from_dict(data)` | `ObjectInfo` | Builds object state with sensors. |
| `ObjectFull.from_dict(data)` | `ObjectFull` | Builds full object state. |
| `Coord.from_dict(data)` | `Coord` | Builds one track coordinate. |
| `TrackInfo.from_dict(data)` | `TrackInfo` | Builds object track data. |
| `TreeNode.from_dict(data)` | `TreeNode` | Builds one tree node recursively. |
| `TreeNode.build_tree(data)` | `list[TreeNode]` | Builds all root nodes from a tree response. |
| `TreeNode.build_tree_with_index(data)` | `tuple[list[TreeNode], dict[int, TreeNode]]` | Builds roots and an index by `real_id`. |

## Errors

All library exceptions inherit from `FortMonitorError`.

| Exception | Description |
| --- | --- |
| `FortMonitorError` | Base exception for all library-level errors. |
| `FortMonitorSessionError` | Request attempted before the HTTP session was opened. |
| `FortMonitorTransportError` | Network or `aiohttp` transport failure. |
| `FortMonitorApiError` | FortMonitor returned an unsuccessful HTTP/API response. Has `status` and `payload`. |
| `FortMonitorAuthenticationError` | Authentication failed, was rejected or expired. |
| `FortMonitorResponseError` | FortMonitor returned an unexpected response shape. |

```python
from fort_monitor import (
    FortMonitor,
    FortMonitorApiError,
    FortMonitorAuthenticationError,
    FortMonitorError,
)

try:
    async with FortMonitor("login", "bad-password") as client:
        await client.ping()
except FortMonitorAuthenticationError:
    print("Invalid credentials, missing API access or expired session")
except FortMonitorApiError as exc:
    print(exc.status, exc.payload)
except FortMonitorError as exc:
    print(f"FortMonitor client error: {exc}")
```

## Logging

The package uses standard Python logging.

```python
import logging

logging.basicConfig(level=logging.INFO)
```

Enable debug logs for HTTP diagnostics:

```python
logging.getLogger("fort_monitor").setLevel(logging.DEBUG)
```

## Adding New Swagger Methods

1. Open Swagger for the target FortMonitor server.
2. Find the path, HTTP method, query/body parameters and response shape.
3. Add dataclass response models to `fort_monitor/schemas`.
4. Add behavior to the relevant resource in `fort_monitor/api`.
5. Use `self._client.request_json_object()`, `request_json()` or `request_text()`.
6. Add unit tests with a local `aiohttp` server.

Example resource method:

```python
from typing import Any


async def new_method(self, oid: int) -> dict[str, Any]:
    self.logger.info("Call FortMonitor method", extra={"oid": oid})
    return await self._client.request_json_object(
        "GET",
        "newmethod/",
        params={"oid": oid},
    )
```

## Development

Run tests:

```bash
uv run python -m unittest discover -s tests
```

Compile-check package modules:

```bash
uv run python -m compileall fort_monitor tests
```

Build PyPI artifacts:

```bash
uv build
```

Check and upload artifacts:

```bash
python -m pip install twine
twine check dist/*
twine upload --repository testpypi dist/*
twine upload dist/*
```

The test suite uses a local `aiohttp` test server and does not call the real
FortMonitor API.
