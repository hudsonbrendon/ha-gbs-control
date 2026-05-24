"""Tests for GBS Control diagnostics."""
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import DOMAIN
from custom_components.gbs_control.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics_reports_state(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    coordinator._handle_connection(True)
    coordinator.async_set_updated_data({"preset": "1", "scanlines": True})

    diag = await async_get_config_entry_diagnostics(hass, entry)
    assert diag["host"] == "gbscontrol.local"
    assert diag["connected"] is True
    assert diag["data"] == {"preset": "1", "scanlines": True}
