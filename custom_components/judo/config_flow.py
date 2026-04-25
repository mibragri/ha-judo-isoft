"""Config Flow für Judo."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JudoApi, JudoApiAuthError, JudoApiError
from .const import DEFAULT_PASSWORD, DEFAULT_USERNAME, DOMAIN

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_USERNAME, default=DEFAULT_USERNAME): str,
        vol.Optional(CONF_PASSWORD, default=DEFAULT_PASSWORD): str,
    }
)


class JudoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = JudoApi(
                host=user_input[CONF_HOST],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                session=session,
            )
            try:
                _, name = await api.get_device_type()
                device_number = await api.get_device_number()
            except JudoApiAuthError:
                errors["base"] = "invalid_auth"
            except JudoApiError:
                errors["base"] = "cannot_connect"
            else:
                await self.async_set_unique_id(f"judo-{device_number}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Judo {name} ({device_number})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            session = async_get_clientsession(self.hass)
            api = JudoApi(
                host=user_input[CONF_HOST],
                username=user_input[CONF_USERNAME],
                password=user_input[CONF_PASSWORD],
                session=session,
            )
            try:
                await api.get_device_type()
            except JudoApiAuthError:
                errors["base"] = "invalid_auth"
            except JudoApiError:
                errors["base"] = "cannot_connect"
            else:
                return self.async_update_reload_and_abort(
                    entry,
                    data={**entry.data, **user_input},
                )
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_HOST, default=entry.data.get(CONF_HOST)): str,
                    vol.Optional(
                        CONF_USERNAME, default=entry.data.get(CONF_USERNAME, DEFAULT_USERNAME)
                    ): str,
                    vol.Optional(
                        CONF_PASSWORD, default=entry.data.get(CONF_PASSWORD, DEFAULT_PASSWORD)
                    ): str,
                }
            ),
            errors=errors,
        )
