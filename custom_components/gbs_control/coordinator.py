"""Push-style coordinator backed by the GBS Control WebSocket."""
from __future__ import annotations

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .api import GBSControlApiClient, decode_status
from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

# Config entry typed with its runtime coordinator (stored in entry.runtime_data).
type GBSConfigEntry = ConfigEntry[GBSControlCoordinator]


class GBSControlCoordinator(DataUpdateCoordinator[dict]):
    """Owns the WebSocket lifecycle and the decoded state dict."""

    def __init__(self, hass: HomeAssistant, host: str) -> None:
        super().__init__(hass, _LOGGER, name=DOMAIN)
        self.host = host
        self.api = GBSControlApiClient(host, async_get_clientsession(hass))
        self._stop_event = asyncio.Event()
        self._listen_task: asyncio.Task | None = None
        self._connected = False
        self.slots: list[dict] = []
        self.data = {}

    @property
    def connected(self) -> bool:
        """Whether the WebSocket is currently connected to the device."""
        return self._connected

    async def async_start(self) -> None:
        """Begin listening on the WebSocket and load saved slots (best-effort)."""
        self._stop_event.clear()
        self._listen_task = self.hass.async_create_background_task(
            self.api.listen(self._handle_frame, self._stop_event, self._handle_connection),
            name=f"{DOMAIN}_ws_{self.host}",
        )
        try:
            self.slots = await self.api.get_slots()
        except Exception as err:  # noqa: BLE001 - slots are optional metadata
            _LOGGER.debug("Could not load GBS Control slots: %s", err)

    async def async_stop(self) -> None:
        """Stop listening and tear down the task."""
        self._stop_event.set()
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
            except Exception as err:  # noqa: BLE001 - cleanup must never fail unload
                # The listener may surface a stray error when cancelled mid-I/O
                # (e.g. the DNS resolver). Log it, but never let it block unload.
                _LOGGER.debug("Error stopping GBS Control listener: %s", err)
            self._listen_task = None
        self._handle_connection(False)

    @callback
    def _handle_frame(self, raw: bytes) -> None:
        """Decode one WebSocket frame; ignore non-status frames."""
        state = decode_status(raw)
        if state is None:
            return
        self.async_set_updated_data(state)

    @callback
    def _handle_connection(self, connected: bool) -> None:
        """Track WebSocket connectivity; refresh entity availability on change."""
        if self._connected == connected:
            return
        self._connected = connected
        self.async_update_listeners()
