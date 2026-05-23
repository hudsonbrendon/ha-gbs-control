"""Tests for the GBS Control resolution select."""
from unittest.mock import AsyncMock, patch

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import DOMAIN, RESOLUTION_COMMANDS


async def test_select_options_and_command(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    coordinator = hass.data[DOMAIN][entry.entry_id]
    coordinator._handle_connection(True)  # simulate a connected device

    state = hass.states.get("select.gbs_control_output_resolution")
    assert state is not None
    assert set(state.attributes["options"]) == set(RESOLUTION_COMMANDS)

    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            "select",
            "select_option",
            {"entity_id": "select.gbs_control_output_resolution", "option": "1920x1080"},
            blocking=True,
        )
        send.assert_awaited_once_with("/uc", "s")

    state = hass.states.get("select.gbs_control_output_resolution")
    assert state.state == "1920x1080"
