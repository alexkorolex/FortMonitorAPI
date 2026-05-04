from __future__ import annotations

from typing import Any


class FortMonitorError(Exception):
    """Base exception for all library-level errors."""


class FortMonitorSessionError(FortMonitorError):
    """Raised when an API request is attempted without an opened session."""


class FortMonitorTransportError(FortMonitorError):
    """Raised when aiohttp cannot complete the network operation."""


class FortMonitorApiError(FortMonitorError):
    """Raised when FortMonitor returns an unsuccessful HTTP/API response."""

    def __init__(
        self,
        message: str,
        *,
        status: int | None = None,
        payload: Any | None = None,
    ) -> None:
        super().__init__(message)
        self.status = status
        self.payload = payload


class FortMonitorAuthenticationError(FortMonitorApiError):
    """Raised when FortMonitor rejects or expires authentication."""


class FortMonitorResponseError(FortMonitorApiError):
    """Raised when FortMonitor returns an unexpected response shape."""
