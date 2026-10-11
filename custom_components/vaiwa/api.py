"""Minimal VAIWA Firebase Auth + Realtime Database REST client.

No Firebase Admin credential is used. Each user reads only their own sensors
through their Firebase Authentication ID token and existing database rules.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import AUTH_REFRESH_URL, AUTH_SIGNIN_URL, DATABASE_URL

_LOGGER = logging.getLogger(__name__)
_REQUEST_TIMEOUT = ClientTimeout(total=15)


class VaiwaAuthError(Exception):
    """Invalid credentials or an expired/revoked session."""


class VaiwaConnectionError(Exception):
    """Network or API error that can be retried."""


async def async_sign_in(
    session: ClientSession, api_key: str, email: str, password: str
) -> dict[str, Any]:
    """Sign in once. Password is not stored anywhere by the integration."""
    try:
        async with session.post(
            AUTH_SIGNIN_URL,
            params={"key": api_key},
            json={"email": email, "password": password, "returnSecureToken": True},
            timeout=_REQUEST_TIMEOUT,
        ) as response:
            if response.status in (400, 401, 403):
                raise VaiwaAuthError("invalid_credentials")
            if response.status != 200:
                raise VaiwaConnectionError(f"Firebase sign-in HTTP {response.status}")
            data = await response.json()
    except (ClientError, asyncio.TimeoutError) as exc:
        raise VaiwaConnectionError("Cannot contact Firebase Authentication") from exc

    if not isinstance(data, dict) or not data.get("refreshToken") or not data.get("localId"):
        raise VaiwaAuthError("invalid_credentials")
    return data


class VaiwaCloudClient:
    """Firebase Auth client backed by a refresh token, no saved password."""

    def __init__(
        self,
        session: ClientSession,
        api_key: str,
        uid: str,
        refresh_token: str,
        save_refresh_token: Callable[[str], None],
    ) -> None:
        self._session = session
        self._api_key = api_key
        self.uid = uid
        self._refresh_token = refresh_token
        self._save_refresh_token = save_refresh_token
        self._id_token: str | None = None
        self._expires_at = 0.0
        self._token_lock = asyncio.Lock()

    async def _get_token(self, *, force: bool = False) -> str:
        async with self._token_lock:
            if not force and self._id_token and time.monotonic() < self._expires_at:
                return self._id_token
            try:
                async with self._session.post(
                    AUTH_REFRESH_URL,
                    params={"key": self._api_key},
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": self._refresh_token,
                    },
                    timeout=_REQUEST_TIMEOUT,
                ) as response:
                    if response.status in (400, 401, 403):
                        raise VaiwaAuthError("session_expired")
                    if response.status != 200:
                        raise VaiwaConnectionError(f"Firebase token HTTP {response.status}")
                    data = await response.json()
            except (ClientError, asyncio.TimeoutError) as exc:
                raise VaiwaConnectionError("Cannot refresh Firebase Authentication token") from exc

            if not isinstance(data, dict) or not data.get("id_token"):
                raise VaiwaAuthError("session_expired")
            if data.get("user_id") != self.uid:
                raise VaiwaAuthError("user_mismatch")

            self._id_token = data["id_token"]
            try:
                expires_in = int(data.get("expires_in", 3600))
            except (ValueError, TypeError):
                expires_in = 3600
            self._expires_at = time.monotonic() + max(expires_in - 120, 30)

            new_refresh = data.get("refresh_token")
            if new_refresh and new_refresh != self._refresh_token:
                self._refresh_token = new_refresh
                self._save_refresh_token(new_refresh)
            return self._id_token

    async def async_get_sensors(self) -> dict[str, dict[str, Any]]:
        """Read only /users/<authenticated uid>/sensors."""
        url = f"{DATABASE_URL}/users/{self.uid}/sensors.json"

        for attempt in range(2):
            token = await self._get_token(force=attempt == 1)
            try:
                # Firebase Realtime Database REST requires ID token as auth query.
                # Never log URLs, which would expose this token.
                async with self._session.get(
                    url, params={"auth": token}, timeout=_REQUEST_TIMEOUT
                ) as response:
                    if response.status == 401 and attempt == 0:
                        continue
                    if response.status in (401, 403):
                        raise VaiwaAuthError("database_permission_denied")
                    if response.status != 200:
                        raise VaiwaConnectionError(f"Realtime Database HTTP {response.status}")
                    payload = await response.json(content_type=None)
            except (ClientError, asyncio.TimeoutError) as exc:
                raise VaiwaConnectionError("Cannot contact Firebase Realtime Database") from exc

            if payload is None:
                return {}
            if not isinstance(payload, dict):
                raise VaiwaConnectionError("Unexpected Firebase sensor response")

            result: dict[str, dict[str, Any]] = {}
            for sensor_id, sensor in payload.items():
                if not isinstance(sensor_id, str) or not isinstance(sensor, dict):
                    continue
                name = sensor.get("name")
                data = sensor.get("data")
                if isinstance(data, dict):
                    result[sensor_id] = {
                        "name": name if isinstance(name, str) and name.strip() else "VAIWA Sensor",
                        # PM1.0 a PM4.0 nie su podporovane v HA integracii VAIWA.
                        "data": {k: v for k, v in data.items() if k not in ("pm1", "pm4")},
                    }
            return result
        raise VaiwaAuthError("session_expired")
