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
SERVICE_SET_SLOT = "set_slot"
SERVICE_SAVE_SLOT = "save_slot"
SERVICE_REMOVE_SLOT = "remove_slot"
ATTR_DEVICE_ID = "device_id"
ATTR_COMMAND = "command"
ATTR_PATH = "path"
ATTR_SLOT = "slot"
ATTR_INDEX = "index"
ATTR_NAME = "name"

# Friendly path name -> endpoint. /uc = user/web commands, /sc = low-level serial.
_PATHS = {"uc": PATH_UC, "sc": PATH_SC}

SEND_COMMAND_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_COMMAND): vol.All(cv.string, vol.Length(min=1, max=1)),
        vol.Optional(ATTR_PATH, default="uc"): vol.In(list(_PATHS)),
    }
)

SET_SLOT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_SLOT): vol.All(cv.string, vol.Length(min=1, max=1)),
    }
)

SAVE_SLOT_SCHEMA = vol.Schema(
    {
        vol.Required(ATTR_DEVICE_ID): cv.string,
        vol.Required(ATTR_INDEX): vol.All(vol.Coerce(int), vol.Range(min=0)),
        vol.Required(ATTR_NAME): cv.string,
    }
)

REMOVE_SLOT_SCHEMA = vol.Schema({vol.Required(ATTR_DEVICE_ID): cv.string})


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

    async def handle_set_slot(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        await coordinator.api.send_get("/slot/set", {"slot": call.data[ATTR_SLOT]})

    async def handle_save_slot(call: ServiceCall) -> None:
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        # Order matters: the firmware reads getParam(0)=index, getParam(1)=name.
        await coordinator.api.send_get(
            "/slot/save",
            {"index": str(call.data[ATTR_INDEX]), "name": call.data[ATTR_NAME]},
        )

    async def handle_remove_slot(call: ServiceCall) -> None:
        # /slot/remove removes the CURRENTLY ACTIVE slot; a param name other than
        # '0' triggers the removal (the firmware reads getParam(0).name()).
        coordinator = _coordinator_for_device(hass, call.data[ATTR_DEVICE_ID])
        await coordinator.api.send_command("/slot/remove", "1")

    services = (
        (SERVICE_SEND_COMMAND, handle_send_command, SEND_COMMAND_SCHEMA),
        (SERVICE_SET_SLOT, handle_set_slot, SET_SLOT_SCHEMA),
        (SERVICE_SAVE_SLOT, handle_save_slot, SAVE_SLOT_SCHEMA),
        (SERVICE_REMOVE_SLOT, handle_remove_slot, REMOVE_SLOT_SCHEMA),
    )
    for name, handler, schema in services:
        if not hass.services.has_service(DOMAIN, name):
            hass.services.async_register(DOMAIN, name, handler, schema=schema)
