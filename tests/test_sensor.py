"""Tests for GBS Control sensors."""
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import DOMAIN


async def test_sensors_render_from_coordinator(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator.async_set_updated_data({"preset": "8", "slot": 3})
    await hass.async_block_till_done()

    preset = hass.states.get("sensor.gbs_control_output_preset")
    assert preset is not None
    assert preset.state == "Bypass"

    slot = hass.states.get("sensor.gbs_control_active_slot")
    assert slot.state == "3"
