"""Tests for GBS Control switches."""
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import DOMAIN, SWITCHES


async def test_all_switches_created(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    switch_states = [s for s in hass.states.async_all() if s.entity_id.startswith("switch.")]
    assert len(switch_states) == len(SWITCHES) == 14


async def test_scanlines_turn_on_sends_toggle_only_when_off(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    coordinator._handle_connection(True)  # simulate a connected device
    coordinator.async_set_updated_data({"scanlines": False})
    await hass.async_block_till_done()

    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": "switch.gbs_control_scanlines"}, blocking=True
        )
        send.assert_awaited_once_with("/uc", "7")

    coordinator.async_set_updated_data({"scanlines": True})
    await hass.async_block_till_done()
    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": "switch.gbs_control_scanlines"}, blocking=True
        )
        send.assert_not_awaited()


async def test_deinterlace_uses_distinct_on_off_commands(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    coordinator._handle_connection(True)  # simulate a connected device
    coordinator.async_set_updated_data({"deinterlace": False})
    await hass.async_block_till_done()
    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": "switch.gbs_control_motion_adaptive_deinterlace"}, blocking=True
        )
        send.assert_awaited_once_with("/uc", "q")

    coordinator.async_set_updated_data({"deinterlace": True})
    await hass.async_block_till_done()
    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": "switch.gbs_control_motion_adaptive_deinterlace"}, blocking=True
        )
        send.assert_awaited_once_with("/uc", "r")


async def test_turn_off_noop_when_already_off(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    coordinator._handle_connection(True)  # simulate a connected device
    coordinator.async_set_updated_data({"scanlines": False})
    await hass.async_block_till_done()
    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": "switch.gbs_control_scanlines"}, blocking=True
        )
        send.assert_not_awaited()


async def test_no_command_when_state_unknown(hass):
    # Before the first WebSocket frame, coordinator.data is empty -> is_on None.
    # A blind toggle could invert the device, so neither turn_on nor turn_off
    # should send anything until state is known.
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    coordinator._handle_connection(True)  # simulate a connected device
    assert coordinator.data == {}  # no frame received yet

    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": "switch.gbs_control_scanlines"}, blocking=True
        )
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": "switch.gbs_control_scanlines"}, blocking=True
        )
        send.assert_not_awaited()
