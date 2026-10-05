"""Shared base entity for the Berbel Skyline integration.

Every entity of the integration wraps a reference to the one, shared
BerbelDevice of its config entry. The device pushes state and
availability changes through callbacks, so the entities do not need to
poll.

"""

from __future__ import annotations

from homeassistant.core import callback
from homeassistant.helpers.device_registry import CONNECTION_BLUETOOTH, DeviceInfo
from homeassistant.helpers.entity import Entity

from .berbel_ble import BerbelDevice, BerbelState


class BerbelEntity(Entity):
    """Base entity bound to one Berbel Skyline."""

    _attr_has_entity_name = True
    _attr_should_poll = False

    def __init__(self, device: BerbelDevice) -> None:
        """Bind the entity to its device and describe the device registry entry."""
        self._device = device
        self._attr_device_info = DeviceInfo(
            connections={(CONNECTION_BLUETOOTH, device.address)},
            name=device.name or "Berbel hood",
            manufacturer="Berbel",
            model=device.model,
            sw_version=device.fw_version,
        )

    @property
    def available(self) -> bool:
        """The entity is available while the connection to the hood is up."""
        return self._device.available

    async def async_added_to_hass(self) -> None:
        """Subscribe to the pushed state and availability updates of the device."""
        self.async_on_remove(
            self._device.register_callback(self._handle_state_update)
        )
        self.async_on_remove(
            self._device.register_availability_callback(
                self._handle_availability_update
            )
        )

    @callback
    def _handle_state_update(self, state: BerbelState) -> None:
        """Write a pushed main state frame through to Home Assistant."""
        self.async_write_ha_state()

    @callback
    def _handle_availability_update(self, available: bool) -> None:
        """Write a connection state change through to Home Assistant."""
        self.async_write_ha_state()
