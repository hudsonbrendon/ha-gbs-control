"""Tests for the GBS Control connectivity binary sensor."""
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import DOMAIN

ENTITY = "binary_sensor.gbs_control_connectivity"


async def test_connectivity_off_when_disconnected_but_still_available(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    # No WebSocket yet: the connectivity sensor reports "off", NOT "unavailable"
    # (reporting disconnected is its whole job).
    state = hass.states.get(ENTITY)
    assert state is not None
    assert state.state == "off"


async def test_connectivity_on_when_connected(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    coordinator._handle_connection(True)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "on"

    coordinator._handle_connection(False)
    await hass.async_block_till_done()
    assert hass.states.get(ENTITY).state == "off"
