"""Tests for the gbs_control.send_command service."""
from unittest.mock import AsyncMock, patch

from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import device_registry as dr
import pytest
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import DOMAIN


async def _setup(hass):
    entry = MockConfigEntry(domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local")
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    coordinator = entry.runtime_data
    device = dr.async_get(hass).async_get_device(identifiers={(DOMAIN, "gbscontrol.local")})
    return coordinator, device


async def test_send_command_service_uc_and_sc(hass):
    coordinator, device = await _setup(hass)

    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            DOMAIN, "send_command",
            {"device_id": device.id, "command": "K", "path": "uc"},
            blocking=True,
        )
        send.assert_awaited_once_with("/uc", "K")

    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            DOMAIN, "send_command",
            {"device_id": device.id, "command": "Z", "path": "sc"},
            blocking=True,
        )
        send.assert_awaited_once_with("/sc", "Z")


async def test_send_command_service_defaults_to_uc(hass):
    coordinator, device = await _setup(hass)
    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            DOMAIN, "send_command", {"device_id": device.id, "command": "a"}, blocking=True
        )
        send.assert_awaited_once_with("/uc", "a")


async def test_send_command_service_unknown_device(hass):
    await _setup(hass)
    with pytest.raises(ServiceValidationError):
        await hass.services.async_call(
            DOMAIN, "send_command",
            {"device_id": "does-not-exist", "command": "a"},
            blocking=True,
        )


async def test_set_slot_service(hass):
    coordinator, device = await _setup(hass)
    with patch.object(coordinator.api, "send_get", new=AsyncMock()) as send:
        await hass.services.async_call(
            DOMAIN, "set_slot", {"device_id": device.id, "slot": "0"}, blocking=True
        )
        send.assert_awaited_once_with("/slot/set", {"slot": "0"})


async def test_save_slot_service_preserves_param_order(hass):
    coordinator, device = await _setup(hass)
    with patch.object(coordinator.api, "send_get", new=AsyncMock()) as send:
        await hass.services.async_call(
            DOMAIN, "save_slot",
            {"device_id": device.id, "index": 2, "name": "SNES 720p"},
            blocking=True,
        )
        send.assert_awaited_once_with("/slot/save", {"index": "2", "name": "SNES 720p"})


async def test_remove_slot_service(hass):
    coordinator, device = await _setup(hass)
    with patch.object(coordinator.api, "send_command", new=AsyncMock()) as send:
        await hass.services.async_call(
            DOMAIN, "remove_slot", {"device_id": device.id}, blocking=True
        )
        send.assert_awaited_once_with("/slot/remove", "1")
