"""Switch entities (stateful actions)."""
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
    async_add_entities([JudoVacationModeSwitch(coordinator, entry.entry_id)])


class JudoVacationModeSwitch(SwitchEntity):
    """Vacation mode toggle.

    The connectivity module exposes only write registers for vacation mode
    (no read state), so we cache the last requested state locally. When HA
    restarts the displayed state defaults to off until the user toggles it.
    """

    _attr_has_entity_name = True
    _attr_translation_key = "vacation_mode"
    _attr_icon = "mdi:beach"

    def __init__(self, coordinator: JudoCoordinator, entry_id: str) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry_id}_vacation_mode"
        self._attr_device_info = coordinator.device_info
        self._is_on = False

    @property
    def is_on(self) -> bool:
        return self._is_on

    async def async_turn_on(self, **kwargs) -> None:
        try:
            await self._coordinator.api.set_vacation_mode(True)
        except JudoApiError as err:
            _LOGGER.error("enabling vacation mode failed: %s", err)
            return
        self._is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs) -> None:
        try:
            await self._coordinator.api.set_vacation_mode(False)
        except JudoApiError as err:
            _LOGGER.error("disabling vacation mode failed: %s", err)
            return
        self._is_on = False
        self.async_write_ha_state()
