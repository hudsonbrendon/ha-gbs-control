"""GBS Control sensors."""

from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.const import EntityCategory, UnitOfFrequency
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import (
    FTL_METHOD_OPTIONS,
    FTL_METHODS,
    INPUT_FORMAT_OPTIONS,
    PRESET_OPTIONS,
    PRESET_STATES,
    SLOT_EMPTY_NAME,
)
from .coordinator import GBSConfigEntry, GBSControlCoordinator
from .entity import GBSControlEntity

PARALLEL_UPDATES = 0

# Plain value sensors fed by parsed WebSocket text: key -> entity category.
# Values only change when the device prints them (step buttons, colour info).
VALUE_SENSORS = {
    "brightness": None,
    "contrast": None,
    "pb_gain": None,
    "pr_gain": None,
    "adc_gain": None,
    "scanline_strength": None,
}


async def async_setup_entry(
    hass: HomeAssistant, entry: GBSConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[SensorEntity] = [
        GBSPresetSensor(coordinator, "output_preset"),
        GBSSlotSensor(coordinator, "active_slot"),
        GBSInputFormatSensor(coordinator, "input_format"),
        GBSFrequencySensor(coordinator, "source_hz"),
        GBSFrequencySensor(coordinator, "output_hz"),
        GBSFtlMethodSensor(coordinator, "frame_time_lock_method"),
        GBSWifiSsidSensor(coordinator, "wifi_ssid"),
        GBSValueSensor(coordinator, "ip_address", EntityCategory.DIAGNOSTIC),
    ]
    entities += [GBSValueSensor(coordinator, key, cat) for key, cat in VALUE_SENSORS.items()]
    async_add_entities(entities)


class GBSPresetSensor(GBSControlEntity, SensorEntity):
    """Current output preset as a translatable enum (resolution names)."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = PRESET_OPTIONS

    @property
    def native_value(self) -> str | None:
        preset = self.coordinator.data.get("preset")
        if preset is None:
            return None
        return PRESET_STATES.get(preset)  # None for '0'/unknown

    @property
    def extra_state_attributes(self) -> dict:
        # From the "preset applied:" line: the real resolution even for custom presets.
        data = self.coordinator.data
        return {
            "resolution": data.get("output_resolution"),
            "custom_preset": data.get("custom_preset"),
            "preset_id": data.get("preset_id"),
        }


class GBSSlotSensor(GBSControlEntity, SensorEntity):
    """Active preset slot — shows the saved slot name when known, else its char."""

    @property
    def native_value(self) -> str | None:
        slot_byte = self.coordinator.data.get("slot")
        if slot_byte is None:
            return None
        char = chr(slot_byte)
        for slot in self.coordinator.slots:
            if slot["char"] == char and slot["name"] and slot["name"] != SLOT_EMPTY_NAME:
                return str(slot["name"])
        return char


class GBSInputFormatSensor(GBSControlEntity, SensorEntity):
    """Detected input video format (from "preset applied" / "Format change")."""

    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = INPUT_FORMAT_OPTIONS

    @property
    def native_value(self) -> str | None:
        return self.coordinator.data.get("input_format")


class GBSFrequencySensor(GBSControlEntity, SensorEntity):
    """Source field rate / output frame rate (printed on frame-time-lock runs)."""

    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_state_class = SensorStateClass.MEASUREMENT
    _attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
    _attr_suggested_display_precision = 3

    @property
    def native_value(self) -> float | None:
        return self.coordinator.data.get(self._key)


class GBSFtlMethodSensor(GBSControlEntity, SensorEntity):
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = FTL_METHOD_OPTIONS
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str | None:
        method = self.coordinator.data.get("frame_time_lock_method")
        return None if method is None else FTL_METHODS.get(method)


class GBSWifiSsidSensor(GBSControlEntity, SensorEntity):
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def native_value(self) -> str | None:
        wifi = self.coordinator.wifi
        return wifi.get("ssid") if wifi.get("mode") == "sta" else wifi.get("mode")


class GBSValueSensor(GBSControlEntity, SensorEntity):
    """A plain value read from the device's printed output."""

    def __init__(
        self, coordinator: GBSControlCoordinator, key: str, category: EntityCategory | None
    ) -> None:
        super().__init__(coordinator, key)
        self._attr_entity_category = category

    @property
    def native_value(self) -> int | str | None:
        return self.coordinator.data.get(self._key)
