"""BerbelDevice tests that run without a radio.

The tests inject captured frames through the indication handlers and
check:
 - the state tracking
 - the lift calibration
 - the position percentage
 - the callback plumbing
 - the command button press thingits for the fan and the lift
 - and the read-modify-write frame helpers for the lights and the
   color temperatures.

The Bluetooth client is a small mockup that records writes. The Kelvin
mapping helpers from the integration constants are tested here too,
loaded straight from their source file because they have no Home
Assistant dependencies.

"""

import asyncio
import importlib.util
from pathlib import Path

import pytest
from berbel_ble import BerbelDevice, LiftMotion
from berbel_ble.const import (
    CHAR_COMMAND,
    CHAR_MAIN_STATE,
    CHAR_SETTINGS,
    COMMAND_FAN_BOOST,
    COMMAND_FAN_LEVEL_1,
    COMMAND_FAN_LEVEL_2,
    COMMAND_FAN_LEVEL_3,
    COMMAND_FAN_OFF,
    COMMAND_LIFT_DOWN,
    COMMAND_LIFT_UP,
    COMMAND_RELEASE,
    SETTINGS_OFFSET_DOWN_COLOR_TEMP,
    SETTINGS_OFFSET_EFFECT_COLOR_TEMP,
    SETTINGS_OFFSET_TOP_COLOR_TEMP,
    STATE_OFFSET_DOWN_BRIGHTNESS,
    STATE_OFFSET_EFFECT_BLUE,
    STATE_OFFSET_EFFECT_BRIGHTNESS,
    STATE_OFFSET_EFFECT_GREEN,
    STATE_OFFSET_EFFECT_RED,
    STATE_OFFSET_EFFECT_WHITE_BRIGHTNESS,
    STATE_OFFSET_FAN_RUN_ON,
    STATE_OFFSET_TOP_BRIGHTNESS,
)

# hack to load Kelvin mapping helpers
_INTEGRATION_CONST_SPEC = importlib.util.spec_from_file_location(
    "berbel_integration_const",
    Path(__file__).resolve().parent.parent / "custom_components" / "berbel" / "const.py",
)
integration_const = importlib.util.module_from_spec(_INTEGRATION_CONST_SPEC)
_INTEGRATION_CONST_SPEC.loader.exec_module(integration_const)

ADDRESS = "9C:9E:FF:FF:FF:FF"

# Some real-world mid-travel capture from berbel-info.md
FRAME_TEMPLATE = bytes.fromhex(
    "02:83:00:00:a8:00:00:00:05:5c:ff:60:00:ff:00:00:00:00:01:"
    "00:00:00:00:00:00:00:00:00:00:00:00".replace(":", "")
)


class FakeBLEDevice:
    """The two attributes of a BLEDevice that BerbelDevice reads."""

    def __init__(self) -> None:
        self.address = ADDRESS
        self.name = "SKE_P"


class FakeClient:
    """A connected Bluetooth client that records every GATT write. Use respond
    callbacks to simulate Berbel device answers."""

    def __init__(self) -> None:
        self.is_connected = True
        self.writes: list[tuple[str, bytes]] = []
        self.respond = None

    async def write_gatt_char(self, characteristic, data, response=False):
        self.writes.append((characteristic, bytes(data)))
        if self.respond is not None:
            self.respond(characteristic, bytes(data))


def make_device(**kwargs) -> BerbelDevice:
    return BerbelDevice(FakeBLEDevice(), **kwargs)


def connected_device(echo_frames: bool = False) -> tuple[BerbelDevice, FakeClient]:
    """A device with a fake connected client, so the write helpers can
    run. With echo_frames, every frame write comes straight back as an
    indication carrying the written bytes, which is how the hood
    confirms a frame write.

    """
    device = make_device()
    client = FakeClient()
    device._client = client
    if echo_frames:

        def respond(characteristic: str, data: bytes) -> None:
            if characteristic == CHAR_MAIN_STATE:
                inject(device, data)
            elif characteristic == CHAR_SETTINGS:
                inject_settings(device, data)

        client.respond = respond
    return device, client


