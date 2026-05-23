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

# Output preset indicator (frame byte 1) -> human label.
PRESET_LABELS = {
    "0": "Unknown",
    "1": "Preset 1",
    "2": "Preset 2",
    "3": "Preset 3",
    "4": "Preset 4",
    "5": "Preset 5",
    "6": "Preset 6",
    "8": "Bypass",
    "9": "Custom",
}

# Command endpoints.
PATH_UC = "/uc"
PATH_SC = "/sc"
PATH_RESTORE_FILTERS = "/gbs/restore-filters"

# Resolution select: option label -> /uc command char (verified in firmware).
RESOLUTION_COMMANDS = {
    "1280x960": "f",
    "1280x720": "g",
    "720x480 / 768x576": "h",
    "1280x1024": "p",
    "1920x1080": "s",
    "Downscale": "L",
}

# Switch definitions: key, friendly name, on_path, on_char, off_path, off_char.
# For plain toggles on-char == off-char (the device flips current state).
SWITCHES = [
    ("scanlines", "Scanlines", PATH_UC, "7", PATH_UC, "7"),
    ("line_filter", "Line filter", PATH_UC, "m", PATH_UC, "m"),
    ("frame_time_lock", "Frame time lock", PATH_UC, "5", PATH_UC, "5"),
    ("pal_force_60", "Force PAL to 60Hz", PATH_UC, "0", PATH_UC, "0"),
    ("tap6", "6-tap filter", PATH_UC, "t", PATH_UC, "t"),
    ("full_height", "Full height", PATH_UC, "v", PATH_UC, "v"),
    ("adc_calibration", "ADC calibration", PATH_UC, "w", PATH_UC, "w"),
    ("scaling_rgbhv", "Scaling RGBHV", PATH_UC, "x", PATH_UC, "x"),
    ("ext_clock_disabled", "External clock disabled", PATH_UC, "X", PATH_UC, "X"),
    ("peaking", "Peaking", PATH_SC, "f", PATH_SC, "f"),
    ("auto_gain", "Auto gain", PATH_SC, "T", PATH_SC, "T"),
    ("output_component", "Component output", PATH_SC, "L", PATH_SC, "L"),
    ("match_preset_source", "Match preset to source", PATH_SC, "Z", PATH_SC, "Z"),
    # deinterlace uses distinct on/off commands (q = motion-adaptive on, r = bob off)
    ("deinterlace", "Motion-adaptive deinterlace", PATH_UC, "q", PATH_UC, "r"),
]

# Button definitions: key, friendly name, endpoint, char (None = path is a direct GET).
# The adjustment buttons fire firmware step/cycle commands that have no readback,
# so they are momentary actions rather than stateful entities.
BUTTONS = [
    ("reboot", "Reboot", PATH_UC, "a"),
    ("restore_defaults", "Restore defaults", PATH_UC, "1"),
    ("save_custom_preset", "Save custom preset", PATH_UC, "4"),
    ("load_custom_preset", "Load custom preset", PATH_UC, "3"),
    ("restore_filters", "Restore filters", PATH_RESTORE_FILTERS, None),
    ("scanline_strength", "Cycle scanline strength", PATH_UC, "K"),
    ("sdram_clock", "Cycle SDRAM clock", PATH_UC, "l"),
    ("frame_time_lock_method", "Cycle frame-time-lock method", PATH_UC, "i"),
    ("vertical_mask_increase", "Vertical mask increase", PATH_UC, "C"),
    ("vertical_mask_decrease", "Vertical mask decrease", PATH_UC, "D"),
]
