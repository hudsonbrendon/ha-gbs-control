"""Tests for GBS Control buttons."""
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import BUTTONS, DOMAIN


async def test_all_buttons_created(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    button_states = [s for s in hass.states.async_all() if s.entity_id.startswith("button.")]
    assert len(button_states) == len(BUTTONS) == 10


async def test_reboot_button_sends_uc_a(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    coordinator._handle_connection(True)  # simulate a connected device
    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            "button", "press", {"entity_id": "button.gbs_control_reboot"}, blocking=True
        )
        send.assert_awaited_once_with("/uc", "a")


async def test_restore_filters_button_uses_path(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = entry.runtime_data
    coordinator._handle_connection(True)  # simulate a connected device
    with patch.object(coordinator.api, "send_path", new=AsyncMock()) as send:
        await hass.services.async_call(
            "button", "press", {"entity_id": "button.gbs_control_restore_filters"}, blocking=True
        )
        send.assert_awaited_once_with("/gbs/restore-filters")
