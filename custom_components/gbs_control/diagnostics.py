"""Diagnostics support for GBS Control."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import GBSControlCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator: GBSControlCoordinator = hass.data[DOMAIN][entry.entry_id]
    return {
        "host": coordinator.host,
        "connected": coordinator.connected,
        "data": dict(coordinator.data),
    }
