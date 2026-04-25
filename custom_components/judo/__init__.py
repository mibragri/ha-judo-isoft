"""JUDO Water Treatment integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryAuthFailed, ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JudoApi, JudoApiAuthError, JudoApiError
from .cloud import JudoCloud
from .const import CONF_CLOUD_PASSWORD, CONF_CLOUD_USER, DOMAIN
from .coordinator import JudoCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.BUTTON,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up JUDO integration from a config entry.

    The connectivity module's firmware rate-limits API requests to ~11s
    apart, so a full first refresh takes 2-3 minutes. To avoid blocking HA's
    setup window we kick the first refresh off in the background — entities
    appear immediately as 'unknown' and populate as the throttled refresh
    progresses.
    """
    session = async_get_clientsession(hass)
    api = JudoApi(
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        session=session,
    )
    cloud: JudoCloud | None = None
    if entry.data.get(CONF_CLOUD_USER) and entry.data.get(CONF_CLOUD_PASSWORD):
        cloud = JudoCloud(
            username=entry.data[CONF_CLOUD_USER],
            password=entry.data[CONF_CLOUD_PASSWORD],
            session=session,
        )
    coordinator = JudoCoordinator(hass, api, cloud=cloud)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    # Trigger first refresh in the background; do not block setup.
    entry.async_create_background_task(
        hass, coordinator.async_refresh(), name="judo first refresh"
    )
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unloaded:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unloaded


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