def frame_with(original: bytes, changes: dict[int, int]) -> bytes:
    """The original frame with the given byte changes applied."""
    data = bytearray(original)
    for offset, value in changes.items():
        data[offset] = value
    return bytes(data)


def frame(motion: int, position: int, changes: dict[int, int] | None = None) -> bytes:
    return frame_with(FRAME_TEMPLATE, {0: motion, 1: position, **(changes or {})})


def inject(device: BerbelDevice, data: bytes) -> None:
    """Deliver a main state frame the way a Bluetooth indication would."""
    device._on_state_indication(None, bytearray(data))


def inject_settings(device: BerbelDevice, data: bytes) -> None:
    """Deliver a settings frame the way a Bluetooth indication would."""
    device._on_settings_indication(None, bytearray(data))


def press_writes(*codes: int) -> list[tuple[str, bytes]]:
    """The GATT writes a sequence of button presses: each command code is
    written to the command characteristic - followed by a release command."""
    writes = []
    for code in codes:
        writes.append((CHAR_COMMAND, bytes([0x00, code])))
        writes.append((CHAR_COMMAND, bytes([0x00, COMMAND_RELEASE])))
    return writes


async def deliver_state_after_press(
    device: BerbelDevice, client: FakeClient, data: bytes
) -> None:
    """Wait until one press and release pair has been written, then deliver the frame."""
    for _ in range(400):
        if len(client.writes) >= 2:
            break
        await asyncio.sleep(0.005)
    inject(device, data)


# A real settings frame from the capture, with the down light set to a cold temperature.
SETTINGS_FRAME = bytes.fromhex(
    "4f:90:00:00:00:00:1a:ff:23:00:00:00:00:00:00:00:00:01:"
    "00:00:00:00:00:00:00:00".replace(":", "")
)


def test_state_updates_with_every_indication():
    device = make_device()
    assert device.state is None
    inject(device, frame(LiftMotion.IDLE_TOP, 0x4F))
    assert device.state is not None
    assert device.state.lift_position_raw == 0x4F
    inject(device, frame(LiftMotion.STOPPED, 0x83))
    assert device.state.lift_position_raw == 0x83


def test_short_state_frame_is_dropped():
    device = make_device()
    inject(device, frame(LiftMotion.IDLE_TOP, 0x4F))
    before = device.state
    inject(device, frame(LiftMotion.STOPPED, 0x83)[:19])
    assert device.state is before


def test_state_callback_fires_until_unsubscribed():
    device = make_device()
    seen = []
    unsubscribe = device.register_callback(seen.append)
    inject(device, frame(LiftMotion.IDLE_TOP, 0x4F))
    assert len(seen) == 1
    assert seen[0].lift_motion == LiftMotion.IDLE_TOP
    unsubscribe()
    inject(device, frame(LiftMotion.STOPPED, 0x83))
    assert len(seen) == 1
    unsubscribe()


def test_settings_callback_fires_until_unsubscribed():
    device = make_device()
    seen = []
    unsubscribe = device.register_settings_callback(seen.append)
    inject_settings(device, SETTINGS_FRAME)
    assert len(seen) == 1
    assert seen[0].down_color_temp == 0x1A
    assert device.settings is seen[0]
    unsubscribe()
    inject_settings(device, SETTINGS_FRAME)
    assert len(seen) == 1


def test_default_calibration_matches_the_reference_installation():
    device = make_device()
    assert device.lift_top_raw == 0x0F
    assert device.lift_bottom_raw == 0xE0


def test_idle_at_top_records_the_top_end_stop():
    device = make_device(lift_top_raw=0x4F, lift_bottom_raw=0x91)
    seen = []
    device.register_calibration_callback(lambda top, bottom: seen.append((top, bottom)))
    inject(device, frame(LiftMotion.IDLE_TOP, 0x52))
    assert device.lift_top_raw == 0x52
    assert device.lift_bottom_raw == 0x91
    assert seen == [(0x52, 0x91)]


