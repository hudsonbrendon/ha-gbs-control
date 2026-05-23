"""Tests for the GBS Control API client."""
import pytest

from custom_components.gbs_control.api import decode_status
from custom_components.gbs_control.const import (
    FLAGS_BYTE3,
    FLAGS_BYTE4,
    FLAGS_BYTE5,
)


def _frame(preset: int, slot: int, b3: int, b4: int, b5: int) -> bytes:
    return bytes([ord("#"), preset, slot, b3, b4, b5])


def test_decode_status_all_flags_off():
    # base 0x40 ('@') on every flag byte = all options off
    frame = _frame(ord("1"), 2, 0x40, 0x40, 0x40)
    state = decode_status(frame)
    assert state["preset"] == "1"
    assert state["slot"] == 2
    # Full contract: preset + slot + every flag key, all flags off.
    expected_keys = (
        {"preset", "slot"}
        | set(FLAGS_BYTE3.values())
        | set(FLAGS_BYTE4.values())
        | set(FLAGS_BYTE5.values())
    )
    assert set(state) == expected_keys
    assert all(state[flag] is False for flag in expected_keys - {"preset", "slot"})


def test_decode_status_specific_flags_on():
    # byte3 bit1 scanlines + bit3 peaking; byte4 bit2 deinterlace; byte5 bit1 scaling_rgbhv
    b3 = 0x40 | (1 << 1) | (1 << 3)
    b4 = 0x40 | (1 << 2)
    b5 = 0x40 | (1 << 1)
    state = decode_status(_frame(ord("8"), 0, b3, b4, b5))
    assert state["preset"] == "8"
    assert state["scanlines"] is True
    assert state["peaking"] is True
    assert state["auto_gain"] is False
    assert state["deinterlace"] is True
    assert state["scaling_rgbhv"] is True


def test_decode_status_rejects_non_status_frame():
    assert decode_status(b"some serial log line") is None
    assert decode_status(b"#log: ") is None  # 6 bytes but flag bytes lack 0x40 base
    assert decode_status(b"") is None
    # 6 bytes, starts with '#', but flag bytes missing 0x40 marker -> log noise
    assert decode_status(bytes([ord("#"), 1, 2, 3, 4, 5])) is None
