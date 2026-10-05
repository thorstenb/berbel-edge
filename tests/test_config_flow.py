"""Config flow tests for the Berbel Skyline integration.

These tests need Home Assistant and its custom-component test plugin.
"""

import pytest

pytest.importorskip("homeassistant")
pytest.importorskip("pytest_homeassistant_custom_component")

from unittest.mock import patch

from bleak.backends.device import BLEDevice
from bleak.backends.scanner import AdvertisementData

from homeassistant.components.bluetooth import BluetoothServiceInfoBleak
from homeassistant.config_entries import SOURCE_BLUETOOTH, SOURCE_USER
from homeassistant.const import CONF_ADDRESS
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType

from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.berbel.const import DOMAIN

HOOD_ADDRESS = "9C:9E:FF:FF:FF:FF"
HOOD_NAME = "SKE_P"


def make_service_info(
    name: str = HOOD_NAME, address: str = HOOD_ADDRESS
) -> BluetoothServiceInfoBleak:
    """Build the discovery object the Bluetooth integration hands to a config flow."""
    return BluetoothServiceInfoBleak(
        name=name,
        address=address,
        rssi=-60,
        manufacturer_data={},
        service_data={},
        service_uuids=[],
        source="local",
        device=BLEDevice(address=address, name=name, details=None),
        advertisement=AdvertisementData(
            local_name=name,
            manufacturer_data={},
            service_data={},
            service_uuids=[],
            tx_power=-127,
            rssi=-60,
            platform_data=(),
        ),
        connectable=True,
        time=0.0,
        tx_power=-127,
    )


@pytest.fixture(autouse=True)
def load_custom_integrations(enable_custom_integrations):
    """Let Home Assistant find the integration under custom_components."""
    yield


@pytest.fixture(autouse=True)
def mock_setup_entry():
    """Keep entry creation from running the real setup, which needs a radio."""
    with patch(
        "custom_components.berbel.async_setup_entry", return_value=True
    ) as setup_mock:
        yield setup_mock


async def test_bluetooth_discovery_creates_an_entry(hass: HomeAssistant) -> None:
    """A discovered hood is confirmed by the user and becomes a config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=make_service_info(),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "bluetooth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == HOOD_NAME
    assert result["data"] == {CONF_ADDRESS: HOOD_ADDRESS}
    assert result["result"].unique_id == HOOD_ADDRESS.upper()


async def test_bluetooth_discovery_aborts_for_a_configured_hood(
    hass: HomeAssistant,
) -> None:
    """A hood that already has a config entry is not listed again."""
    MockConfigEntry(domain=DOMAIN, unique_id=HOOD_ADDRESS.upper()).add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_BLUETOOTH},
        data=make_service_info(),
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_user_step_lists_discovered_hoods_and_creates_an_entry(
    hass: HomeAssistant,
) -> None:
    """The manual setup lists the discovered hoods and sets up the selected one."""
    with patch(
        "custom_components.berbel.config_flow.async_discovered_service_info",
        return_value=[make_service_info()],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
        assert result["type"] is FlowResultType.FORM
        assert result["step_id"] == "user"

        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={CONF_ADDRESS: HOOD_ADDRESS}
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == HOOD_NAME
    assert result["data"] == {CONF_ADDRESS: HOOD_ADDRESS}


async def test_user_step_aborts_without_discovered_hoods(hass: HomeAssistant) -> None:
    """The manual setup aborts when nothing has been discovered."""
    with patch(
        "custom_components.berbel.config_flow.async_discovered_service_info",
        return_value=[],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_user_step_ignores_devices_with_unknown_names(
    hass: HomeAssistant,
) -> None:
    """A device whose local name matches no Berbel prefix is never listed."""
    with patch(
        "custom_components.berbel.config_flow.async_discovered_service_info",
        return_value=[make_service_info(name="OTHER_DEVICE", address="AA:BB:CC:DD:EE:FF")],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"


async def test_user_step_ignores_already_configured_hoods(
    hass: HomeAssistant,
) -> None:
    """A hood that already has a config entry does not show up in the pick list."""
    MockConfigEntry(domain=DOMAIN, unique_id=HOOD_ADDRESS.upper()).add_to_hass(hass)
    with patch(
        "custom_components.berbel.config_flow.async_discovered_service_info",
        return_value=[make_service_info()],
    ):
        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": SOURCE_USER}
        )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "no_devices_found"
