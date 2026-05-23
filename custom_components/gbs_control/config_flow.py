"""Config flow for GBS Control."""
from __future__ import annotations

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GBSControlApiClient
from .const import DEFAULT_HOST, DOMAIN


class GBSControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GBS Control."""

    VERSION = 1

    async def async_step_user(self, user_input=None) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input["host"]
            await self.async_set_unique_id(host)
            self._abort_if_unique_id_configured()

            client = GBSControlApiClient(host, async_get_clientsession(self.hass))
            if await client.async_check_connection():
                return self.async_create_entry(title=host, data={"host": host})
            errors["base"] = "cannot_connect"

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required("host", default=DEFAULT_HOST): str}),
            errors=errors,
        )
