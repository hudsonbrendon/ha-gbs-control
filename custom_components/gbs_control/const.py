"""Constants for the GBS Control integration."""
from __future__ import annotations

DOMAIN = "gbs_control"
DEFAULT_HOST = "gbscontrol.local"
DEFAULT_NAME = "GBS Control"

# Network ports on the device firmware.
HTTP_PORT = 80
WS_PORT = 81

# Status frame: exactly 6 bytes, byte 0 == '#', flag bytes carry the 0x40 base marker.
FRAME_LEN = 6
FRAME_MARKER = ord("#")
FLAG_BASE = 0x40  # '@' — present on every valid flag byte (bytes 3, 4, 5)

# Flag bit -> state key, per firmware updateWebSocketData().
FLAGS_BYTE3 = {
    0: "auto_gain",
    1: "scanlines",
    2: "line_filter",
    3: "peaking",
    4: "pal_force_60",
    5: "output_component",
}
FLAGS_BYTE4 = {
    0: "match_preset_source",
    1: "frame_time_lock",
    2: "deinterlace",
    3: "tap6",
    4: "step_response",  # decoded for completeness; no control exposed (no verified command)
    5: "full_height",
}
FLAGS_BYTE5 = {
    0: "adc_calibration",
    1: "scaling_rgbhv",
    2: "ext_clock_disabled",
}

# Output preset indicator (frame byte 1) -> enum state key (translated in
# strings.json under entity.sensor.output_preset.state). '0'/unknown -> None.
PRESET_STATES = {
    "1": "preset_1",
    "2": "preset_2",
    "3": "preset_3",
    "4": "preset_4",
    "5": "preset_5",
    "6": "preset_6",
    "8": "bypass",
    "9": "custom",
}
PRESET_OPTIONS = list(PRESET_STATES.values())

# Command endpoints.
PATH_UC = "/uc"
PATH_SC = "/sc"
PATH_RESTORE_FILTERS = "/gbs/restore-filters"
PATH_SLOTS_BIN = "/bin/slots.bin"
PATH_SLOT_SET = "/slot/set"

# Preset slots: /bin/slots.bin is SLOTS_TOTAL records of SLOT_RECORD_LEN bytes,
# each starting with a SLOT_NAME_LEN-byte name. Slot index i maps to the
# identifier char SLOT_INDEX_MAP[i] (firmware slotIndexMap), e.g. 0 -> "A".
SLOT_RECORD_LEN = 32
SLOT_NAME_LEN = 25
SLOT_INDEX_MAP = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~()!*:,"
SLOT_EMPTY_NAME = "Empty"

# Resolution select: option label -> /uc command char (verified in firmware).
RESOLUTION_COMMANDS = {
    "1280x960": "f",
    "1280x720": "g",
    "720x480 / 768x576": "h",
    "1280x1024": "p",
    "1920x1080": "s",
    "Downscale": "L",
}

# Switch definitions: key, on_path, on_char, off_path, off_char.
# For plain toggles on-char == off-char (the device flips current state).
# Display names live in strings.json (entity.switch.<key>.name) for translation.
SWITCHES = [
    ("scanlines", PATH_UC, "7", PATH_UC, "7"),
    ("line_filter", PATH_UC, "m", PATH_UC, "m"),
    ("frame_time_lock", PATH_UC, "5", PATH_UC, "5"),
    ("pal_force_60", PATH_UC, "0", PATH_UC, "0"),
    ("tap6", PATH_UC, "t", PATH_UC, "t"),
    ("full_height", PATH_UC, "v", PATH_UC, "v"),
    ("adc_calibration", PATH_UC, "w", PATH_UC, "w"),
    ("scaling_rgbhv", PATH_UC, "x", PATH_UC, "x"),
    ("ext_clock_disabled", PATH_UC, "X", PATH_UC, "X"),
    ("peaking", PATH_SC, "f", PATH_SC, "f"),
    ("auto_gain", PATH_SC, "T", PATH_SC, "T"),
    ("output_component", PATH_SC, "L", PATH_SC, "L"),
    ("match_preset_source", PATH_SC, "Z", PATH_SC, "Z"),
    # deinterlace uses distinct on/off commands (q = motion-adaptive on, r = bob off)
    ("deinterlace", PATH_UC, "q", PATH_UC, "r"),
]

# Button definitions: key, endpoint, char (None = path is a direct GET).
# The adjustment buttons fire firmware step/cycle commands that have no readback,
# so they are momentary actions rather than stateful entities.
# Display names live in strings.json (entity.button.<key>.name) for translation.
BUTTONS = [
    ("reboot", PATH_UC, "a"),
    ("restore_defaults", PATH_UC, "1"),
    ("save_custom_preset", PATH_UC, "4"),
    ("load_custom_preset", PATH_UC, "3"),
    ("restore_filters", PATH_RESTORE_FILTERS, None),
    ("scanline_strength", PATH_UC, "K"),
    ("sdram_clock", PATH_UC, "l"),
    ("frame_time_lock_method", PATH_UC, "i"),
    ("vertical_mask_increase", PATH_UC, "C"),
    ("vertical_mask_decrease", PATH_UC, "D"),
]
