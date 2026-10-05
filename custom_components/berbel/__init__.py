"""Setup and teardown of a Berbel Skyline config entry.

The config entry carries the Bluetooth address of the hood. Setup connects a BerbelDevice
to that address, stores it as the entry's runtime data and forwards the entry to the
cover, fan and light platforms. The device pushes every state change itself, so there is
no coordinator and no polling needed.
"""

from __future__ import annotations

import logging

from bleak_retry_connector import close_stale_connections_by_address
from homeassistant.components import bluetooth
from homeassistant.components.bluetooth import (
    BluetoothCallbackMatcher,
    BluetoothChange,
    BluetoothScanningMode,
    BluetoothServiceInfoBleak,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_ADDRESS, EVENT_HOMEASSISTANT_STOP, Platform
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import ConfigEntryNotReady

from .berbel_ble import BerbelDevice
from .const import (
    CONF_LIFT_BOTTOM_RAW,
    CONF_LIFT_TOP_RAW,
    DEFAULT_LIFT_BOTTOM_RAW,
    DEFAULT_LIFT_TOP_RAW,
)

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.COVER, Platform.FAN, Platform.LIGHT]

type BerbelConfigEntry = ConfigEntry[BerbelDevice]


async def async_setup_entry(hass: HomeAssistant, entry: BerbelConfigEntry) -> bool:
    """Connect to the hood and set up its platforms."""
    address: str = entry.data[CONF_ADDRESS]
    await close_stale_connections_by_address(address)

    ble_device = bluetooth.async_ble_device_from_address(
        hass, address, connectable=True
    )
    if ble_device is None:
        raise ConfigEntryNotReady(
            f"Berbel Skyline with address {address} is not present or not connectable"
        )

    device = BerbelDevice(
        ble_device,
        lift_top_raw=entry.options.get(CONF_LIFT_TOP_RAW, DEFAULT_LIFT_TOP_RAW),
        lift_bottom_raw=entry.options.get(
            CONF_LIFT_BOTTOM_RAW, DEFAULT_LIFT_BOTTOM_RAW
        ),
    )

    try:
        await device.start()
    except Exception as err:
        await device.stop()
        raise ConfigEntryNotReady(
            f"Could not connect to Berbel Skyline at {address}: {err}"
        ) from err

    # Home Assistant runs the entry's async_on_unload callbacks when the entry unloads
    # and also when setup fails after this point, so the started device is stopped on
    # every exit path, including a platform setup failure further down.
    entry.async_on_unload(device.stop)

    @callback
    def _async_advertisement_received(
        service_info: BluetoothServiceInfoBleak, change: BluetoothChange
    ) -> None:
        """Hand each fresh advertisement to the device, so reconnects use the
        scanner or Bluetooth proxy that saw the hood most recently."""
        device.set_ble_device(service_info.device)

    entry.async_on_unload(
        bluetooth.async_register_callback(
            hass,
            _async_advertisement_received,
            BluetoothCallbackMatcher(address=address, connectable=True),
            BluetoothScanningMode.ACTIVE,
        )
    )

    @callback
    def _async_bluetooth_unavailable(
        service_info: BluetoothServiceInfoBleak,
    ) -> None:
        """Note when no scanner sees the hood any more. The entities report
        unavailability from the connection state, which drops on its own."""
        _LOGGER.debug(
            "Berbel Skyline %s is no longer seen by any Bluetooth scanner", address
        )

    entry.async_on_unload(
        bluetooth.async_track_unavailable(
            hass, _async_bluetooth_unavailable, address, connectable=True
        )
    )

    @callback
    def _async_calibration_changed(top_raw: int, bottom_raw: int) -> None:
        """Persist an observed lift end stop in the entry options, so the
        calibration survives a restart."""
        hass.config_entries.async_update_entry(
            entry,
            options={
                **entry.options,
                CONF_LIFT_TOP_RAW: top_raw,
                CONF_LIFT_BOTTOM_RAW: bottom_raw,
            },
        )

    entry.async_on_unload(
        device.register_calibration_callback(_async_calibration_changed)
    )

    async def _async_stop(event: Event) -> None:
        """Disconnect cleanly when Home Assistant shuts down."""
        await device.stop()

    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _async_stop)
    )

    entry.runtime_data = device
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: BerbelConfigEntry) -> bool:
    """Unload the platforms.

    The device is stopped by the async_on_unload callback that setup registered, which
    Home Assistant runs after a successful unload.
    """
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Let the hood be discovered again once its entry is gone."""
    bluetooth.async_rediscover_address(hass, entry.data[CONF_ADDRESS])
