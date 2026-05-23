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
    coordinator = hass.data[DOMAIN][entry.entry_id]
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
