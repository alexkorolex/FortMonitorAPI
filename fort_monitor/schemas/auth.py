from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class AuthTokens:
    headers: dict[str, str]
    cookies: dict[str, str]
