"""Tests for the GBS Control coordinator."""
from custom_components.gbs_control.coordinator import GBSControlCoordinator


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
