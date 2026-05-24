"""GBS Control connectivity binary sensor."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .coordinator import GBSConfigEntry
from .entity import GBSControlEntity

PARALLEL_UPDATES = 0


async def async_setup_entry(
    hass: HomeAssistant, entry: GBSConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities([GBSConnectivitySensor(coordinator, "connectivity")])


class GBSConnectivitySensor(GBSControlEntity, BinarySensorEntity):
    """Reports whether the device WebSocket is connected.

    Unlike the other entities it stays available even when the device is
    offline — reporting "off" (disconnected) is its entire purpose.
    """

    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    @property
    def available(self) -> bool:
        return True

    @property
    def is_on(self) -> bool:
        return self.coordinator.connected
