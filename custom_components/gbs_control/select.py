"""GBS Control output resolution select."""
from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import PATH_SLOT_SET, RESOLUTION_COMMANDS, SLOT_EMPTY_NAME
from .coordinator import GBSConfigEntry, GBSControlCoordinator
from .entity import GBSControlEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: GBSConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    entities: list[SelectEntity] = [GBSResolutionSelect(coordinator, "output_resolution")]
    slot_select = GBSSlotSelect(coordinator, "preset_slot")
    if slot_select.options:  # only when the device has named slots
        entities.append(slot_select)
    async_add_entities(entities)


class GBSResolutionSelect(GBSControlEntity, SelectEntity):
    """Loads an output resolution preset. The device exposes no readback that
    maps cleanly to a resolution label, so current_option is optimistic —
    it reflects the last resolution this entity commanded."""

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


class GBSSlotSelect(GBSControlEntity, SelectEntity):
    """Switch between the device's named preset slots.

    Options are the saved (non-empty) slot names read from /bin/slots.bin;
    current_option is derived from the active-slot byte in the status frame.
    Read from coordinator.slots live so a slot refresh updates the options.
    """

    def _name_to_char(self) -> dict[str, str]:
        return {
            slot["name"]: slot["char"]
            for slot in self.coordinator.slots
            if slot["name"] and slot["name"] != SLOT_EMPTY_NAME
        }

    @property
    def options(self) -> list[str]:
        return list(self._name_to_char())

    @property
    def current_option(self) -> str | None:
        slot_byte = self.coordinator.data.get("slot")
        if slot_byte is None:
            return None
        char = chr(slot_byte)
        for name, slot_char in self._name_to_char().items():
            if slot_char == char:
                return name
        return None

    async def async_select_option(self, option: str) -> None:
        char = self._name_to_char().get(option)
        if char is not None:
            await self.coordinator.api.send_get(PATH_SLOT_SET, {"slot": char})
