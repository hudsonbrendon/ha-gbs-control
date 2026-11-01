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
    4: "step_response",
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

# Resolution select: option label -> (path, command char), verified in firmware
# handleType2Command (/uc f g h p s L) and the serial handler (/sc K = HD bypass,
# the web UI "Pass Through" button).
RESOLUTION_COMMANDS = {
    "1280x960": (PATH_UC, "f"),
    "1280x720": (PATH_UC, "g"),
    "720x480 / 768x576": (PATH_UC, "h"),
    "1280x1024": (PATH_UC, "p"),
    "1920x1080": (PATH_UC, "s"),
    "Downscale": (PATH_UC, "L"),
    "Pass-through": (PATH_SC, "K"),
}

# Status-frame preset byte -> resolution select option (firmware updateWebSocketData:
# presetID 0x01/0x11 -> '1' 1280x960, 0x02/0x12 -> '2' 1280x1024, 0x03/0x13 -> '3'
# 1280x720, 0x04/0x14 -> '4' 720x480/768x576, 0x05/0x15 -> '5' 1920x1080,
# 0x06/0x16 -> '6' downscale, HD/RGBHV bypass -> '8'). '9' (custom) and '0' (no
# preset loaded) carry no resolution.
PRESET_RESOLUTIONS = {
    "1": "1280x960",
    "2": "1280x1024",
    "3": "1280x720",
    "4": "720x480 / 768x576",
    "5": "1920x1080",
    "6": "Downscale",
    "8": "Pass-through",
}

# "preset applied: <res> ... for <input>" resolution word -> select option.
APPLIED_RESOLUTIONS = {
    "1280x960": "1280x960",
    "1280x1024": "1280x1024",
    "1280x720": "1280x720",
    "720x480": "720x480 / 768x576",
    "768x576": "720x480 / 768x576",
    "1920x1080": "1920x1080",
    "downscale": "Downscale",
    "bypass": "Pass-through",
}

# Input format (firmware rto->videoStandardInput / getVideoMode()) -> enum key.
VIDEO_MODES = {
    0: "none",
    1: "ntsc_480i",
    2: "pal_576i",
    3: "edtv_480p",
    4: "edtv_576p",
    5: "hdtv_720p",
    6: "hdtv_1080i",
    7: "hdtv_1080p",
    8: "medium_res",
    13: "vga_graphic",
    14: "rgbhv_scaling",
    15: "rgbhv_bypass",
}
INPUT_FORMAT_OPTIONS = list(VIDEO_MODES.values())

# Prefix of the "for <input>" text in "preset applied:" lines -> enum key.
INPUT_FORMAT_TEXT = {
    "NTSC 60Hz": "ntsc_480i",
    "PAL 50Hz": "pal_576i",
    "EDTV 60Hz": "edtv_480p",
    "EDTV 50Hz": "edtv_576p",
    "720p 60Hz HDTV": "hdtv_720p",
    "1080i 60Hz HDTV": "hdtv_1080i",
    "1080p 60Hz HDTV": "hdtv_1080p",
    "Medium Res": "medium_res",
    "VGA/SVGA/XGA/SXGA": "vga_graphic",
    "scaling RGB": "rgbhv_scaling",
    "RGB Bypass": "rgbhv_bypass",
}

# Frame-time-lock method (firmware uopt->frameTimeLockMethod) -> enum key.
FTL_METHODS = {0: "vtotal_vsst", 1: "vtotal_only"}
FTL_METHOD_OPTIONS = list(FTL_METHODS.values())

# Read-only JSON endpoints.
PATH_WIFI_STATUS = "/wifi/status"
PATH_SPIFFS_DIR = "/spiffs/dir"

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
    ("step_response", PATH_SC, "V", PATH_SC, "V"),
    # deinterlace uses distinct on/off commands (q = motion-adaptive on, r = bob off)
    ("deinterlace", PATH_UC, "q", PATH_UC, "r"),
]

