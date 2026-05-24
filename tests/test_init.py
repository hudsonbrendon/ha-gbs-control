"""Tests for setup and unload of the GBS Control entry."""
from homeassistant.config_entries import ConfigEntryState
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import DOMAIN
from custom_components.gbs_control.coordinator import GBSControlCoordinator


async def test_setup_and_unload_entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.LOADED
    assert isinstance(entry.runtime_data, GBSControlCoordinator)

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.NOT_LOADED
