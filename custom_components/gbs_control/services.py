"""Services for GBS Control."""
from __future__ import annotations

from homeassistant.core import HomeAssistant, ServiceCall, callback
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers import device_registry as dr
import voluptuous as vol

from .const import DOMAIN, PATH_SC, PATH_UC
from .coordinator import GBSControlCoordinator

SERVICE_SEND_COMMAND = "send_command"
ATTR_DEVICE_ID = "device_id"
ATTR_COMMAND = "command"
ATTR_PATH = "path"

# Friendly path name -> endpoint. /uc = user/web commands, /sc = low-level serial.
_PATHS = {"uc": PATH_UC, "sc": PATH_SC}

SEND_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_COMMAND): vol.All(cv.string, vol.Length(min=1, max=1)),
        vol.Optional(ATTR_PATH, default="uc"): vol.In(list(_PATHS)),
    }
)


def _coordinator_for_device(hass: HomeAssistant, device_id: str) -> GBSControlCoordinator:
    """Resolve a HA device id to its GBS Control coordinator."""
    device = dr.async_get(hass).async_get(device_id)
    if device is None:
        raise ServiceValidationError(f"Unknown device id: {device_id}")
    for entry_id in device.config_entries:
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is not None and entry.domain == DOMAIN:
            coordinator = getattr(entry, "runtime_data", None)
            if isinstance(coordinator, GBSControlCoordinator):
                return coordinator
    raise ServiceValidationError(f"Device {device_id} is not a GBS Control device")


@callback
def async_setup_services(hass: HomeAssistant) -> None:
    """Register integration services (idempotent)."""

    async def handle_send_command(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        path = _PATHS[call.data[ATTR_PATH]]
        await coordinator.api.send_command(path, call.data[ATTR_COMMAND])

    if not hass.services.has_service(DOMAIN, SERVICE_SEND_COMMAND):
        hass.services.async_register(
            DOMAIN, SERVICE_SEND_COMMAND, handle_send_command, schema=SEND_COMMAND_SCHEMA
        )
