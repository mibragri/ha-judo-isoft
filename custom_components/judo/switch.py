"""Switches (zustandsbehaftete Aktionen)."""
from __future__ import annotations

import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .api import JudoApiError
from .const import DOMAIN
from .coordinator import JudoCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: JudoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            JudoLeakageProtectionSwitch(coordinator, entry.entry_id),
            JudoVacationModeSwitch(coordinator, entry.entry_id),
        ]
    )


class _JudoSwitchBase(SwitchEntity):
    """Basis: HA hat keinen Read-Zustand für diese Schalter, daher
    halten wir den letzten gewünschten Zustand selbst."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: JudoCoordinator, entry_id: str, key: str) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = coordinator.device_info
        self._is_on = False

    @property
    def is_on(self) -> bool:
        return self._is_on


class JudoLeakageProtectionSwitch(_JudoSwitchBase):
    _attr_translation_key = "leakage_protection"
    _attr_icon = "mdi:water-alert"

    def __init__(self, coordinator: JudoCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "leakage_protection")

    async def async_turn_on(self, **kwargs) -> None:
        try:
            await self._coordinator.api.set_leakage_protection(True)
        except JudoApiError as err:
            _LOGGER.error("Leckageschutz aktivieren: %s", err)
            return
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self._coordinator.api.set_leakage_protection(False)
        except JudoApiError as err:
            _LOGGER.error("Leckageschutz deaktivieren: %s", err)
            return
        self._is_on = False
        self.async_write_ha_state()


class JudoVacationModeSwitch(_JudoSwitchBase):
    _attr_translation_key = "vacation_mode"
    _attr_icon = "mdi:beach"

    def __init__(self, coordinator: JudoCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "vacation_mode")

    async def async_turn_on(self, **kwargs) -> None:
        try:
            await self._coordinator.api.set_vacation_mode(True)
        except JudoApiError as err:
            _LOGGER.error("Urlaubsmodus aktivieren: %s", err)
            return
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self._coordinator.api.set_vacation_mode(False)
        except JudoApiError as err:
            _LOGGER.error("Urlaubsmodus deaktivieren: %s", err)
            return
        self._is_on = False
        self.async_write_ha_state()
