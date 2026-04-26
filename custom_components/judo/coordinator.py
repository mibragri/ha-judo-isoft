"""DataUpdateCoordinator for the JUDO integration."""
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
from .cloud import JudoCloud, JudoCloudAuthError, JudoCloudError
from .const import DEFAULT_SCAN_INTERVAL, DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass(slots=True)
class JudoData:
    """Container for one coordinator update cycle."""

    device_type_code: int | None = None
    device_type_name: str | None = None
    device_number: str | None = None
    software_version: str | None = None
    installation_date: datetime | None = None
    target_hardness: int | None = None
    salt_storage_mass_kg: float | None = None
    salt_range_days: int | None = None
    salt_warning_days: int | None = None
    service_contact: str | None = None
    total_water_m3: float | None = None
    soft_water_m3: float | None = None
    operating_minutes: int | None = None
    operating_hours: int | None = None
    operating_days: int | None = None
    operating_text: str | None = None
    daily_total_l: int | None = None
    daily_slots_l: list[int] | None = None  # 8 values, 3 hours each
    last_full_refresh: datetime | None = None

    # Cloud-derived (only populated when myjudo.eu credentials are configured).
    cloud_available: bool = False
    live_flow_l_per_h: int | None = None
    input_hardness_dh: int | None = None
    regeneration_count: int | None = None
    regeneration_active: bool | None = None
    battery_backup_percent: int | None = None
    days_until_maintenance: int | None = None
    status_text: str | None = None
    # Raw debug values exposed as attributes on the status sensor.
    cloud_status_attrs: dict[str, Any] | None = None


class JudoCoordinator(DataUpdateCoordinator[JudoData]):
    """Centrally fetches all values with controlled throttling."""

    api: JudoApi

    def __init__(
        self,
        hass: HomeAssistant,
        api: JudoApi,
        *,
        cloud: JudoCloud | None = None,
        scan_interval: int = DEFAULT_SCAN_INTERVAL,
    ) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=scan_interval),
        )
        self.api = api
        self.cloud = cloud
        self._static_loaded = False
        self._static = JudoData()

    async def _load_static(self) -> None:
        """Load static device info once on first refresh."""
        try:
            code, name = await self.api.get_device_type()
            self._static.device_type_code = code
            self._static.device_type_name = name
        except JudoApiError as err:
            _LOGGER.warning("device type unavailable: %s", err)
        try:
            self._static.device_number = await self.api.get_device_number()
        except JudoApiError as err:
            _LOGGER.warning("device number unavailable: %s", err)
        try:
            self._static.software_version = await self.api.get_software_version()
        except JudoApiError as err:
            _LOGGER.warning("software version unavailable: %s", err)
        try:
            self._static.installation_date = await self.api.get_installation_date()
        except JudoApiError as err:
            _LOGGER.debug("installation date unavailable: %s", err)
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
            salt = await self.api.get_salt()
            data.salt_storage_mass_kg = salt["storage_mass_g"] / 1000
            data.salt_range_days = salt["range_days"]
            try:
                data.salt_warning_days = await self.api.get_salt_warning_days()
            except JudoApiError:
                data.salt_warning_days = None
            try:
                data.service_contact = await self.api.get_service_contact()
            except JudoApiError:
                data.service_contact = None
            data.total_water_m3 = await self.api.get_total_water()
            data.soft_water_m3 = await self.api.get_soft_water()
            op = await self.api.get_operating_time()
            data.operating_minutes = op["minutes"]
            data.operating_hours = op["hours"]
            data.operating_days = op["days"]
            data.operating_text = (
                f"{op['days']}d {op['hours']}h {op['minutes']}min"
            )
            stats = await self.api.get_daily_stats()
            data.daily_total_l = stats.get("total")
            data.daily_slots_l = stats.get("slots")
        except JudoApiAuthError as err:
            raise UpdateFailed(f"auth error: {err}") from err
        except JudoApiError as err:
            raise UpdateFailed(str(err)) from err

        if self.cloud is not None:
            try:
                cloud_state = await self.cloud.get_state()
            except JudoCloudAuthError as err:
                _LOGGER.warning("cloud auth failed: %s", err)
            except JudoCloudError as err:
                _LOGGER.debug("cloud unavailable: %s", err)
            else:
                data.cloud_available = True
                data.live_flow_l_per_h = cloud_state.get("live_flow_l_per_h")
                data.input_hardness_dh = cloud_state.get("input_hardness_dh")
                data.regeneration_count = cloud_state.get("regeneration_count")
                data.regeneration_active = cloud_state.get("regeneration_active")
                data.battery_backup_percent = cloud_state.get(
                    "battery_backup_percent"
                )
                data.days_until_maintenance = cloud_state.get(
                    "days_until_maintenance"
                )
                data.status_text = cloud_state.get("status_text")
                data.cloud_status_attrs = {
                    k: cloud_state.get(k)
                    for k in (
                        "holiday_mode_raw",
                        "water_lock_raw",
                        "water_lock_active",
                        "regeneration_active",
                        "index_792_hex",
                    )
                    if cloud_state.get(k) is not None
                }

        data.last_full_refresh = datetime.now()
        return data

    @property
    def device_info(self) -> dict[str, Any]:
        """Device identification used by all entities."""
        ident = self._static.device_number or "judo"
        return {
            "identifiers": {(DOMAIN, ident)},
            "manufacturer": "JUDO Wasseraufbereitung",
            "model": self._static.device_type_name or "Connectivity module",
            "name": f"JUDO {self._static.device_type_name or 'i-soft'}",
            "sw_version": self._static.software_version,
        }
