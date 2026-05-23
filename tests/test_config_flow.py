"""Tests for the GBS Control config flow."""
from unittest.mock import patch

from homeassistant import config_entries, data_entry_flow

from custom_components.gbs_control.const import DOMAIN


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
