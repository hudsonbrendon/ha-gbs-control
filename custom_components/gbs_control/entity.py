"""Base entity for GBS Control."""
from __future__ import annotations

from homeassistant.helpers.device_info import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DEFAULT_NAME, DOMAIN
from .coordinator import GBSControlCoordinator


class GBSControlEntity(CoordinatorEntity[GBSControlCoordinator]):
    """Base entity tying everything to one device."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: GBSControlCoordinator, key: str) -> None:
        super().__init__(coordinator)
        self._key = key
        self._attr_unique_id = f"{coordinator.host}_{key}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, coordinator.host)},
            name=DEFAULT_NAME,
            manufacturer="GBS Control",
            model="gbs-control (GBS-8200/8220)",
            configuration_url=f"http://{coordinator.host}",
        )
