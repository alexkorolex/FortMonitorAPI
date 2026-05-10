from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FortMonitorConfig:
    """Runtime settings for FortMonitor API calls."""

    base_url: str = "https://fort.psmgroup.ru/api/integration/v1/"
    lang: str = "ru-ru"
    timezone: int = 0
    timeout: float = 30.0

    def __post_init__(self) -> None:
        if self.timeout <= 0:
            raise ValueError("timeout must be greater than zero")

        normalized_url = self.base_url.rstrip("/") + "/"
        object.__setattr__(self, "base_url", normalized_url)
