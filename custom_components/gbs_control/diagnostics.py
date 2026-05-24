"""Diagnostics support for GBS Control."""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from .coordinator import GBSConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: GBSConfigEntry
) -> dict[str, Any]:
    """Return diagnostics for a config entry."""
    coordinator = entry.runtime_data
    return {
        "host": coordinator.host,
        "connected": coordinator.connected,
        "data": dict(coordinator.data),
    }
