"""GBS Control output resolution select."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, RESOLUTION_COMMANDS
from .coordinator import GBSControlCoordinator
from .entity import GBSControlEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GBSResolutionSelect(coordinator, "output_resolution")])


class GBSResolutionSelect(GBSControlEntity, SelectEntity):
    """Loads an output resolution preset. The device exposes no readback that
    maps cleanly to a resolution label, so current_option is optimistic —
    it reflects the last resolution this entity commanded."""

    _attr_icon = "mdi:monitor-screenshot"
    _attr_options = list(RESOLUTION_COMMANDS)

    def __init__(self, coordinator: GBSControlCoordinator, key: str) -> None:
        super().__init__(coordinator, key)
        self._current: str | None = None

    @property
    def current_option(self) -> str | None:
        return self._current

    async def async_select_option(self, option: str) -> None:
        await self.coordinator.api.send_command("/uc", RESOLUTION_COMMANDS[option])
        self._current = option
        self.async_write_ha_state()