# Button definitions: key, endpoint, char (None = path is a direct GET), category
# (None = primary control, "config" or "diagnostic") and enabled-by-default.
# All chars verified in the firmware command handlers (/uc = handleType2Command,
# /sc = serial handler) and cross-checked with the web UI button labels.
# The adjustment buttons fire step/cycle commands that have no readback, so they
# are momentary actions rather than stateful entities. Developer-tab toggles
# without any readback are disabled by default.
BUTTONS = [
    # System
    ("reboot", PATH_UC, "a", None, True),
    ("restore_defaults", PATH_UC, "1", "config", True),
    ("save_custom_preset", PATH_UC, "4", None, True),
    ("load_custom_preset", PATH_UC, "3", None, True),
    ("restore_filters", PATH_RESTORE_FILTERS, None, "config", True),
    ("list_options", PATH_UC, "e", "diagnostic", True),
    ("wifi_reconnect", PATH_UC, "u", "diagnostic", False),
    ("enable_ota", PATH_SC, "c", "config", False),
    # Picture
    ("scanline_strength", PATH_UC, "K", "config", True),
    ("sdram_clock", PATH_UC, "l", "config", True),
    ("frame_time_lock_method", PATH_UC, "i", "config", True),
    ("brightness_increase", PATH_UC, "Z", None, True),
    ("brightness_decrease", PATH_UC, "T", None, True),
    ("contrast_increase", PATH_UC, "N", None, True),
    ("contrast_decrease", PATH_UC, "M", None, True),
    ("pb_gain_increase", PATH_UC, "Q", None, True),
    ("pb_gain_decrease", PATH_UC, "H", None, True),
    ("pr_gain_increase", PATH_UC, "P", None, True),
    ("pr_gain_decrease", PATH_UC, "S", None, True),
    ("color_defaults", PATH_UC, "U", None, True),
    ("color_info", PATH_UC, "O", "diagnostic", True),
    ("adc_gain_increase", PATH_UC, "n", None, True),
    ("adc_gain_decrease", PATH_UC, "o", None, True),
    # Geometry
    ("vertical_mask_increase", PATH_UC, "C", None, True),
    ("vertical_mask_decrease", PATH_UC, "D", None, True),
    ("horizontal_mask_increase", PATH_UC, "A", None, True),
    ("horizontal_mask_decrease", PATH_UC, "B", None, True),
    ("shift_left", PATH_SC, "7", None, True),
    ("shift_right", PATH_SC, "6", None, True),
    ("shift_up", PATH_SC, "*", None, True),
    ("shift_down", PATH_SC, "/", None, True),
    ("scale_horizontal_increase", PATH_SC, "z", None, True),
    ("scale_horizontal_decrease", PATH_SC, "h", None, True),
    ("scale_vertical_increase", PATH_SC, "4", None, True),
    ("scale_vertical_decrease", PATH_SC, "5", None, True),
    ("memory_left", PATH_SC, "-", "config", False),
    ("memory_right", PATH_SC, "+", "config", False),
    ("hsync_left", PATH_SC, "1", "config", False),
    ("hsync_right", PATH_SC, "0", "config", False),
    # Sync / developer
    ("htotal_increase", PATH_SC, "a", "config", False),
    ("htotal_decrease", PATH_SC, "A", "config", False),
    ("resync_htotal", PATH_SC, ".", "config", True),
    ("snap_frame_rate", PATH_SC, "S", "config", True),
    ("reset_sync_processor", PATH_SC, "l", "config", True),
    ("reset_chip", PATH_SC, "q", "config", True),
    ("oversampling", PATH_SC, "o", "config", False),
    ("invert_sync", PATH_SC, "8", "config", False),
    ("pll_divider_increase", PATH_SC, "n", "config", False),
    ("sog_level_decrease", PATH_UC, "z", "config", False),
    ("video_timings", PATH_SC, ",", "diagnostic", False),
    ("freeze_capture", PATH_UC, "F", "config", False),
    ("adc_filter", PATH_SC, "F", "config", False),
    ("if_auto_offset", PATH_UC, "E", "config", False),
    ("debug_view", PATH_SC, "D", "config", False),
    ("sync_watcher", PATH_SC, "m", "config", False),
]
