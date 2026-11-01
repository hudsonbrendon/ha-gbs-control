"""Tests for the GBS Control coordinator."""

from datetime import timedelta
from unittest.mock import AsyncMock, patch

from homeassistant.helpers import issue_registry as ir
from homeassistant.util import dt as dt_util
from pytest_homeassistant_custom_component.common import async_fire_time_changed

from custom_components.gbs_control.const import DOMAIN
from custom_components.gbs_control.coordinator import (
    OFFLINE_GRACE_SECONDS,
    GBSControlCoordinator,
)


async def test_handle_frame_updates_data(hass):
    coordinator = GBSControlCoordinator(hass, "gbscontrol.local")
    # base 0x40 flag bytes, scanlines bit set in byte 3 (bit 1)
    frame = bytes([ord("#"), ord("2"), 5, 0x40 | (1 << 1), 0x40, 0x40])
    coordinator._handle_frame(frame)
    assert coordinator.data["preset"] == "2"
    assert coordinator.data["slot"] == 5
    assert coordinator.data["scanlines"] is True


async def test_handle_frame_ignores_log_noise(hass):
    coordinator = GBSControlCoordinator(hass, "gbscontrol.local")
    coordinator.async_set_updated_data({"preset": "1"})  # seed
    coordinator._handle_frame(b"MCU: some log line")
    # unchanged — noise did not overwrite state
    assert coordinator.data == {"preset": "1"}


async def test_connection_state_tracked(hass):
    coordinator = GBSControlCoordinator(hass, "gbscontrol.local")
    assert coordinator.connected is False
    coordinator._handle_connection(True)
    assert coordinator.connected is True
    coordinator._handle_connection(False)
    assert coordinator.connected is False
    await coordinator.async_stop()  # cancel the pending offline timer


async def test_refresh_slots_updates_state(hass):
    coordinator = GBSControlCoordinator(hass, "gbscontrol.local")
    slots = [{"index": 0, "char": "A", "name": "PS1"}]
    with patch.object(coordinator.api, "get_slots", new=AsyncMock(return_value=slots)):
        await coordinator.async_refresh_slots()
    assert coordinator.slots == slots


async def test_offline_raises_and_clears_repair_issue(hass):
    coordinator = GBSControlCoordinator(hass, "gbscontrol.local")
    reg = ir.async_get(hass)

    coordinator._handle_connection(True)
    coordinator._handle_connection(False)  # schedules the offline timer
    # No issue during the grace period.
    assert reg.async_get_issue(DOMAIN, coordinator._issue_id) is None

    # Advance past the grace period -> the timer fires and raises the issue.
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=OFFLINE_GRACE_SECONDS + 1))
    await hass.async_block_till_done()
    assert reg.async_get_issue(DOMAIN, coordinator._issue_id) is not None

    # Reconnecting clears it.
    coordinator._handle_connection(True)
    assert reg.async_get_issue(DOMAIN, coordinator._issue_id) is None


async def test_text_lines_merge_with_status(hass):
    coordinator = GBSControlCoordinator(hass, "gbscontrol.local")
    frame = bytes([ord("#"), ord("1"), 65, 0x40, 0x40, 0x40])
    coordinator._handle_frame(frame)
    assert coordinator.data["signal"] is True  # preset '1' loaded = source present
    # Text arrives fragmented; parsed values persist across later status frames.
    for frag in (b"preset applied: ", b"1280x960", b" for ", b"NTSC 60Hz ", b"\r\n"):
        coordinator._handle_frame(frag)
    assert coordinator.data["input_format"] == "ntsc_480i"
    assert coordinator.data["output_resolution"] == "1280x960"
    coordinator._handle_frame(bytes([ord("#"), ord("0"), 65, 0x40, 0x40, 0x40]))
    assert coordinator.data["preset"] == "0"
    assert coordinator.data["signal"] is False  # status frame wins over text
    assert coordinator.data["input_format"] == "ntsc_480i"  # text state kept


async def test_refresh_info_seeds_wifi_and_prints(hass):
    coordinator = GBSControlCoordinator(hass, "gbscontrol.local")
    with (
        patch.object(
            coordinator.api,
            "get_wifi_status",
            new=AsyncMock(return_value={"mode": "sta", "ssid": "net"}),
        ),
        patch.object(coordinator.api, "send_command", new=AsyncMock()) as send,
        patch("custom_components.gbs_control.coordinator.asyncio.sleep", new=AsyncMock()),
    ):
        await coordinator.async_refresh_info()
    assert coordinator.wifi == {"mode": "sta", "ssid": "net"}
    assert [c.args for c in send.await_args_list] == [("/uc", "e"), ("/uc", "O")]
