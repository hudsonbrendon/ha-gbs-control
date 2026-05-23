"""Transport and decoding for the GBS Control device."""
from __future__ import annotations

from .const import (
    FLAG_BASE,
    FLAGS_BYTE3,
    FLAGS_BYTE4,
    FLAGS_BYTE5,
    FRAME_LEN,
    FRAME_MARKER,
)


def decode_status(frame: bytes) -> dict | None:
    """Decode a 6-byte GBS Control status frame.

    Returns a state dict, or None if the bytes are not a status frame
    (the same WebSocket also carries serial log text, which we ignore).
    """
    if len(frame) != FRAME_LEN or frame[0] != FRAME_MARKER:
        return None
    # Every valid flag byte carries the 0x40 base marker; log noise won't.
    if not (frame[3] & FLAG_BASE and frame[4] & FLAG_BASE and frame[5] & FLAG_BASE):
        return None

    state: dict = {
        "preset": chr(frame[1]),
        "slot": frame[2],
    }
    for bit, key in FLAGS_BYTE3.items():
        state[key] = bool(frame[3] & (1 << bit))
    for bit, key in FLAGS_BYTE4.items():
        state[key] = bool(frame[4] & (1 << bit))
    for bit, key in FLAGS_BYTE5.items():
        state[key] = bool(frame[5] & (1 << bit))
    return state
