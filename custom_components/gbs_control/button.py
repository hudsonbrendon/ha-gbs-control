"""GBS Control buttons."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import BUTTONS
from .coordinator import GBSConfigEntry, GBSControlCoordinator
from .entity import GBSControlEntity

PARALLEL_UPDATES = 1


async def async_setup_entry(
    hass: HomeAssistant, entry: GBSConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator = entry.runtime_data
    async_add_entities(
        GBSButton(coordinator, key, path, char, category, enabled)
        for key, path, char, category, enabled in BUTTONS
    )


class GBSButton(GBSControlEntity, ButtonEntity):
    def __init__(
        self,
        coordinator: GBSControlCoordinator,
        key: str,
        path: str,
        char: str | None,
        category: str | None,
        enabled: bool,
    ) -> None:
        super().__init__(coordinator, key)
        self._path = path
        self._char = char
        self._attr_entity_category = EntityCategory(category) if category else None
        self._attr_entity_registry_enabled_default = enabled

    async def async_press(self) -> None:
        if self._char is None:
            await self.coordinator.api.send_path(self._path)
        else:
            await self.coordinator.api.send_command(self._path, self._char)
