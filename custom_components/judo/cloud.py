"""Cloud client for myjudo.eu.

The local connectivity-module API exposes most of the device state, but a
handful of values (live flow rate, regeneration counter, battery backup
status, maintenance interval) are only surfaced through the JUDO cloud
endpoint at https://www.myjudo.eu. Cloud access is optional and disabled
unless the user supplies their myjudo.eu account credentials.

Wire protocol reverse-engineered from
github.com/danielegger1/Judo-i-soft-save-plus-appdaemon (appdaemon script
for i-soft SAFE+).
"""
from __future__ import annotations

import asyncio
import hashlib
import logging
from typing import Any

import aiohttp
import async_timeout

from .const import CLOUD_BASE_URL, REQUEST_TIMEOUT

_LOGGER = logging.getLogger(__name__)


class JudoCloudError(Exception):
    """Generic cloud-side failure."""


class JudoCloudAuthError(JudoCloudError):
    """myjudo.eu rejected the credentials."""


class JudoCloud:
    """Async client for the myjudo.eu cloud relay.

    Tokens are obtained on first use and refreshed transparently when the
    backend returns ``status=error / data=login failed``.
    """

    def __init__(
        self,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._user = username
        # The cloud API expects the MD5 hex digest, not the plaintext.
        self._pw_md5 = hashlib.md5(password.encode("utf-8")).hexdigest()
        self._session = session
        self._token: str | None = None
        self._lock = asyncio.Lock()

    async def _login(self) -> str:
        url = (
            f"{CLOUD_BASE_URL}/interface/"
            f"?group=register&command=login&name=login"
            f"&user={self._user}&password={self._pw_md5}"
            "&nohash=Service&role=customer"
        )
        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self._session.get(url) as resp:
                    if resp.status != 200:
                        raise JudoCloudError(f"login HTTP {resp.status}")
                    payload = await resp.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise JudoCloudError("login timed out") from err
        except aiohttp.ClientError as err:
            raise JudoCloudError(f"login connection error: {err}") from err

        if not isinstance(payload, dict) or "token" not in payload:
            # The server returns status=error / data="login failed" on bad creds.
            raise JudoCloudAuthError("login rejected by myjudo.eu")
        token = str(payload["token"])
        _LOGGER.debug("cloud login successful")
        self._token = token
        return token

    async def _ensure_token(self) -> str:
        if self._token is None:
            return await self._login()
        return self._token

    async def _request_device_data(self, token: str) -> dict[str, Any]:
        url = (
            f"{CLOUD_BASE_URL}/interface/"
            f"?token={token}&group=register&command=get%20device%20data"
        )
        try:
            async with async_timeout.timeout(REQUEST_TIMEOUT):
                async with self._session.get(url) as resp:
                    if resp.status != 200:
                        raise JudoCloudError(f"HTTP {resp.status}")
                    return await resp.json(content_type=None)
        except asyncio.TimeoutError as err:
            raise JudoCloudError("device-data request timed out") from err
        except aiohttp.ClientError as err:
            raise JudoCloudError(f"connection error: {err}") from err

    async def get_state(self) -> dict[str, Any]:
        """Fetch the cloud device-data payload and return the parsed values.

        On stale/expired tokens this transparently re-logs in once.
        """
        async with self._lock:
            token = await self._ensure_token()
            payload = await self._request_device_data(token)

            if (
                isinstance(payload, dict)
                and payload.get("status") == "error"
                and payload.get("data") == "login failed"
            ):
                _LOGGER.debug("cloud token expired, re-logging in")
                self._token = None
                token = await self._login()
                payload = await self._request_device_data(token)

            if not isinstance(payload, dict) or payload.get("status") != "ok":
                raise JudoCloudError(
                    f"unexpected cloud response: {payload!r:.200}"
                )

            return _parse_state(payload)


# --- parser -----------------------------------------------------------------

def _le_int(hexstr: str, start: int, end: int) -> int | None:
    """Parse a little-endian unsigned integer from a hex sub-string."""
    chunk = hexstr[start:end]
    if not chunk:
        return None
    try:
        return int.from_bytes(bytes.fromhex(chunk), "little")
    except ValueError:
        return None


def _index_data(payload: dict[str, Any], index: int) -> str | None:
    """Walk the deeply nested cloud payload to extract one register's hex."""
    try:
        data = payload["data"][0]["data"][0]["data"][str(index)]["data"]
    except (KeyError, IndexError, TypeError):
        return None
    if data == "":
        return None
    return data


def _parse_state(payload: dict[str, Any]) -> dict[str, Any]:
    """Map the cloud payload onto a flat dict of values used by entities.

    Index map verified against danielegger1's appdaemon code (i-soft SAFE+):
        7  : days_until_maintenance (uint16 LE, value is hours -> /24)
        93 : [6:8] battery_backup_percent (uint8)
        790: [34:38] live_flow_l_per_h (uint16 LE)
             [54:56] input_hardness_dh (uint8)
        791: [2:4]   regeneration_active (uint8)
             [62:66] regeneration_count (uint16 LE)
        792: [2:4]   water_lock (uint8)
             [38:40] holiday_mode (uint8)
    """
    result: dict[str, Any] = {}

    # Maintenance interval
    h = _index_data(payload, 7)
    if h is not None:
        hours = _le_int(h, 0, 4)
        if hours is not None:
            result["days_until_maintenance"] = int(hours / 24)

    # Battery backup
    h = _index_data(payload, 93)
    if h is not None and len(h) >= 8:
        result["battery_backup_percent"] = _le_int(h, 6, 8)

    # Live readings
    h = _index_data(payload, 790)
    if h is not None and len(h) >= 56:
        result["live_flow_l_per_h"] = _le_int(h, 34, 38)
        ih = _le_int(h, 54, 56)
        if ih is not None:
            result["input_hardness_dh"] = ih

    # Regeneration
    h = _index_data(payload, 791)
    if h is not None and len(h) >= 66:
        result["regeneration_count"] = _le_int(h, 62, 66)
        active = _le_int(h, 2, 4)
        if active is not None:
            result["regeneration_active"] = bool(active & 0x0F)

    # Operating mode
    h = _index_data(payload, 792)
    if h is not None and len(h) >= 40:
        result["index_792_hex"] = h
        wl = _le_int(h, 2, 4)
        if wl is not None:
            result["water_lock_raw"] = wl
            result["water_lock_active"] = wl > 0
        hm = _le_int(h, 38, 40)
        if hm is not None:
            result["holiday_mode_raw"] = hm

    # Top-level status text derived from the above (best-effort).
    # The byte at register 792 [38:40] encodes the active operating-mode on
    # i-soft K SAFE+: 0=off, 3=leakage protection / limited usage (mode 1),
    # 5=mode 2, 9=valve fully locked. On older i-soft SAFE+ models the same
    # byte was labelled "vacation mode" — empirically on i-soft K SAFE+ it
    # also reflects leakage protection, so we use a generic label.
    mode_raw = result.get("holiday_mode_raw")
    if result.get("regeneration_active"):
        result["status_text"] = "regenerating"
    elif mode_raw == 9 or result.get("water_lock_active"):
        result["status_text"] = "valve locked"
    elif mode_raw in (3, 5):
        result["status_text"] = "leakage protection"
    else:
        result["status_text"] = "normal"

    return result
