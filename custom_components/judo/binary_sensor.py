"""Binary-Sensoren für Judo (z.B. Verbindungs-Status)."""
from __future__ import annotations

from datetime import timedelta

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.util import dt as dt_util

from .const import DOMAIN
from .coordinator import JudoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: JudoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([JudoConnectivity(coordinator, entry.entry_id)])


class JudoConnectivity(CoordinatorEntity[JudoCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "connectivity"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator: JudoCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_connectivity"
        self._attr_device_info = coordinator.device_info

    @property
    def is_on(self) -> bool:
        # Connectivity = letzte erfolgreiche Aktualisierung < 2× Update-Intervall
        if not self.coordinator.last_update_success:
            return False
        last = self.coordinator.data.last_full_refresh if self.coordinator.data else None
        if last is None:
            return False
        return dt_util.now() - last.astimezone(dt_util.now().tzinfo) < (
            self.coordinator.update_interval * 2 if self.coordinator.update_interval else timedelta(minutes=15)
        )
