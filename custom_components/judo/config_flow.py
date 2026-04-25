"""Config flow for JUDO."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_USERNAME
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import JudoApi, JudoApiAuthError, JudoApiError
from .cloud import JudoCloud, JudoCloudAuthError, JudoCloudError
from .const import (
    CONF_CLOUD_PASSWORD,
    CONF_CLOUD_USER,
    DEFAULT_PASSWORD,
    DEFAULT_USERNAME,
    DOMAIN,
)


def _user_schema(defaults: dict[str, Any] | None = None) -> vol.Schema:
    d = defaults or {}
    return vol.Schema(
        {
            vol.Required(CONF_HOST, default=d.get(CONF_HOST, vol.UNDEFINED)): str,
            vol.Optional(
                CONF_USERNAME, default=d.get(CONF_USERNAME, DEFAULT_USERNAME)
            ): str,
            vol.Optional(
                CONF_PASSWORD, default=d.get(CONF_PASSWORD, DEFAULT_PASSWORD)
            ): str,
            vol.Optional(
                CONF_CLOUD_USER, default=d.get(CONF_CLOUD_USER, "")
            ): str,
            vol.Optional(
                CONF_CLOUD_PASSWORD, default=d.get(CONF_CLOUD_PASSWORD, "")
            ): str,
        }
    )


async def _validate(
    hass, user_input: dict[str, Any]
) -> tuple[str | None, str | None]:
    """Verify both local and (if configured) cloud credentials.

    Returns ``(error_key, device_number)``. When ``error_key`` is None the
    input is valid. The device number drives the unique-id assignment.
    """
    session = async_get_clientsession(hass)
    api = JudoApi(
        host=user_input[CONF_HOST],
        username=user_input[CONF_USERNAME],
        password=user_input[CONF_PASSWORD],
        session=session,
    )
    try:
        await api.get_device_type()
        device_number = await api.get_device_number()
    except JudoApiAuthError:
        return "invalid_auth", None
    except JudoApiError:
        return "cannot_connect", None

    cloud_user = user_input.get(CONF_CLOUD_USER)
    cloud_pw = user_input.get(CONF_CLOUD_PASSWORD)
    if cloud_user and cloud_pw:
        cloud = JudoCloud(cloud_user, cloud_pw, session)
        try:
            await cloud.get_state()
        except JudoCloudAuthError:
            return "cloud_invalid_auth", None
        except JudoCloudError:
            return "cloud_cannot_connect", None
    return None, device_number


class JudoConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            # Drop empty cloud strings so we don't store "".
            if not user_input.get(CONF_CLOUD_USER):
                user_input.pop(CONF_CLOUD_USER, None)
                user_input.pop(CONF_CLOUD_PASSWORD, None)
            err, device_number = await _validate(self.hass, user_input)
            if err:
                errors["base"] = err
            else:
                await self.async_set_unique_id(f"judo-{device_number}")
                self._abort_if_unique_id_configured()
                api = JudoApi(
                    host=user_input[CONF_HOST],
                    username=user_input[CONF_USERNAME],
                    password=user_input[CONF_PASSWORD],
                    session=async_get_clientsession(self.hass),
                )
                _, name = await api.get_device_type()
                return self.async_create_entry(
                    title=f"JUDO {name} ({device_number})",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=_user_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> config_entries.ConfigFlowResult:
        entry = self._get_reconfigure_entry()
        errors: dict[str, str] = {}
        if user_input is not None:
            if not user_input.get(CONF_CLOUD_USER):
                user_input.pop(CONF_CLOUD_USER, None)
                user_input.pop(CONF_CLOUD_PASSWORD, None)
            err, _ = await _validate(self.hass, user_input)
            if err:
                errors["base"] = err
            else:
                # Strip cloud creds from the stored entry if they were cleared.
                merged = {**entry.data, **user_input}
                if CONF_CLOUD_USER not in user_input:
                    merged.pop(CONF_CLOUD_USER, None)
                    merged.pop(CONF_CLOUD_PASSWORD, None)
                return self.async_update_reload_and_abort(entry, data=merged)
        return self.async_show_form(
            step_id="reconfigure",
            data_schema=_user_schema(entry.data),
            errors=errors,
        )
