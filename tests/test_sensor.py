"""Tests for GBS Control sensors."""

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import DOMAIN


async def test_sensors_render_from_coordinator(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local"
    )
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
    entry = MockConfigEntry(
        domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local"
    )
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
    entry = MockConfigEntry(
        domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local"
    )
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


async def test_text_derived_sensors(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local"
    )
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data
    coordinator.wifi = {"mode": "sta", "ssid": "CASA"}
    coordinator._handle_connection(True)
    coordinator.async_set_updated_data(
        {
            "preset": "9",
            "slot": ord("A"),
            "input_format": "hdtv_720p",
            "output_resolution": "1920x1080",
            "custom_preset": True,
            "source_hz": 59.941,
            "output_hz": 59.941,
            "frame_time_lock_method": 1,
            "ip_address": "192.168.31.248",
            "brightness": 3,
            "contrast": 128,
            "adc_gain": 0x7A,
        }
    )
    await hass.async_block_till_done()
    get = hass.states.get
    assert get("sensor.gbs_control_input_format").state == "hdtv_720p"
    assert get("sensor.gbs_control_source_field_rate").state == "59.941"
    assert get("sensor.gbs_control_output_frame_rate").attributes["unit_of_measurement"] == "Hz"
    assert get("sensor.gbs_control_frame_time_lock_method").state == "vtotal_only"
    assert get("sensor.gbs_control_wi_fi_network").state == "CASA"
    assert get("sensor.gbs_control_ip_address").state == "192.168.31.248"
    assert get("sensor.gbs_control_brightness").state == "3"
    assert get("sensor.gbs_control_contrast").state == "128"
    assert get("sensor.gbs_control_adc_gain").state == "122"
    preset = get("sensor.gbs_control_output_preset")
    assert preset.state == "custom"
    assert preset.attributes["resolution"] == "1920x1080"
