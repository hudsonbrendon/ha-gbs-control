"""Tests for the GBS Control API client."""
import asyncio
import re
from unittest.mock import AsyncMock, patch

import aiohttp
from aioresponses import aioresponses
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import pytest

from custom_components.gbs_control.api import GBSControlApiClient, decode_status
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


class _FakeResponse:
    """Minimal async-context-manager stand-in for an aiohttp response."""

    def raise_for_status(self) -> None:
        return None

    async def __aenter__(self) -> "_FakeResponse":
        return self

    async def __aexit__(self, *exc) -> bool:
        return False


async def test_send_command_builds_uc_url(hass):
    # The command char is the bare query-param NAME, so the built URL must be
    # exactly ".../uc?7". aioresponses normalises bare params away, so we capture
    # the URL passed to session.get directly to prove the char is included.
    session = async_get_clientsession(hass)
    client = GBSControlApiClient("gbscontrol.local", session)
    captured: dict[str, str] = {}

    def _capture(url, **kwargs):
        captured["url"] = url
        return _FakeResponse()

    with patch.object(session, "get", side_effect=_capture):
        await client.send_command("/uc", "7")

    assert captured["url"] == "http://gbscontrol.local/uc?7"


async def test_send_sc_command_builds_sc_url(hass):
    session = async_get_clientsession(hass)
    client = GBSControlApiClient("gbscontrol.local", session)
    captured: dict[str, str] = {}

    def _capture(url, **kwargs):
        captured["url"] = url
        return _FakeResponse()

    with patch.object(session, "get", side_effect=_capture):
        await client.send_command("/sc", "T")

    assert captured["url"] == "http://gbscontrol.local/sc?T"


async def test_send_path_get(hass):
    session = async_get_clientsession(hass)
    client = GBSControlApiClient("gbscontrol.local", session)
    captured: dict[str, str] = {}

    def _capture(url, **kwargs):
        captured["url"] = url
        return _FakeResponse()

    with patch.object(session, "get", side_effect=_capture):
        await client.send_path("/gbs/restore-filters")

    assert captured["url"] == "http://gbscontrol.local/gbs/restore-filters"


async def test_send_get_passes_query_params(hass):
    session = async_get_clientsession(hass)
    client = GBSControlApiClient("gbscontrol.local", session)
    captured: dict = {}

    def _capture(url, **kwargs):
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        return _FakeResponse()

    with patch.object(session, "get", side_effect=_capture):
        await client.send_get("/slot/save", {"index": "2", "name": "Foo"})

    assert captured["url"] == "http://gbscontrol.local/slot/save"
    assert captured["params"] == {"index": "2", "name": "Foo"}


async def test_send_command_raises_on_error_status(hass):
    # A non-2xx device response must propagate (send_command calls raise_for_status).
    session = async_get_clientsession(hass)
    client = GBSControlApiClient("gbscontrol.local", session)
    with aioresponses() as mocked:
        mocked.get(re.compile(r"http://gbscontrol\.local/uc.*"), status=500)
        with pytest.raises(aiohttp.ClientResponseError):
            await client.send_command("/uc", "7")


async def test_async_check_connection_true(hass):
    session = async_get_clientsession(hass)
    client = GBSControlApiClient("gbscontrol.local", session)
    with aioresponses() as mocked:
        mocked.get("http://gbscontrol.local/", status=200, body=b"gzip-bytes")
        assert await client.async_check_connection() is True


async def test_async_check_connection_false_on_error(hass):
    from aiohttp import ClientError

    session = async_get_clientsession(hass)
    client = GBSControlApiClient("gbscontrol.local", session)
    with aioresponses() as mocked:
        mocked.get("http://gbscontrol.local/", exception=ClientError())
        assert await client.async_check_connection() is False


# --- listen() reconnect-loop coverage ---------------------------------------


class _FakeWS:
    """Async-context-manager + async-iterator standing in for a WS connection."""

    def __init__(self, messages):
        self._messages = list(messages)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    def __aiter__(self):
        return self

    async def __anext__(self):
        if not self._messages:
            raise StopAsyncIteration
        return self._messages.pop(0)


class _RaisingCM:
    def __init__(self, exc):
        self._exc = exc

    async def __aenter__(self):
        raise self._exc

    async def __aexit__(self, *exc):
        return False


class _FakeSession:
    """Yields a scripted sequence of ws_connect attempts."""

    def __init__(self, attempts):
        self._attempts = attempts
        self.connect_calls = 0

    def ws_connect(self, url, **kwargs):
        attempt = self._attempts[min(self.connect_calls, len(self._attempts) - 1)]
        self.connect_calls += 1
        if isinstance(attempt, Exception):
            return _RaisingCM(attempt)
        return _FakeWS(attempt)


async def test_listen_reconnects_and_reports_connection():
    # Attempt 1 fails to connect; attempt 2 connects, delivers one status frame,
    # then closes. on_frame stops the loop after the first frame.
    frame = bytes([ord("#"), ord("1"), 0, 0x40, 0x40, 0x40])
    messages = [
        aiohttp.WSMessage(aiohttp.WSMsgType.TEXT, frame.decode("latin-1"), None),
        aiohttp.WSMessage(aiohttp.WSMsgType.CLOSE, None, None),
    ]
    session = _FakeSession([aiohttp.ClientError("boom"), messages])
    client = GBSControlApiClient("gbscontrol.local", session)

    stop = asyncio.Event()
    frames: list[bytes] = []
    connections: list[bool] = []

    def on_frame(raw: bytes) -> None:
        frames.append(raw)
        stop.set()

    def on_connection(connected: bool) -> None:
        connections.append(connected)

    with patch("custom_components.gbs_control.api.asyncio.sleep", new=AsyncMock()):
        await asyncio.wait_for(client.listen(on_frame, stop, on_connection), timeout=5)

    assert frames == [frame]  # frame decoded and forwarded after the reconnect
    assert connections == [True, False]  # connected, then dropped on close
    assert session.connect_calls == 2  # retried after the first failed connect
