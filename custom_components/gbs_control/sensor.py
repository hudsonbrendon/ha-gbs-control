"""GBS Control sensors."""
from __future__ import annotations

from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, PRESET_LABELS
from .entity import GBSControlEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            GBSPresetSensor(coordinator, "output_preset"),
            GBSSlotSensor(coordinator, "active_slot"),
        ]
    )


class GBSPresetSensor(GBSControlEntity, SensorEntity):
    _attr_name = "Output preset"
    _attr_icon = "mdi:television"

    @property
    def native_value(self) -> str | None:
        preset = self.coordinator.data.get("preset")
        if preset is None:
            return None
        return PRESET_LABELS.get(preset, "Unknown")


class GBSSlotSensor(GBSControlEntity, SensorEntity):
    _attr_name = "Active slot"
    _attr_icon = "mdi:memory"

    @property
    def native_value(self) -> int | None:
        return self.coordinator.data.get("slot")