def test_idle_at_top_with_the_known_value_fires_no_callback():
    device = make_device(lift_top_raw=0x4F, lift_bottom_raw=0x91)
    seen = []
    device.register_calibration_callback(lambda top, bottom: seen.append((top, bottom)))
    inject(device, frame(LiftMotion.IDLE_TOP, 0x4F))
    assert seen == []


def test_down_run_that_stops_on_its_own_records_the_bottom_end_stop():
    device = make_device(lift_top_raw=0x4F, lift_bottom_raw=0x91)
    seen = []
    device.register_calibration_callback(lambda top, bottom: seen.append((top, bottom)))
    inject(device, frame(LiftMotion.MOVING_DOWN, 0x80))
    inject(device, frame(LiftMotion.MOVING_DOWN_END, 0x8C))
    inject(device, frame(LiftMotion.STOPPED, 0x8F))
    assert device.lift_bottom_raw == 0x8F
    assert seen == [(0x4F, 0x8F)]
    # Reaching the same end stop again changes nothing, so no further callback fires.
    inject(device, frame(LiftMotion.MOVING_DOWN, 0x80))
    inject(device, frame(LiftMotion.STOPPED, 0x8F))
    assert seen == [(0x4F, 0x8F)]


def test_requested_stop_records_no_bottom_end_stop():
    device = make_device(lift_top_raw=0x4F, lift_bottom_raw=0x91)
    device._client = FakeClient()
    seen = []
    device.register_calibration_callback(lambda top, bottom: seen.append((top, bottom)))
    inject(device, frame(LiftMotion.MOVING_DOWN, 0x7A))
    asyncio.run(device.lift_stop())
    inject(device, frame(LiftMotion.STOPPED, 0x7C))
    assert device.lift_bottom_raw == 0x91
    assert seen == []


def test_up_run_that_stops_records_no_bottom_end_stop():
    device = make_device(lift_top_raw=0x4F, lift_bottom_raw=0x91)
    inject(device, frame(LiftMotion.MOVING_UP, 0x7A))
    inject(device, frame(LiftMotion.STOPPED, 0x78))
    assert device.lift_bottom_raw == 0x91


def test_lift_stop_presses_the_direction_of_travel():
    device, client = connected_device()
    inject(device, frame(LiftMotion.MOVING_DOWN, 0x7A))
    asyncio.run(device.lift_stop())
    assert client.writes == press_writes(COMMAND_LIFT_DOWN)


def test_lift_stop_leaves_an_idle_lift_alone():
    device, client = connected_device()
    inject(device, frame(LiftMotion.IDLE_TOP, 0x4F))
    asyncio.run(device.lift_stop())
    assert client.writes == []


def test_lift_up_and_lift_down_press_their_direction_commands():
    device, client = connected_device()
    asyncio.run(device.lift_up())
    asyncio.run(device.lift_down())
    assert client.writes == press_writes(COMMAND_LIFT_UP, COMMAND_LIFT_DOWN)


def test_lift_position_is_none_before_the_first_frame():
    device = make_device()
    assert device.lift_position_pct() is None


def test_lift_position_spans_the_calibrated_range():
    device = make_device(lift_top_raw=0x4F, lift_bottom_raw=0x91)
    inject(device, frame(LiftMotion.IDLE_TOP, 0x4F))
    assert device.lift_position_pct() == 100
    inject(device, frame(LiftMotion.STOPPED, 0x91))
    assert device.lift_position_pct() == 0
    inject(device, frame(LiftMotion.STOPPED, 0x83))
    # (0x91 - 0x83) * 100 / (0x91 - 0x4f) is roughly 21%.
    assert device.lift_position_pct() == 21


