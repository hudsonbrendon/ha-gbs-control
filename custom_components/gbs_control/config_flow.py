"""Config flow for GBS Control."""
from __future__ import annotations

from typing import TYPE_CHECKING

import voluptuous as vol
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import GBSControlApiClient
from .const import DEFAULT_HOST, DOMAIN

if TYPE_CHECKING:
    from homeassistant.components.zeroconf import ZeroconfServiceInfo


class GBSControlConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for GBS Control."""

    VERSION = 1

    def __init__(self) -> None:
        self._discovered_host: str | None = None
        self._discovered_name: str | None = None

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

    async def async_step_zeroconf(
        self, discovery_info: ZeroconfServiceInfo
    ) -> ConfigFlowResult:
        """Handle a device discovered via mDNS (gbscontrol.local)."""
        # The mDNS hostname is stable across DHCP changes; use it as the unique
        # id, but connect over the discovered IP for reliable HTTP/WS access.
        name = discovery_info.hostname.rstrip(".")
        host = str(discovery_info.host)
        await self.async_set_unique_id(name)
        self._abort_if_unique_id_configured(updates={"host": host})

        self._discovered_host = host
        self._discovered_name = name
        self.context["title_placeholders"] = {"name": name}
        return await self.async_step_zeroconf_confirm()

    async def async_step_zeroconf_confirm(
        self, user_input=None
    ) -> ConfigFlowResult:
        """Confirm adding a discovered device."""
        if user_input is not None:
            client = GBSControlApiClient(
                self._discovered_host, async_get_clientsession(self.hass)
            )
            if await client.async_check_connection():
                return self.async_create_entry(
                    title=self._discovered_name,
                    data={"host": self._discovered_host},
                )
            return self.async_abort(reason="cannot_connect")

        return self.async_show_form(
            step_id="zeroconf_confirm",
            description_placeholders={"name": self._discovered_name},
        )
