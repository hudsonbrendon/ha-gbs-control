"""Tests for the GBS Control config flow."""
from ipaddress import ip_address
from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow
from homeassistant.components.zeroconf import ZeroconfServiceInfo
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.gbs_control.const import DOMAIN

CHECK_CONNECTION = (
    "custom_components.gbs_control.config_flow.GBSControlApiClient.async_check_connection"
)


def _discovery() -> ZeroconfServiceInfo:
    return ZeroconfServiceInfo(
        ip_address=ip_address("192.168.31.251"),
        ip_addresses=[ip_address("192.168.31.251")],
        port=80,
        hostname="gbscontrol.local.",
        type="_http._tcp.local.",
        name="gbscontrol._http._tcp.local.",
        properties={},
    )


async def test_user_flow_success(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    with patch(
        "custom_components.gbs_control.config_flow.GBSControlApiClient.async_check_connection",
        return_value=True,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "gbscontrol.local"}
        )
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result2["title"] == "gbscontrol.local"
    assert result2["data"] == {"host": "gbscontrol.local"}


async def test_user_flow_cannot_connect(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    with patch(
        "custom_components.gbs_control.config_flow.GBSControlApiClient.async_check_connection",
        return_value=False,
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "bad.local"}
        )
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}


async def test_zeroconf_discovery_flow(hass):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=_discovery()
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"

    with patch(CHECK_CONNECTION, return_value=True):
        result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result2["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    # unique id is the stable mDNS hostname; host is the discovered IP
    assert result2["title"] == "gbscontrol.local"
    assert result2["data"] == {"host": "192.168.31.251"}


async def test_reconfigure_updates_host(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local"
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    with patch(CHECK_CONNECTION, return_value=True):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "192.168.31.251"}
        )
    assert result2["type"] == data_entry_flow.FlowResultType.ABORT
    assert result2["reason"] == "reconfigure_successful"
    assert entry.data["host"] == "192.168.31.251"


async def test_reconfigure_cannot_connect(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"host": "gbscontrol.local"}, unique_id="gbscontrol.local"
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    with patch(CHECK_CONNECTION, return_value=False):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"], {"host": "bad.local"}
        )
    assert result2["type"] == data_entry_flow.FlowResultType.FORM
    assert result2["errors"] == {"base": "cannot_connect"}
    assert entry.data["host"] == "gbscontrol.local"  # unchanged


async def test_zeroconf_aborts_when_already_configured(hass):
    entry = MockConfigEntry(
        domain=DOMAIN, data={"host": "192.168.31.251"}, unique_id="gbscontrol.local"
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_ZEROCONF}, data=_discovery()
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] == "already_configured"
