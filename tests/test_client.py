from __future__ import annotations

import unittest
import logging
from datetime import datetime, timezone
from typing import Any

from aiohttp import web

from fort_monitor import (
    FortMonitor,
    FortMonitorAuthenticationError,
    FortMonitorConfig,
)


class FortMonitorConfigTest(unittest.TestCase):
    def test_normalizes_base_url(self) -> None:
        config = FortMonitorConfig(base_url="https://example.test/api")

        self.assertEqual(config.base_url, "https://example.test/api/")

    def test_rejects_invalid_timeout(self) -> None:
        with self.assertRaises(ValueError):
            FortMonitorConfig(timeout=0)


class FortMonitorClientTest(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        self.requests: list[dict[str, Any]] = []
        self.app = self._build_app()
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, "127.0.0.1", 0)
        await self.site.start()
        self.config = FortMonitorConfig(base_url=self._base_url())
        self.logger = logging.getLogger(f"tests.fort_monitor.{id(self)}")
        self.logger.addHandler(logging.NullHandler())
        self.logger.propagate = False

    async def asyncTearDown(self) -> None:
        await self.runner.cleanup()

    async def test_context_manager_authenticates_and_disconnects(self) -> None:
        async with FortMonitor("login", "password", config=self.config) as client:
            self.assertTrue(await client.ping())
            objects = await client.objects.get_objects_list(company_id=42)
            track = await client.objects.track(
                oid=objects[0].id,
                start_time=datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc),
                finish_time=datetime(2026, 5, 1, 1, 30, tzinfo=timezone.utc),
            )

        self.assertEqual(objects[0].name, "Truck 1")
        self.assertEqual(track.coords[0].speed, 50.0)
        self.assertIn("disconnect", self._request_names())

    async def test_authentication_error_for_failed_connect(self) -> None:
        with self.assertRaises(FortMonitorAuthenticationError):
            async with FortMonitor(
                "bad",
                "password",
                config=self.config,
                logger=self.logger,
            ):
                pass

    async def _connect(self, request: web.Request) -> web.Response:
        payload = await request.json()
        self.requests.append({"name": "connect", "payload": payload})
        if payload["login"] == "bad":
            return web.Response(text="Invalid login")

        response = web.Response(text="Ok", headers={"SessionId": "session-1"})
        response.set_cookie("sid", "cookie-1")
        return response

    async def _ping(self, request: web.Request) -> web.Response:
        self._record_authorized_request("ping", request)
        return web.Response(text="Ok")

    async def _disconnect(self, request: web.Request) -> web.Response:
        self._record_authorized_request("disconnect", request)
        return web.Response(text="Ok")

    async def _objects_list(self, request: web.Request) -> web.Response:
        self._record_authorized_request("objects", request)
        self.assertEqual(request.query["companyId"], "42")
        return web.json_response({"result": "Ok", "objects": [self._object_payload()]})

    async def _track(self, request: web.Request) -> web.Response:
        self._record_authorized_request("track", request)
        self.assertEqual(request.query["from"], "2026-05-01 00:00:00")
        self.assertEqual(request.query["to"], "2026-05-01 01:30:00")
        return web.json_response(self._track_payload())

    def _build_app(self) -> web.Application:
        app = web.Application()
        app.router.add_post("/api/integration/v1/connect/", self._connect)
        app.router.add_get("/api/integration/v1/ping", self._ping)
        app.router.add_get("/api/integration/v1/disconnect/", self._disconnect)
        app.router.add_get("/api/integration/v1/getobjectslist/", self._objects_list)
        app.router.add_get("/api/integration/v1/track/", self._track)
        return app

    def _base_url(self) -> str:
        sockets = self.site._server.sockets
        port = sockets[0].getsockname()[1]
        return f"http://127.0.0.1:{port}/api/integration/v1/"

    def _record_authorized_request(self, name: str, request: web.Request) -> None:
        self.requests.append(
            {
                "name": name,
                "session_id": request.headers.get("SessionId"),
                "sid": request.cookies.get("sid"),
            }
        )

    def _request_names(self) -> list[str]:
        return [request["name"] for request in self.requests]

    def _object_payload(self) -> dict[str, Any]:
        return {
            "id": 100,
            "name": "Truck 1",
            "groupId": 10,
            "IMEI": "1234567890",
            "icon": "truck",
            "rotateIcon": True,
            "iconHeight": 32,
            "iconWidth": 32,
            "status": 1,
            "lat": 55.75,
            "lon": 37.61,
            "direction": 180,
            "move": 1,
            "lastData": "2026-05-01 01:00:00",
        }

    def _track_payload(self) -> dict[str, Any]:
        return {
            "oid": 100,
            "result": "Ok",
            "coords": [
                {
                    "tm": "2026-05-01 00:05:00",
                    "lat": 55.75,
                    "lon": 37.61,
                    "dir": 180,
                    "dst": 1000,
                    "st": 1,
                    "speed": 50,
                }
            ],
        }
