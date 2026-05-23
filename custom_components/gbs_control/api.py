"""Transport and decoding for the GBS Control device."""
from __future__ import annotations

import asyncio
import logging
from collections.abc import Callable

import aiohttp

from .const import (
    FLAG_BASE,
    FLAGS_BYTE3,
    FLAGS_BYTE4,
    FLAGS_BYTE5,
    FRAME_LEN,
    FRAME_MARKER,
    HTTP_PORT,
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

    async def async_check_connection(self) -> bool:
        """Return True if the device root responds 200."""
        try:
            async with self._session.get(
                f"{self.base_url}/", timeout=aiohttp.ClientTimeout(total=10)
            ) as resp:
                return resp.status == 200
        except (aiohttp.ClientError, asyncio.TimeoutError):
            return False

    async def listen(
        self,
        on_frame: Callable[[bytes], None],
        stop_event: asyncio.Event,
    ) -> None:
        """Connect the WebSocket and feed raw frame bytes to on_frame until stopped.

        Reconnects with backoff on drop (the ESP8266 disconnects clients when
        its heap runs low). Returns only when stop_event is set.
        """
        backoff = 1
        while not stop_event.is_set():
            try:
                # heartbeat=30 is the idle-drop guard once connected: aiohttp
                # pings every 30s and closes the socket if no pong arrives.
                async with self._session.ws_connect(
                    self.ws_url, heartbeat=30
                ) as ws:
                    # Reset backoff on a successful connect; it only grows while
                    # the device is unreachable (connect attempts raise below).
                    backoff = 1
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
            except (aiohttp.ClientError, asyncio.TimeoutError) as err:
                _LOGGER.debug("GBS Control WebSocket error: %s", err)
            if stop_event.is_set():
                break
            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, 30)
