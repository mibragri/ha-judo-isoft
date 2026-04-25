"""Button entities (stateless actions)."""
from __future__ import annotations

import logging

from homeassistant.components.button import ButtonEntity
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
            JudoRegenerationButton(coordinator, entry.entry_id),
            JudoLeakageCloseButton(coordinator, entry.entry_id),
            JudoLeakageOpenButton(coordinator, entry.entry_id),
        ]
    )


class _JudoButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: JudoCoordinator, entry_id: str, key: str) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_device_info = coordinator.device_info


class JudoRegenerationButton(_JudoButton):
    _attr_translation_key = "regeneration"
    _attr_icon = "mdi:autorenew"

    def __init__(self, coordinator: JudoCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "regeneration")

    async def async_press(self) -> None:
        try:
            await self._coordinator.api.start_regeneration()
        except JudoApiError as err:
            _LOGGER.error("start regeneration failed: %s", err)
            return
        await self._coordinator.async_request_refresh()


class JudoLeakageCloseButton(_JudoButton):
    """Activate leakage protection (close the main water valve)."""

    _attr_translation_key = "leakage_close"
    _attr_icon = "mdi:water-off"

    def __init__(self, coordinator: JudoCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "leakage_close")

    async def async_press(self) -> None:
        try:
            await self._coordinator.api.close_leakage_valve()
        except JudoApiError as err:
            _LOGGER.error("close leakage valve failed: %s", err)


class JudoLeakageOpenButton(_JudoButton):
    """Deactivate leakage protection (open the main water valve)."""

    _attr_translation_key = "leakage_open"
    _attr_icon = "mdi:water-check"

    def __init__(self, coordinator: JudoCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id, "leakage_open")

    async def async_press(self) -> None:
        try:
            await self._coordinator.api.open_leakage_valve()
        except JudoApiError as err:
            _LOGGER.error("open leakage valve failed: %s", err)