def test_lift_position_is_clamped_outside_the_calibrated_range():
    device = make_device(lift_top_raw=0x4F, lift_bottom_raw=0x91)
    inject(device, frame(LiftMotion.STOPPED, 0x20))
    assert device.lift_position_pct() == 100
    inject(device, frame(LiftMotion.STOPPED, 0xA0))
    assert device.lift_position_pct() == 0


def test_lift_position_is_none_while_the_calibration_span_is_empty():
    device = make_device(lift_top_raw=0x60, lift_bottom_raw=0x60)
    inject(device, frame(LiftMotion.STOPPED, 0x60))
    assert device.lift_position_pct() is None


def test_availability_callback_fires_until_unsubscribed():
    device = make_device()
    seen = []
    unsubscribe = device.register_availability_callback(seen.append)
    assert device.available is False
    device._set_available(True)
    assert seen == [True]
    unsubscribe()
    device._set_available(False)
    assert seen == [True]


def test_set_fan_level_maps_levels_one_to_three_onto_the_fan_commands():
    device, client = connected_device()

    async def run() -> None:
        for level in (1, 2, 3):
            await device.set_fan_level(level)

    asyncio.run(run())
    assert client.writes == press_writes(
        COMMAND_FAN_LEVEL_1, COMMAND_FAN_LEVEL_2, COMMAND_FAN_LEVEL_3
    )


def test_set_fan_level_rejects_levels_the_hood_does_not_have():
    device, client = connected_device()
    for level in (0, 4, -1):
        with pytest.raises(ValueError):
            asyncio.run(device.set_fan_level(level))
    assert client.writes == []


def test_set_fan_boost_presses_the_intensive_level_command():
    device, client = connected_device()
    asyncio.run(device.set_fan_boost())
    assert client.writes == press_writes(COMMAND_FAN_BOOST)


def test_fan_run_on_presses_the_off_button_once():
    device, client = connected_device()
    asyncio.run(device.fan_run_on())
    assert client.writes == press_writes(COMMAND_FAN_OFF)


def test_fan_off_presses_once_when_the_next_frame_shows_the_fan_off():
    device, client = connected_device()

    async def run() -> None:
        task = asyncio.create_task(device.fan_off())
        await deliver_state_after_press(
            device, client, frame(LiftMotion.IDLE_TOP, 0x4F)
        )
        await task

    asyncio.run(run())
    assert client.writes == press_writes(COMMAND_FAN_OFF)


def test_fan_off_presses_again_when_the_next_frame_still_shows_run_on():
    device, client = connected_device()

    async def run() -> None:
        task = asyncio.create_task(device.fan_off())
        await deliver_state_after_press(
            device,
            client,
            frame(LiftMotion.IDLE_TOP, 0x4F, {STATE_OFFSET_FAN_RUN_ON: 0x01}),
        )
        await task

    asyncio.run(run())
    assert client.writes == press_writes(COMMAND_FAN_OFF, COMMAND_FAN_OFF)


def test_fan_off_presses_once_when_no_frame_arrives_within_the_timeout(monkeypatch):
    monkeypatch.setattr("berbel_ble.device.FAN_OFF_STATE_TIMEOUT_SECONDS", 0.05)
    device, client = connected_device()
    asyncio.run(device.fan_off())
    assert client.writes == press_writes(COMMAND_FAN_OFF)


def test_set_down_light_changes_the_brightness_and_round_trips_the_rest():
    device, client = connected_device(echo_frames=True)
    last = frame(LiftMotion.IDLE_TOP, 0x4F)
    inject(device, last)
    asyncio.run(device.set_down_light(0x80))
    assert client.writes == [
        (CHAR_MAIN_STATE, frame_with(last, {STATE_OFFSET_DOWN_BRIGHTNESS: 0x80}))
    ]


def test_set_top_light_changes_the_brightness_and_round_trips_the_rest():
    device, client = connected_device(echo_frames=True)
    last = frame(LiftMotion.IDLE_TOP, 0x4F)
    inject(device, last)
    asyncio.run(device.set_top_light(0x40))
    assert client.writes == [
        (CHAR_MAIN_STATE, frame_with(last, {STATE_OFFSET_TOP_BRIGHTNESS: 0x40}))
    ]


