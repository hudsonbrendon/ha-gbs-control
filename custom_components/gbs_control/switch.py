"""GBS Control switches."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import SWITCHES
from .coordinator import GBSConfigEntry, GBSControlCoordinator
from .entity import GBSControlEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: GBSConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GBSSwitch(coordinator, key, on_path, on_char, off_path, off_char)
        for key, on_path, on_char, off_path, off_char in SWITCHES
    )


class GBSSwitch(GBSControlEntity, SwitchEntity):
    """A boolean device option. The device commands are toggles, so we only
    send a command when the requested state differs from the reported state."""

    def __init__(
        self,
        coordinator: GBSControlCoordinator,
        key: str,
        on_path: str,
        on_char: str,
        off_path: str,
        off_char: str,
    ) -> None:
        super().__init__(coordinator, key)
        self._on_path = on_path
        self._on_char = on_char
        self._off_path = off_path
        self._off_char = off_char

    @property
    def is_on(self) -> bool | None:
        return self.coordinator.data.get(self._key)

    async def async_turn_on(self, **kwargs: Any) -> None:
        # The device command is a blind toggle, so only act when we KNOW the
        # option is currently off. If state is unknown (None, before the first
        # WebSocket frame) we do nothing rather than risk inverting it.
        if self.is_on is False:
            await self.coordinator.api.send_command(self._on_path, self._on_char)

    async def async_turn_off(self, **kwargs: Any) -> None:
        if self.is_on is True:
            await self.coordinator.api.send_command(self._off_path, self._off_char)
