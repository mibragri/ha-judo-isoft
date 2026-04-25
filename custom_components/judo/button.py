"""Button entities (stateless actions)."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import JudoCoordinator


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: JudoCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([JudoRegenerationButton(coordinator, entry.entry_id)])


class JudoRegenerationButton(ButtonEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "regeneration"
    _attr_icon = "mdi:autorenew"

    def __init__(self, coordinator: JudoCoordinator, entry_id: str) -> None:
        self._coordinator = coordinator
        self._attr_unique_id = f"{entry_id}_regeneration"
        self._attr_device_info = coordinator.device_info

    async def async_press(self) -> None:
        await self._coordinator.api.start_regeneration()
        await self._coordinator.async_request_refresh()
