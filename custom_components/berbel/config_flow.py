"""Config flow for the Berbel Skyline integration.

The hood advertises only its local name, so both discovery paths match on the known
name prefixes. The config entry stores nothing but the Bluetooth address.
"""

from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.bluetooth import (
    BluetoothServiceInfoBleak,
    async_discovered_service_info,
)
from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_ADDRESS

from .const import DEVICE_NAME_PREFIXES, DOMAIN


def _is_supported_name(name: str | None) -> bool:
    """Return True when the advertised local name matches a known Berbel prefix."""
    if not name:
        return False
    return name.upper().startswith(DEVICE_NAME_PREFIXES)


class BerbelConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the config flow for a Berbel Skyline."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize the flow."""
        self._discovery_info: BluetoothServiceInfoBleak | None = None
        self._discovered_devices: dict[str, BluetoothServiceInfoBleak] = {}

    async def async_step_bluetooth(
        self, discovery_info: BluetoothServiceInfoBleak
    ) -> ConfigFlowResult:
        """Handle a hood discovered over Bluetooth."""
        await self.async_set_unique_id(discovery_info.address.upper())
        self._abort_if_unique_id_configured()
        self._discovery_info = discovery_info
        self.context["title_placeholders"] = {"name": discovery_info.name}
        return await self.async_step_bluetooth_confirm()

    async def async_step_bluetooth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Ask the user to confirm setting up the discovered hood."""
        assert self._discovery_info is not None
        if user_input is not None:
            return self.async_create_entry(
                title=self._discovery_info.name,
                data={CONF_ADDRESS: self._discovery_info.address},
            )
        self._set_confirm_only()
        return self.async_show_form(
            step_id="bluetooth_confirm",
            description_placeholders={"name": self._discovery_info.name},
        )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Handle a setup started by the user, picking from the discovered hoods."""
        if user_input is not None:
            address = user_input[CONF_ADDRESS]
            discovery = self._discovered_devices[address]
            await self.async_set_unique_id(address.upper(), raise_on_progress=False)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=discovery.name,
                data={CONF_ADDRESS: address},
            )

        current_ids = self._async_current_ids(include_ignore=False)
        for discovery in async_discovered_service_info(self.hass):
            if discovery.address.upper() in current_ids:
                continue
            if not _is_supported_name(discovery.name):
                continue
            self._discovered_devices[discovery.address] = discovery

        if not self._discovered_devices:
            return self.async_abort(reason="no_devices_found")

        picker = {
            address: f"{discovery.name} ({address})"
            for address, discovery in self._discovered_devices.items()
        }
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({vol.Required(CONF_ADDRESS): vol.In(picker)}),
        )