def test_set_effect_color_sets_the_color_bytes_and_switches_white_mode_off():
    device, client = connected_device(echo_frames=True)
    # Start from a frame with the white mode on, so the write for sure switches it off.
    last = frame(
        LiftMotion.IDLE_TOP, 0x4F, {STATE_OFFSET_EFFECT_WHITE_BRIGHTNESS: 0x99}
    )
    inject(device, last)
    asyncio.run(device.set_effect_color((0x11, 0x22, 0x33), 0x44))
    assert client.writes == [
        (
            CHAR_MAIN_STATE,
            frame_with(
                last,
                {
                    STATE_OFFSET_EFFECT_RED: 0x11,
                    STATE_OFFSET_EFFECT_GREEN: 0x22,
                    STATE_OFFSET_EFFECT_BLUE: 0x33,
                    STATE_OFFSET_EFFECT_BRIGHTNESS: 0x44,
                    STATE_OFFSET_EFFECT_WHITE_BRIGHTNESS: 0x00,
                },
            ),
        )
    ]


def test_set_effect_white_sets_the_brightness_and_switches_color_mode_off():
    device, client = connected_device(echo_frames=True)
    # The template frame has the color mode on, so the write for sure switches it off.
    last = frame(LiftMotion.IDLE_TOP, 0x4F)
    inject(device, last)
    asyncio.run(device.set_effect_white(0x55))
    assert client.writes == [
        (
            CHAR_MAIN_STATE,
            frame_with(
                last,
                {
                    STATE_OFFSET_EFFECT_WHITE_BRIGHTNESS: 0x55,
                    STATE_OFFSET_EFFECT_BRIGHTNESS: 0x00,
                },
            ),
        )
    ]


def test_each_color_temp_setter_changes_only_its_own_settings_byte():
    device, client = connected_device(echo_frames=True)
    inject_settings(device, SETTINGS_FRAME)
    asyncio.run(device.set_down_color_temp(0x20))
    asyncio.run(device.set_effect_color_temp(0x40))
    asyncio.run(device.set_top_color_temp(0x60))
    # Each write starts from the frame the previous write has
    # imprinted on the hood. Modified bytes accumulate, and everything
    # else round-trips unchanged.
    first = frame_with(SETTINGS_FRAME, {SETTINGS_OFFSET_DOWN_COLOR_TEMP: 0x20})
    second = frame_with(first, {SETTINGS_OFFSET_EFFECT_COLOR_TEMP: 0x40})
    third = frame_with(second, {SETTINGS_OFFSET_TOP_COLOR_TEMP: 0x60})
    assert client.writes == [
        (CHAR_SETTINGS, first),
        (CHAR_SETTINGS, second),
        (CHAR_SETTINGS, third),
    ]


def test_kelvin_byte_mapping_spans_the_full_scale_with_warmer_as_higher():
    assert integration_const.kelvin_to_byte(integration_const.MAX_KELVIN) == 0
    assert integration_const.kelvin_to_byte(integration_const.MIN_KELVIN) == 255
    assert integration_const.byte_to_kelvin(0) == integration_const.MAX_KELVIN
    assert integration_const.byte_to_kelvin(255) == integration_const.MIN_KELVIN
    # A warmer (lower Kelvin) light leads to higher byte value.
    assert integration_const.kelvin_to_byte(3000) > integration_const.kelvin_to_byte(6000)


def test_kelvin_values_outside_the_supported_range_are_clamped():
    assert integration_const.kelvin_to_byte(10000) == 0
    assert integration_const.kelvin_to_byte(1000) == 255


def test_color_temp_bytes_round_trip_through_kelvin_unchanged():
    for byte in (0, 1, 64, 128, 191, 254, 255):
        kelvin = integration_const.byte_to_kelvin(byte)
        assert integration_const.kelvin_to_byte(kelvin) == byte
