"""DataUpdateCoordinator für die Judo-Integration."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import (
    DataUpdateCoordinator,
    UpdateFailed,
)

from .api import JudoApi, JudoApiAuthError, JudoApiError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class JudoData:
    """Strukturierte Daten, die der Coordinator pro Update liefert."""

    device_type_code: int | None = None
    device_type_name: str | None = None
    device_number: str | None = None
    software_version: str | None = None
    installation_date: datetime | None = None
    target_hardness: int | None = None
    salt_level_g: int | None = None
    total_water_m3: float | None = None
    soft_water_m3: float | None = None
    operating_minutes: int | None = None
    operating_hours: int | None = None
    operating_days: int | None = None
    daily_total_l: int | None = None
    daily_hourly_l: list[int] | None = None
    last_full_refresh: datetime | None = None


class JudoCoordinator(DataUpdateCoordinator[JudoData]):
    """Holt alle Werte zentral mit kontrolliertem Throttling."""

    api: JudoApi

    def __init__(
        self,
        hass: HomeAssistant,
        api: JudoApi,
        *,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self._static_loaded = False
        self._static = JudoData()

    async def _load_static(self) -> None:
        """Statische Werte einmalig laden (Geräteinfo)."""
        try:
            code, name = await self.api.get_device_type()
            self._static.device_type_code = code
            self._static.device_type_name = name
        except JudoApiError as err:
            _LOGGER.warning("Gerätetyp konnte nicht gelesen werden: %s", err)
        try:
            self._static.device_number = await self.api.get_device_number()
        except JudoApiError as err:
            _LOGGER.warning("Gerätenummer konnte nicht gelesen werden: %s", err)
        try:
            self._static.software_version = await self.api.get_software_version()
        except JudoApiError as err:
            _LOGGER.warning("SW-Version konnte nicht gelesen werden: %s", err)
        try:
            self._static.installation_date = await self.api.get_installation_date()
        except JudoApiError as err:
            _LOGGER.debug("Inbetriebnahmedatum nicht verfügbar: %s", err)
        self._static_loaded = True

    async def _async_update_data(self) -> JudoData:
        if not self._static_loaded:
            await self._load_static()

        data = JudoData(
            device_type_code=self._static.device_type_code,
            device_type_name=self._static.device_type_name,
            device_number=self._static.device_number,
            software_version=self._static.software_version,
            installation_date=self._static.installation_date,
        )
        try:
            data.target_hardness = await self.api.get_target_hardness()
            data.salt_level_g = await self.api.get_salt_level()
            data.total_water_m3 = await self.api.get_total_water()
            data.soft_water_m3 = await self.api.get_soft_water()
            op = await self.api.get_operating_time()
            data.operating_minutes = op["minutes"]
            data.operating_hours = op["hours"]
            data.operating_days = op["days"]
            stats = await self.api.get_daily_stats()
            data.daily_total_l = stats.get("total")
            data.daily_hourly_l = stats.get("hourly")
        except JudoApiAuthError as err:
            raise UpdateFailed(f"Auth-Fehler: {err}") from err
        except JudoApiError as err:
            raise UpdateFailed(str(err)) from err

        data.last_full_refresh = datetime.now()
        return data

    @property
    def device_info(self) -> dict[str, Any]:
        """HA Geräte-Identifikation für Entity-Registry."""
        ident = self._static.device_number or "judo"
        return {
            "identifiers": {(DOMAIN, ident)},
            "manufacturer": "JUDO Wasseraufbereitung",
            "model": self._static.device_type_name or "Judo Connectivity",
            "name": f"Judo {self._static.device_type_name or 'i-soft'}",
            "sw_version": self._static.software_version,
        }
