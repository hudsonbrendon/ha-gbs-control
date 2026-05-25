"""GBS Control sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import PRESET_OPTIONS, PRESET_STATES, SLOT_EMPTY_NAME
from .coordinator import GBSConfigEntry
from .entity import GBSControlEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: GBSConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        [
            GBSPresetSensor(coordinator, "output_preset"),
            GBSSlotSensor(coordinator, "active_slot"),
        ]
    )


class GBSPresetSensor(GBSControlEntity, SensorEntity):
    """Current output preset as a translatable enum."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = PRESET_OPTIONS

    @property
    def native_value(self) -> str | None:
        preset = self.coordinator.data.get("preset")
        if preset is None:
            return None
        return PRESET_STATES.get(preset)  # None for '0'/unknown


class GBSSlotSensor(GBSControlEntity, SensorEntity):
    """Active preset slot — shows the saved slot name when known, else its char."""

    @property
    def native_value(self) -> str | None:
        slot_byte = self.coordinator.data.get("slot")
        if slot_byte is None:
            return None
        char = chr(slot_byte)
        for slot in self.coordinator.slots:
            if (
                slot["char"] == char
                and slot["name"]
                and slot["name"] != SLOT_EMPTY_NAME
            ):
                return str(slot["name"])
        return char
