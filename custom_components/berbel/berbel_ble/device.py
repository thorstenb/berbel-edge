"""Persistent Bluetooth Low Energy connection to a Berbel Skyline.

BerbelDevice keeps one connection open, follows the indications the hood sends on the
main state and settings characteristics, and offers write helpers for the lights, the
color temperatures, the fan and the lift. Lights and color temperatures are written by
sending the whole last-seen frame back with the changed bytes. The fan and the lift use
the command characteristic, as a short press followed by a release fifty milliseconds
later.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable

from bleak.backends.characteristic import BleakGATTCharacteristic
from bleak.backends.device import BLEDevice
from bleak_retry_connector import BleakClientWithServiceCache, establish_connection

from .const import (
    CHAR_COMMAND,
    CHAR_DEVICE_INFO,
    CHAR_FIRMWARE_REVISION,
    CHAR_MAIN_STATE,
    CHAR_MODEL_NUMBER,
    CHAR_SETTINGS,
    COMMAND_FAN_BOOST,
    COMMAND_FAN_OFF,
    COMMAND_LIFT_DOWN,
    COMMAND_LIFT_UP,
    COMMAND_RELEASE,
    DEFAULT_LIFT_BOTTOM_RAW,
    DEFAULT_LIFT_TOP_RAW,
    FAN_LEVEL_COMMANDS,
    FAN_OFF_STATE_TIMEOUT_SECONDS,
    PRESS_RELEASE_GAP_SECONDS,
    RECONNECT_BACKOFF_BASE_SECONDS,
    RECONNECT_BACKOFF_CAP_SECONDS,
    SETTINGS_OFFSET_DOWN_COLOR_TEMP,
    SETTINGS_OFFSET_EFFECT_COLOR_TEMP,
    SETTINGS_OFFSET_TOP_COLOR_TEMP,
    STATE_OFFSET_DOWN_BRIGHTNESS,
    STATE_OFFSET_EFFECT_BLUE,
    STATE_OFFSET_EFFECT_BRIGHTNESS,
    STATE_OFFSET_EFFECT_GREEN,
    STATE_OFFSET_EFFECT_RED,
    STATE_OFFSET_EFFECT_WHITE_BRIGHTNESS,
    STATE_OFFSET_TOP_BRIGHTNESS,
)
from .models import BerbelSettings, BerbelState, LiftMotion

_LOGGER = logging.getLogger(__name__)

_LIFT_MOVING_STATES = (
    LiftMotion.MOVING_UP,
    LiftMotion.MOVING_DOWN,
    LiftMotion.MOVING_UP_END,
    LiftMotion.MOVING_DOWN_END,
)
_LIFT_MOVING_DOWN_STATES = (LiftMotion.MOVING_DOWN, LiftMotion.MOVING_DOWN_END)

# How long a frame write waits for the confirming indication before giving up. The hood
# answers a frame write with an indication on the same characteristic within a fraction
# of a second, so two seconds covers a slow link.
_FRAME_CONFIRM_TIMEOUT_SECONDS = 2.0


def _clamp_byte(value: int) -> int:
    """Clamp a value into the range 0 to 255."""
    return max(0, min(255, int(value)))


class BerbelDevice:
    """One Berbel hood, reached over a persistent Bluetooth Low Energy connection."""

    def __init__(
        self,
        ble_device: BLEDevice,
        *,
        lift_top_raw: int = DEFAULT_LIFT_TOP_RAW,
        lift_bottom_raw: int = DEFAULT_LIFT_BOTTOM_RAW,
    ) -> None:
        """Create the device around a BLEDevice, with the stored lift calibration."""
        self._ble_device = ble_device
        self._client: BleakClientWithServiceCache | None = None
        self._started = False
        self._loop: asyncio.AbstractEventLoop | None = None
        self._connect_lock = asyncio.Lock()
        self._write_lock = asyncio.Lock()
        self._reconnect_task: asyncio.Task[None] | None = None
        self._name: str | None = None
        self._model: str | None = None
        self._fw_version: str | None = None
        self._state: BerbelState | None = None
        self._settings: BerbelSettings | None = None
        self._state_received = asyncio.Event()
        self._state_frame_count = 0
        self._settings_received = asyncio.Event()
        self._settings_frame_count = 0
        self._lift_top_raw = lift_top_raw
        self._lift_bottom_raw = lift_bottom_raw
        self._lift_stop_requested = False
        self._previous_lift_motion: int | None = None
        self._available = False
        self._state_callbacks: list[Callable[[BerbelState], None]] = []
        self._settings_callbacks: list[Callable[[BerbelSettings], None]] = []
        self._availability_callbacks: list[Callable[[bool], None]] = []
        self._calibration_callbacks: list[Callable[[int, int], None]] = []

    @property
    def address(self) -> str:
        """The Bluetooth address of the hood."""
        return self._ble_device.address

    @property
    def name(self) -> str | None:
        """The device name read from the hood, for example SKYLINE_EDGE."""
        return self._name

    @property
    def model(self) -> str | None:
        """The model number string from the Device Information service."""
        return self._model

    @property
    def fw_version(self) -> str | None:
        """The firmware revision string from the Device Information service."""
        return self._fw_version

    @property
    def state(self) -> BerbelState | None:
        """The last parsed main state frame, or None before the first frame arrived."""
        return self._state

    @property
    def settings(self) -> BerbelSettings | None:
        """The last parsed settings frame, or None before the first frame arrived."""
        return self._settings

    @property
    def available(self) -> bool:
        """True while the connection to the hood is up."""
        client = self._client
        return client is not None and client.is_connected

    @property
    def lift_top_raw(self) -> int:
        """The raw lift position value at the top end stop."""
        return self._lift_top_raw

    @property
    def lift_bottom_raw(self) -> int:
        """The raw lift position value at the bottom end stop."""
        return self._lift_bottom_raw

    def set_ble_device(self, ble_device: BLEDevice) -> None:
        """Replace the BLEDevice that the next connection attempt uses."""
        self._ble_device = ble_device

    def register_callback(
        self, callback: Callable[[BerbelState], None]
    ) -> Callable[[], None]:
        """Register a callback fired with every parsed main state frame."""
        return self._register(self._state_callbacks, callback)

    def register_settings_callback(
        self, callback: Callable[[BerbelSettings], None]
    ) -> Callable[[], None]:
        """Register a callback fired with every parsed settings frame."""
        return self._register(self._settings_callbacks, callback)

    def register_availability_callback(
        self, callback: Callable[[bool], None]
    ) -> Callable[[], None]:
        """Register a callback fired when the connection comes up or goes down."""
        return self._register(self._availability_callbacks, callback)

    def register_calibration_callback(
        self, callback: Callable[[int, int], None]
    ) -> Callable[[], None]:
        """Register a callback fired with (top_raw, bottom_raw) when an end stop moves."""
        return self._register(self._calibration_callbacks, callback)

    @staticmethod
    def _register(callbacks: list, callback) -> Callable[[], None]:
        callbacks.append(callback)

        def unsubscribe() -> None:
            if callback in callbacks:
                callbacks.remove(callback)

        return unsubscribe

    async def start(self) -> None:
        """Connect, read the device information and both frames, and subscribe."""
        self._started = True
        self._loop = asyncio.get_running_loop()
        await self._connect()

    async def stop(self) -> None:
        """Stop reconnecting, unsubscribe and disconnect."""
        self._started = False
        if self._reconnect_task is not None:
            self._reconnect_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._reconnect_task
            self._reconnect_task = None
        client = self._client
        self._client = None
        if client is not None and client.is_connected:
            with contextlib.suppress(Exception):
                await client.stop_notify(CHAR_MAIN_STATE)
                await client.stop_notify(CHAR_SETTINGS)
            with contextlib.suppress(Exception):
                await client.disconnect()
        self._set_available(False)

    async def set_down_light(self, brightness: int) -> None:
        """Set the down light brightness, 0 to 255. Zero switches the light off."""
        await self._write_main_frame(
            {STATE_OFFSET_DOWN_BRIGHTNESS: _clamp_byte(brightness)}
        )

    async def set_top_light(self, brightness: int) -> None:
        """Set the top light brightness, 0 to 255. Zero switches the light off."""
        await self._write_main_frame(
            {STATE_OFFSET_TOP_BRIGHTNESS: _clamp_byte(brightness)}
        )

    async def set_effect_color(
        self, rgb: tuple[int, int, int], brightness: int
    ) -> None:
        """Set the effect light to a color. The white-mode brightness goes to zero,
        because the active mode is the one whose brightness byte is nonzero."""
        red, green, blue = rgb
        await self._write_main_frame(
            {
                STATE_OFFSET_EFFECT_RED: _clamp_byte(red),
                STATE_OFFSET_EFFECT_GREEN: _clamp_byte(green),
                STATE_OFFSET_EFFECT_BLUE: _clamp_byte(blue),
                STATE_OFFSET_EFFECT_BRIGHTNESS: _clamp_byte(brightness),
                STATE_OFFSET_EFFECT_WHITE_BRIGHTNESS: 0,
            }
        )

    async def set_effect_white(self, brightness: int) -> None:
        """Set the effect light to white mode. The color-mode brightness goes to zero,
        because the active mode is the one whose brightness byte is nonzero."""
        await self._write_main_frame(
            {
                STATE_OFFSET_EFFECT_WHITE_BRIGHTNESS: _clamp_byte(brightness),
                STATE_OFFSET_EFFECT_BRIGHTNESS: 0,
            }
        )

    async def set_down_color_temp(self, value: int) -> None:
        """Set the down light color temperature byte. A higher value is warmer."""
        await self._write_settings_frame(
            {SETTINGS_OFFSET_DOWN_COLOR_TEMP: _clamp_byte(value)}
        )

    async def set_effect_color_temp(self, value: int) -> None:
        """Set the effect light white-mode color temperature byte. Higher is warmer."""
        await self._write_settings_frame(
            {SETTINGS_OFFSET_EFFECT_COLOR_TEMP: _clamp_byte(value)}
        )

    async def set_top_color_temp(self, value: int) -> None:
        """Set the top light color temperature byte. A higher value is warmer."""
        await self._write_settings_frame(
            {SETTINGS_OFFSET_TOP_COLOR_TEMP: _clamp_byte(value)}
        )

    async def set_fan_level(self, level: int) -> None:
        """Set the fan to level 1, 2 or 3."""
        if level not in FAN_LEVEL_COMMANDS:
            raise ValueError(f"fan level must be 1, 2 or 3, not {level}")
        await self._press(FAN_LEVEL_COMMANDS[level])

    async def set_fan_boost(self) -> None:
        """Set the fan to the intensive level P."""
        await self._press(COMMAND_FAN_BOOST)

    async def fan_run_on(self) -> None:
        """Press the off button once, which puts a running fan into delayed shutoff."""
        await self._press(COMMAND_FAN_OFF)

    async def fan_off(self) -> None:
        """Switch the fan hard off. The first press of the off button puts a running fan
        into delayed shutoff, so when a state frame newer than the press still reports
        run-on, the button is pressed once more."""
        newer_than = await self._press(COMMAND_FAN_OFF)
        arrived = await self._wait_for_frame(
            self._state_received,
            lambda: self._state_frame_count,
            newer_than,
            FAN_OFF_STATE_TIMEOUT_SECONDS,
        )
        if not arrived:
            return
        state = self._state
        if state is not None and state.fan_run_on:
            await self._press(COMMAND_FAN_OFF)

    async def lift_up(self) -> None:
        """Start the lift moving up. It runs to the top end stop on its own."""
        await self._press(COMMAND_LIFT_UP)

    async def lift_down(self) -> None:
        """Start the lift moving down. It runs to the bottom end stop on its own."""
        await self._press(COMMAND_LIFT_DOWN)

    async def lift_stop(self) -> None:
        """Stop a moving lift. Pressing the current direction of travel again stops the
        lift mid-travel, so the direction comes from the last state frame. A lift that is
        not moving is left alone."""
        state = self._state
        if state is None:
            return
        if state.is_lift_moving_up:
            code = COMMAND_LIFT_UP
        elif state.is_lift_moving_down:
            code = COMMAND_LIFT_DOWN
        else:
            return
        self._lift_stop_requested = True
        try:
            await self._press(code)
        except BaseException:
            # A press that never went out stops nothing, so the stop request is
            # withdrawn and the calibration tracking keeps treating the next stop the
            # lift makes on its own as an end stop.
            self._lift_stop_requested = False
            raise

    def lift_position_pct(self) -> int | None:
        """The lift position as a percentage: 100 fully up, 0 at the bottom end stop,
        clamped into that range. None before the first state frame or while the
        calibration span is empty."""
        state = self._state
        if state is None:
            return None
        span = self._lift_bottom_raw - self._lift_top_raw
        if span <= 0:
            return None
        percentage = round(
            (self._lift_bottom_raw - state.lift_position_raw) * 100 / span
        )
        return max(0, min(100, percentage))

    async def _connect(self) -> None:
        """Establish the connection, read the initial data and subscribe to frames."""
        async with self._connect_lock:
            if self._client is not None and self._client.is_connected:
                return
            client = await establish_connection(
                BleakClientWithServiceCache,
                self._ble_device,
                self._ble_device.name or self._ble_device.address,
                disconnected_callback=self._handle_disconnect,
            )
            try:
                await self._read_device_information(client)
                state_data = await client.read_gatt_char(CHAR_MAIN_STATE)
                self._handle_state_frame(bytes(state_data))
                settings_data = await client.read_gatt_char(CHAR_SETTINGS)
                self._handle_settings_frame(bytes(settings_data))
                await client.start_notify(CHAR_MAIN_STATE, self._on_state_indication)
                await client.start_notify(CHAR_SETTINGS, self._on_settings_indication)
            except BaseException:
                # The clause catches BaseException so that a cancelled setup also closes
                # the half-established connection before the cancellation travels on.
                with contextlib.suppress(Exception):
                    await client.disconnect()
                raise
            self._client = client
            self._set_available(True)

    async def _read_device_information(
        self, client: BleakClientWithServiceCache
    ) -> None:
        """Read the device name, the model number and the firmware revision."""
        self._name = await self._read_string(client, CHAR_DEVICE_INFO) or self._name
        self._model = await self._read_string(client, CHAR_MODEL_NUMBER) or self._model
        self._fw_version = (
            await self._read_string(client, CHAR_FIRMWARE_REVISION) or self._fw_version
        )

    @staticmethod
    async def _read_string(
        client: BleakClientWithServiceCache, characteristic_uuid: str
    ) -> str | None:
        """Read a characteristic as text, cut at the first zero byte."""
        try:
            data = await client.read_gatt_char(characteristic_uuid)
        except Exception:
            _LOGGER.debug("Could not read %s", characteristic_uuid, exc_info=True)
            return None
        text = bytes(data).split(b"\x00", 1)[0].decode("ascii", errors="replace")
        return text.strip() or None

    def _handle_disconnect(self, client: BleakClientWithServiceCache) -> None:
        """Handle a dropped connection by reporting it and scheduling a reconnect. A
        drop of any connection other than the current one changes nothing."""
        if client is not self._client:
            return
        self._client = None
        self._set_available(False)
        if self._started and self._loop is not None:
            self._loop.call_soon_threadsafe(self._schedule_reconnect)

    def _schedule_reconnect(self) -> None:
        """Start the reconnect loop unless one is already running."""
        if not self._started:
            return
        if self._reconnect_task is not None and not self._reconnect_task.done():
            return
        assert self._loop is not None
        self._reconnect_task = self._loop.create_task(self._reconnect_loop())

    async def _reconnect_loop(self) -> None:
        """Reconnect with exponential backoff, from one second up to one minute."""
        delay = RECONNECT_BACKOFF_BASE_SECONDS
        while self._started:
            try:
                await self._connect()
                return
            except Exception:
                _LOGGER.debug(
                    "Reconnect to %s failed, next attempt in %.0f s",
                    self.address,
                    delay,
                    exc_info=True,
                )
            await asyncio.sleep(delay)
            delay = min(delay * 2, RECONNECT_BACKOFF_CAP_SECONDS)

    def _on_state_indication(
        self, _characteristic: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        self._handle_state_frame(bytes(data))

    def _on_settings_indication(
        self, _characteristic: BleakGATTCharacteristic, data: bytearray
    ) -> None:
        self._handle_settings_frame(bytes(data))

    def _handle_state_frame(self, data: bytes) -> None:
        """Parse a main state frame, track calibration and fire the state callbacks."""
        try:
            state = BerbelState.parse(data)
        except ValueError:
            _LOGGER.debug("Dropping short main state frame: %s", data.hex())
            return
        self._track_lift_calibration(state)
        self._state = state
        self._state_frame_count += 1
        self._state_received.set()
        for callback in list(self._state_callbacks):
            callback(state)

    def _handle_settings_frame(self, data: bytes) -> None:
        """Parse a settings frame and fire the settings callbacks."""
        try:
            settings = BerbelSettings.parse(data)
        except ValueError:
            _LOGGER.debug("Dropping short settings frame: %s", data.hex())
            return
        self._settings = settings
        self._settings_frame_count += 1
        self._settings_received.set()
        for callback in list(self._settings_callbacks):
            callback(settings)

    def _track_lift_calibration(self, state: BerbelState) -> None:
        """Update the end-stop calibration from an observed frame. Idle at the top gives
        the top value. A downward run that stops on its own, rather than through a
        requested stop, ends at the bottom end stop and gives the bottom value. The
        calibration callbacks fire when either value changes."""
        previous = self._previous_lift_motion
        self._previous_lift_motion = state.lift_motion
        top = self._lift_top_raw
        bottom = self._lift_bottom_raw
        if state.lift_motion == LiftMotion.IDLE_TOP:
            top = state.lift_position_raw
        if previous in _LIFT_MOVING_STATES and state.lift_motion not in _LIFT_MOVING_STATES:
            stop_requested = self._lift_stop_requested
            self._lift_stop_requested = False
            if (
                previous in _LIFT_MOVING_DOWN_STATES
                and state.lift_motion == LiftMotion.STOPPED
                and not stop_requested
            ):
                bottom = state.lift_position_raw
        if (top, bottom) != (self._lift_top_raw, self._lift_bottom_raw):
            self._lift_top_raw = top
            self._lift_bottom_raw = bottom
            for callback in list(self._calibration_callbacks):
                callback(top, bottom)

    def _set_available(self, available: bool) -> None:
        """Record the connection state and fire the availability callbacks on a change."""
        if available == self._available:
            return
        self._available = available
        for callback in list(self._availability_callbacks):
            callback(available)

    def _require_client(self) -> BleakClientWithServiceCache:
        """The connected client, or a RuntimeError when the connection is down."""
        client = self._client
        if client is None or not client.is_connected:
            raise RuntimeError(f"not connected to {self.address}")
        return client

    async def _press(self, code: int) -> int:
        """Send one short button press: the command code, then the release fifty
        milliseconds later. The hood confirms each write with an indication. Returns the
        number of main state frames that had arrived when the press was sent, read under
        the write lock just before the command write."""
        client = self._require_client()
        async with self._write_lock:
            count_before_press = self._state_frame_count
            await client.write_gatt_char(
                CHAR_COMMAND, bytes([0x00, code]), response=True
            )
            await asyncio.sleep(PRESS_RELEASE_GAP_SECONDS)
            await client.write_gatt_char(
                CHAR_COMMAND, bytes([0x00, COMMAND_RELEASE]), response=True
            )
        return count_before_press

    @staticmethod
    async def _wait_for_frame(
        received: asyncio.Event,
        frame_count: Callable[[], int],
        newer_than: int,
        timeout_seconds: float,
    ) -> bool:
        """Wait until the given frame counter passes the given value, that is until a
        frame arrived after the counter was read. Returns False on timeout. Every caller
        compares against its own counter reading, so several waiters can share the
        event."""
        if frame_count() > newer_than:
            return True
        received.clear()
        try:
            await asyncio.wait_for(received.wait(), timeout_seconds)
        except TimeoutError:
            pass
        return frame_count() > newer_than

    async def _write_main_frame(self, changes: dict[int, int]) -> None:
        """Write the last main state frame back with the given byte changes, so every
        byte the library does not know about round-trips unchanged. The frame snapshot
        and the write happen under the write lock, and the lock is held until the
        confirming indication has refreshed the stored frame, so each writer starts from
        the bytes the previous write left on the hood."""
        async with self._write_lock:
            state = self._state
            if state is None:
                raise RuntimeError("no main state frame received yet")
            frame = bytearray(state.raw)
            for offset, value in changes.items():
                frame[offset] = value
            client = self._require_client()
            newer_than = self._state_frame_count
            await client.write_gatt_char(CHAR_MAIN_STATE, bytes(frame), response=True)
            confirmed = await self._wait_for_frame(
                self._state_received,
                lambda: self._state_frame_count,
                newer_than,
                _FRAME_CONFIRM_TIMEOUT_SECONDS,
            )
            if not confirmed:
                _LOGGER.debug(
                    "No confirming main state indication from %s within %.0f s",
                    self.address,
                    _FRAME_CONFIRM_TIMEOUT_SECONDS,
                )

    async def _write_settings_frame(self, changes: dict[int, int]) -> None:
        """Write the last settings frame back with the given byte changes, so every byte
        the library does not know about round-trips unchanged. The frame snapshot and
        the write happen under the write lock, and the lock is held until the confirming
        indication has refreshed the stored frame, so each writer starts from the bytes
        the previous write left on the hood."""
        async with self._write_lock:
            settings = self._settings
            if settings is None:
                raise RuntimeError("no settings frame received yet")
            frame = bytearray(settings.raw)
            for offset, value in changes.items():
                frame[offset] = value
            client = self._require_client()
            newer_than = self._settings_frame_count
            await client.write_gatt_char(CHAR_SETTINGS, bytes(frame), response=True)
            confirmed = await self._wait_for_frame(
                self._settings_received,
                lambda: self._settings_frame_count,
                newer_than,
                _FRAME_CONFIRM_TIMEOUT_SECONDS,
            )
            if not confirmed:
                _LOGGER.debug(
                    "No confirming settings indication from %s within %.0f s",
                    self.address,
                    _FRAME_CONFIRM_TIMEOUT_SECONDS,
                )
