"""Transport and decoding for the GBS Control device."""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Iterator
import logging
import re

import aiohttp

from .const import (
    APPLIED_RESOLUTIONS,
    FLAG_BASE,
    FLAGS_BYTE3,
    FLAGS_BYTE4,
    FLAGS_BYTE5,
    FRAME_LEN,
    FRAME_MARKER,
    HTTP_PORT,
    INPUT_FORMAT_TEXT,
    PATH_SLOTS_BIN,
    PATH_SPIFFS_DIR,
    PATH_WIFI_STATUS,
    SLOT_INDEX_MAP,
    SLOT_NAME_LEN,
    SLOT_RECORD_LEN,
    VIDEO_MODES,
    WS_PORT,
)

_LOGGER = logging.getLogger(__name__)


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


def parse_slots(data: bytes) -> list[dict]:
    """Parse /bin/slots.bin into a list of {index, char, name}.

    Each record is SLOT_RECORD_LEN bytes starting with a SLOT_NAME_LEN-byte
    name; slot index i maps to identifier char SLOT_INDEX_MAP[i].
    """
    slots: list[dict] = []
    count = min(len(SLOT_INDEX_MAP), len(data) // SLOT_RECORD_LEN)
    for i in range(count):
        record = data[i * SLOT_RECORD_LEN : (i + 1) * SLOT_RECORD_LEN]
        name = record[:SLOT_NAME_LEN].split(b"\x00", 1)[0].decode("latin-1", "replace").strip()
        slots.append({"index": i, "char": SLOT_INDEX_MAP[i], "name": name})
    return slots


# --- WebSocket text channel -------------------------------------------------
# Besides the 6-byte status frame, the device mirrors every serial print to the
# WebSocket (firmware SerialMirror), one frame per print() call, so a line
# arrives as several fragments: b"preset applied: ", b"1280x960", b" for ", ...
# TextLineAssembler glues fragments back into lines; parse_text_line turns the
# lines we understand into state.


class TextLineAssembler:
    """Accumulate text fragments and yield complete lines."""

    def __init__(self) -> None:
        self._buf = ""

    def feed(self, text: str) -> Iterator[str]:
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            line = line.strip("\r ")
            if line:
                yield line
        # ponytail: cap runaway buffers (e.g. the 'i' print-info stream) at 1 KiB
        if len(self._buf) > 1024:
            self._buf = self._buf[-512:]


# Every regex below is anchored on a literal the firmware prints (gbs-control.ino).
_RE_PRESET_APPLIED = re.compile(
    r"^preset applied: (?P<res>\S+)(?: \((?P<kind>bypass|custom)\))? for (?P<input>.+)$"
)
_RE_FORMAT_CHANGE = re.compile(r"^Format change:\s*(?P<mode>\d+) <(?P<stable>stable|not stable)>")
_RE_SOURCE_HZ = re.compile(r"source Hz: (?P<src>[\d.]+)[, ]+(?:new out|output Hz): (?P<out>[\d.]+)")
_RE_COMMAND_LOG = re.compile(
    r"^(?:user|serial) command . at settings source (?P<pref>\d+), custom slot \d+, "
    r"status (?P<preset>[0-9a-fA-F]+)$"
)
_RE_WIFI_IP = re.compile(r"^\(WiFi\): STA mode connected; IP: (?P<ip>\S+)")
_RE_FTL_METHOD = re.compile(r"(?:^frame lock method = |Method: )(?P<method>[01])")
_RE_PRESET_PREF = re.compile(r"^preset preference = (?P<pref>\d+)$")
_RE_VALUE = re.compile(r"^(?P<name>[A-Za-z_/ ]+?)(?:\+\+|--)? ?: (?P<value>[0-9A-Fa-f]+)$")

# "<name>[++|--] : <value>" prints -> (state key, base). Brightness/contrast/gain
# are printed by the /uc Z T N M Q H P S step commands; Y_OFFSET/Y_GAIN/UCOS_GAIN
# by /uc O (color info); ADC gain by /uc n o; scanline brightness by /uc K.
_VALUE_KEYS = {
    "Brightness": ("brightness", 10),
    "Y_OFFSET": ("brightness", 10),
    "Contrast": ("contrast", 10),
    "Y_GAIN": ("contrast", 10),
    "Pb/U gain": ("pb_gain", 10),
    "UCOS_GAIN": ("pb_gain", 10),
    "Pr/V gain": ("pr_gain", 10),
    "ADC gain": ("adc_gain", 16),
    "Scanline Brightness": ("scanline_strength", 16),
}


def _input_format(text: str) -> str | None:
    for prefix, key in INPUT_FORMAT_TEXT.items():
        if text.startswith(prefix):
            return key
    return None


def parse_text_line(line: str) -> dict:
    """Extract state from one serial-mirror line; {} if not a line we know."""
    if line == "no signal":
        return {"signal": False, "input_format": "none"}

    if m := _RE_PRESET_APPLIED.match(line):
        state: dict = {
            "signal": True,
            "output_resolution": APPLIED_RESOLUTIONS.get(m["res"]),
            "custom_preset": m["kind"] == "custom",
        }
        if fmt := _input_format(m["input"]):
            state["input_format"] = fmt
        return state

    if m := _RE_FORMAT_CHANGE.match(line):
        fmt = VIDEO_MODES.get(int(m["mode"]))
        state = {"signal": m["stable"] == "stable"}
        if fmt is not None:
            state["input_format"] = fmt
        return state

    if m := _RE_SOURCE_HZ.search(line):
        return {"source_hz": float(m["src"]), "output_hz": float(m["out"])}

    if m := _RE_COMMAND_LOG.match(line):
        return {"preset_id": int(m["preset"], 16), "preset_preference": int(m["pref"])}

    if m := _RE_WIFI_IP.match(line):
        return {"ip_address": m["ip"]}

    if m := _RE_FTL_METHOD.search(line):
        return {"frame_time_lock_method": int(m["method"])}

    if m := _RE_PRESET_PREF.match(line):
        return {"preset_preference": int(m["pref"])}

    if m := _RE_VALUE.match(line):
        spec = _VALUE_KEYS.get(m["name"].strip())
        if spec is not None:
            key, base = spec
            return {key: int(m["value"], base)}

    return {}


# Single command char goes into the URL as a bare query-param name, e.g. /uc?7
# (the firmware reads request->getParam(0)->name().charAt(0)).


class GBSControlApiClient:
    """HTTP + WebSocket transport for one GBS Control device."""

    def __init__(self, host: str, session: aiohttp.ClientSession) -> None:
        self._host = host
        self._session = session

    @property
    def base_url(self) -> str:
        return f"http://{self._host}:{HTTP_PORT}" if HTTP_PORT != 80 else f"http://{self._host}"

    @property
    def ws_url(self) -> str:
        return f"ws://{self._host}:{WS_PORT}/"

    async def send_command(self, path: str, char: str) -> None:
        """Send a single-character command (e.g. path='/uc', char='7')."""
        url = f"{self.base_url}{path}?{char}"
        async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()

    async def send_path(self, path: str) -> None:
        """GET a plain command path with no char (e.g. /gbs/restore-filters)."""
        url = f"{self.base_url}{path}"
        async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()

    async def send_get(self, path: str, params: dict[str, str]) -> None:
        """GET a path with value-based query params (e.g. /slot/set?slot=0).

        Unlike send_command (which uses the bare param NAME), the slot endpoints
        read param VALUES, and order matters (the firmware uses getParam(0/1)).
        """
        url = f"{self.base_url}{path}"
        async with self._session.get(
            url, params=params, timeout=aiohttp.ClientTimeout(total=10)
        ) as resp:
            resp.raise_for_status()

    async def get_slots(self) -> list[dict]:
        """Fetch and parse the device's saved preset slots."""
        url = f"{self.base_url}{PATH_SLOTS_BIN}"
        async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            data = await resp.read()
        return parse_slots(data)

    async def get_wifi_status(self) -> dict:
        """GET /wifi/status -> {"mode": "sta", "ssid": "..."} or {"mode": "ap"}."""
        url = f"{self.base_url}{PATH_WIFI_STATUS}"
        async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
        return data if isinstance(data, dict) else {}

    async def get_spiffs_dir(self) -> list[str]:
        """GET /spiffs/dir -> list of file names on the device filesystem."""
        url = f"{self.base_url}{PATH_SPIFFS_DIR}"
        async with self._session.get(url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
            resp.raise_for_status()
            data = await resp.json(content_type=None)
        return [str(f) for f in data] if isinstance(data, list) else []

    async def async_check_connection(self) -> bool:
        """Return True if the device root responds 200."""
        try:
            async with self._session.get(
                f"{self.base_url}/", timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                return resp.status == 200
        except (TimeoutError, aiohttp.ClientError):
            return False

    async def listen(
        self,
        on_frame: Callable[[bytes], None],
        stop_event: asyncio.Event,
        on_connection: Callable[[bool], None] | None = None,
    ) -> None:
        """Connect the WebSocket and feed raw frame bytes to on_frame until stopped.

        Reconnects with backoff on drop (the ESP8266 disconnects clients when
        its heap runs low). Returns only when stop_event is set. If given,
        on_connection is called with True once connected and False when the
        connection drops, so callers can track device availability.
        """
        backoff = 1
        while not stop_event.is_set():
            connected = False
            try:
                # heartbeat=30 is the idle-drop guard once connected: aiohttp
                # pings every 30s and closes the socket if no pong arrives.
                async with self._session.ws_connect(self.ws_url, heartbeat=30) as ws:
                    # Reset backoff on a successful connect; it only grows while
                    # the device is unreachable (connect attempts raise below).
                    backoff = 1
                    connected = True
                    if on_connection is not None:
                        on_connection(True)
                    async for msg in ws:
                        if stop_event.is_set():
                            break
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            # Firmware uses broadcastTXT; bytes are <= 0x7f so latin-1 round-trips.
                            on_frame(msg.data.encode("latin-1", "replace"))
                        elif msg.type == aiohttp.WSMsgType.BINARY:
                            on_frame(msg.data)
                        elif msg.type in (
                            aiohttp.WSMsgType.CLOSE,
                            aiohttp.WSMsgType.CLOSING,
                            aiohttp.WSMsgType.CLOSED,
                            aiohttp.WSMsgType.ERROR,
                        ):
                            break
            except (TimeoutError, aiohttp.ClientError) as err:
                _LOGGER.debug("GBS Control WebSocket error: %s", err)
            finally:
                if connected and on_connection is not None:
                    on_connection(False)
            if stop_event.is_set():
                break
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)
