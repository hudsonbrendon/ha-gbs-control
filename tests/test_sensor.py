"""Tests for GBS Control sensors."""
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import DOMAIN


async def test_sensors_render_from_coordinator(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    coordinator._handle_connection(True)  # simulate a connected device
    coordinator.async_set_updated_data({"preset": "8", "slot": ord("A")})
    await hass.async_block_till_done()

    # Enum sensor: state is the stable key (display name is translated).
    preset = hass.states.get("sensor.gbs_control_output_preset")
    assert preset is not None
    assert preset.state == "bypass"

    # No slots loaded -> active slot falls back to its identifier char.
    slot = hass.states.get("sensor.gbs_control_active_slot")
    assert slot.state == "A"


async def test_active_slot_shows_saved_name(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    coordinator.slots = [{"index": 0, "char": "A", "name": "PS1"}]
    coordinator._handle_connection(True)
    coordinator.async_set_updated_data({"preset": "1", "slot": ord("A")})
    await hass.async_block_till_done()

    assert hass.states.get("sensor.gbs_control_active_slot").state == "PS1"


async def test_sensor_unavailable_until_connected(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # No WebSocket connection yet -> entity reports unavailable, not stale data.
    preset = hass.states.get("sensor.gbs_control_output_preset")
    assert preset.state == "unavailable"

    coordinator = entry.runtime_data
    coordinator._handle_connection(True)
    coordinator.async_set_updated_data({"preset": "1", "slot": 0})
    await hass.async_block_till_done()
    preset = hass.states.get("sensor.gbs_control_output_preset")
    assert preset.state == "preset_1"
