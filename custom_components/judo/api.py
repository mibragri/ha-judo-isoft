"""HTTP client for the JUDO connectivity module."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Any

import aiohttp
import async_timeout

from .const import (
    MIN_API_GAP,
    REG_DAILY_STATS,
    REG_DEVICE_NUMBER,
    REG_DEVICE_TYPE,
    REG_INSTALLATION_DATE,
    REG_LEAKAGE_PROTECTION_OFF,
    REG_LEAKAGE_PROTECTION_ON,
    REG_OPERATING_HOURS,
    REG_REGENERATION_START,
    REG_SALT_LEVEL,
    REG_SOFT_WATER,
    REG_SW_VERSION,
    REG_TARGET_HARDNESS,
    REG_TOTAL_WATER,
    REG_VACATION_MODE_OFF,
    REG_VACATION_MODE_ON,
    REQUEST_TIMEOUT,
)

_LOGGER = logging.getLogger(__name__)


class JudoApiError(Exception):
    """Raised when the API reports an error."""


class JudoApiAuthError(JudoApiError):
    """Authentication failed (HTTP 401)."""


class JudoApi:
    """Async client for the JUDO connectivity module.

    Firmware V2023+ accepts only HTTP and only honors requests at least
    ~10 seconds apart. This class serializes calls and enforces the gap.
    """

    def __init__(
        self,
        host: str,
        username: str,
        password: str,
        session: aiohttp.ClientSession,
    ) -> None:
        self._base_url = f"http://{host}/api/rest"
        self._auth = aiohttp.BasicAuth(username, password)
        self._session = session
        self._lock = asyncio.Lock()
        self._last_call = 0.0

    async def _request(
        self, method: str, register: str, *, expect_data: bool = True
    ) -> str | None:
        url = f"{self._base_url}/{register}"
        async with self._lock:
            wait = MIN_API_GAP - (time.monotonic() - self._last_call)
            if wait > 0:
                _LOGGER.debug("Throttle: waiting %.1fs before %s", wait, register)
                await asyncio.sleep(wait)
            try:
                async with async_timeout.timeout(REQUEST_TIMEOUT):
                    async with self._session.request(
                        method, url, auth=self._auth, allow_redirects=False
                    ) as resp:
                        if resp.status == 401:
                            raise JudoApiAuthError("HTTP 401 Unauthorized")
                        if resp.status != 200:
                            raise JudoApiError(
                                f"HTTP {resp.status} on {method} {register}"
                            )
                        payload = await resp.json(content_type=None)
                        data = payload.get("data") if isinstance(payload, dict) else None
                        if expect_data and (data is None or data == ""):
                            # Empty response usually means rate-limit hit or
                            # unsupported register on this model.
                            raise JudoApiError(
                                f"empty response for {register} (rate-limit?)"
                            )
                        return data
            except asyncio.TimeoutError as err:
                raise JudoApiError(f"timeout on {method} {register}") from err
            except aiohttp.ClientError as err:
                raise JudoApiError(f"connection error: {err}") from err
            finally:
                self._last_call = time.monotonic()

    @staticmethod
    def _hex_le_int(hexstr: str) -> int:
        """Parse a hex string as a little-endian unsigned integer."""
        return int.from_bytes(bytes.fromhex(hexstr), "little")

    # --- read methods ---

    async def get_device_type(self) -> tuple[int, str]:
        from .const import DEVICE_TYPES

        data = await self._request("GET", REG_DEVICE_TYPE)
        code = int(data, 16)
        return code, DEVICE_TYPES.get(code, f"Unknown (0x{code:02X})")

    async def get_device_number(self) -> str:
        data = await self._request("GET", REG_DEVICE_NUMBER)
        # Device number stored as 4 LE bytes, displayed as decimal
        return str(self._hex_le_int(data))

    async def get_software_version(self) -> str:
        data = await self._request("GET", REG_SW_VERSION)
        # Format: "MMmmpp" -> "MM.mm.pp"
        if len(data) >= 6:
            return f"{int(data[0:2], 16)}.{int(data[2:4], 16)}.{int(data[4:6], 16)}"
        return data

    async def get_installation_date(self) -> datetime | None:
        data = await self._request("GET", REG_INSTALLATION_DATE, expect_data=False)
        if not data:
            return None
        # Some models (e.g. i-soft K) return junk values here. Reject anything
        # outside the plausible range [2000-01-01, now+1d].
        ts = self._hex_le_int(data)
        upper = time.time() + 86400
        if not 946684800 <= ts <= upper:
            _LOGGER.debug(
                "implausible installation date %s, ignored (raw=%s)", ts, data
            )
            return None
        return datetime.fromtimestamp(ts)

    async def get_target_hardness(self) -> int:
        data = await self._request("GET", REG_TARGET_HARDNESS)
        # 1 byte, °dH
        return int(data[:2], 16)

    async def get_salt(self) -> dict[str, int]:
        data = await self._request("GET", REG_SALT_LEVEL)
        # Register 5600 returns 4 bytes:
        #   bytes 0-1 (BE)     = salt weight in grams
        #   bytes 2-3 (LE)     = remaining range in days
        return {
            "weight_g": int(data[:4], 16),
            "range_days": int.from_bytes(bytes.fromhex(data[4:8]), "little"),
        }

    async def get_total_water(self) -> float:
        data = await self._request("GET", REG_TOTAL_WATER)
        # 4 LE bytes in mL -> m³
        return self._hex_le_int(data) / 1_000_000

    async def get_soft_water(self) -> float:
        data = await self._request("GET", REG_SOFT_WATER)
        return self._hex_le_int(data) / 1_000_000

    async def get_operating_time(self) -> dict[str, int]:
        data = await self._request("GET", REG_OPERATING_HOURS)
        # Layout: byte0=minutes, byte1=hours, bytes[2:4]=days little-endian
        if len(data) < 8:
            raise JudoApiError(f"unexpected operating-time format: {data}")
        return {
            "minutes": int(data[0:2], 16),
            "hours": int(data[2:4], 16),
            "days": int.from_bytes(bytes.fromhex(data[4:8]), "little"),
        }

    async def get_daily_stats(self, day: datetime | None = None) -> dict[str, Any]:
        """Return liters per 3-hour slot for the given day (default: today).

        Layout returned by the firmware: 8 × uint32 big-endian, one value per
        3-hour slot (00-03, 03-06, … 21-24). The endpoint encodes the year
        big-endian (DDMMYYYY).
        """
        d = day or datetime.now()
        # Endpoint: FB00 + DD + MM + YYYY (year big-endian)
        endpoint = f"{REG_DAILY_STATS}{d.day:02X}{d.month:02X}{d.year:04X}"
        data = await self._request("GET", endpoint, expect_data=False)
        if not data:
            return {"slots": [], "total": 0}
        slots: list[int] = []
        total = 0
        for i in range(0, len(data), 8):
            chunk = data[i : i + 8]
            if len(chunk) < 8:
                break
            v = int.from_bytes(bytes.fromhex(chunk), "big")
            slots.append(v)
            total += v
        return {"slots": slots, "total": total}

    # --- write methods ---

    async def start_regeneration(self) -> None:
        await self._request("POST", REG_REGENERATION_START, expect_data=False)

    async def set_leakage_protection(self, enabled: bool) -> None:
        register = REG_LEAKAGE_PROTECTION_ON if enabled else REG_LEAKAGE_PROTECTION_OFF
        await self._request("POST", register, expect_data=False)

    async def set_vacation_mode(self, enabled: bool) -> None:
        register = REG_VACATION_MODE_ON if enabled else REG_VACATION_MODE_OFF
        await self._request("POST", register, expect_data=False)

    async def set_target_hardness(self, dh: int) -> None:
        if not 1 <= dh <= 25:
            raise ValueError("target hardness must be between 1 and 25 °dH")
        register = f"3000{dh:02X}00"
        await self._request("POST", register, expect_data=False)
