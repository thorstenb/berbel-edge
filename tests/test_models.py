"""Parser tests fed with frames captured from a real Berbel Skyline extractor hood.

Note: did not manage to get certainty on exact protocol behaviour
during lift move. Therefore, the motion-state tests make assumptions,
take the real mid-travel frame and set the motion byte to each moving
value the protocol defines.

"""

import pytest

from berbel_ble import BerbelSettings, BerbelState, LiftMotion


def frame(hex_text: str) -> bytes:
    """Turn a colon-separated hex string from berbel-info.md into bytes."""
    return bytes.fromhex(hex_text.replace(":", ""))


# Main state frames (f006f006, 31 bytes) from the dumps in berbel-info.md.
FRAME_FAN_LEVEL_2 = frame(
    "01:4f:00:00:00:00:00:00:05:00:ff:4e:00:00:00:00:02:00:01:"
    "00:00:00:00:00:00:00:00:00:00:00:00"
)
FRAME_DOWN_FULL = frame(
    "01:4f:00:00:ff:00:00:00:05:00:ff:4e:00:ff:00:00:02:00:01:"
    "00:00:00:00:00:00:00:00:00:00:00:00"
)
FRAME_TOP_FULL = frame(
    "01:4f:00:00:00:00:ff:00:05:00:ff:4e:00:00:00:00:02:00:01:"
    "00:00:00:00:00:00:00:00:00:00:00:00"
)
FRAME_FAN_BOOST = frame(
    "01:4f:00:00:00:00:ff:00:05:00:ff:4e:00:00:00:00:04:00:01:"
    "00:00:00:00:00:00:00:00:00:00:00:00"
)
FRAME_FAN_RUN_ON = frame(
    "01:4f:00:00:00:00:ff:00:05:00:ff:4e:00:00:00:00:01:01:01:"
    "00:00:00:00:00:00:00:00:00:00:00:00"
)
FRAME_EFFECT_PINK = frame(
    "01:4f:00:00:00:00:00:00:05:a8:00:ff:00:ff:00:00:00:00:01:"
    "00:00:00:00:00:00:00:00:00:00:00:00"
)
FRAME_EFFECT_WHITE_MODE = frame(
    "01:4f:00:00:00:ff:00:00:05:5c:ff:60:00:4f:00:00:00:00:01:"
    "00:00:00:00:00:00:00:00:00:00:00:00"
)
FRAME_ALL_OFF = frame(
    "01:4f:00:00:00:00:00:00:05:00:ff:71:00:00:00:00:00:00:01:"
    "00:00:00:00:00:00:00:00:00:00:00:00"
)
FRAME_STOPPED_MID_TRAVEL = frame(
    "02:83:00:00:a8:00:00:00:05:5c:ff:60:00:ff:00:00:00:00:01:"
    "00:00:00:00:00:00:00:00:00:00:00:00"
)

# Settings frames (f006f007, 26 bytes) from the dumps: color
# temperature changes on the down light (byte 6), the effect light in
# white mode (byte 7) and the top light (byte 8).
SETTINGS_DOWN_COLD = frame(
    "4f:90:00:00:00:00:1a:ff:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
)
SETTINGS_DOWN_WARM = frame(
    "4f:90:00:00:00:00:d6:ff:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
)
SETTINGS_EFFECT_COLD = frame(
    "4f:90:00:00:00:00:cd:25:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
)
SETTINGS_TOP_WARM = frame(
    "4f:90:00:00:00:00:cd:c7:cf:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
)


def moving_frame(motion: int, position: int) -> bytes:
    """A main state frame with the given motion byte and raw position.

    The rest of the frame is the real mid-travel capture, so every
    other field keeps a value the hood actually sent.

    """
    data = bytearray(FRAME_STOPPED_MID_TRAVEL)
    data[0] = motion
    data[1] = position
    return bytes(data)


def test_fan_level_frame_parses_every_field():
    state = BerbelState.parse(FRAME_FAN_LEVEL_2)
    assert state.raw == FRAME_FAN_LEVEL_2
    assert state.lift_motion == LiftMotion.IDLE_TOP
    assert state.lift_position_raw == 0x4F
    assert state.down_brightness == 0
    assert state.effect_white_brightness == 0
    assert state.top_brightness == 0
    assert state.effect_rgb == (0x00, 0xFF, 0x4E)
    assert state.effect_brightness == 0
    assert state.fan_level == 2
    assert state.fan_run_on is False
    assert state.is_lift_moving_up is False
    assert state.is_lift_moving_down is False


def test_down_light_frame_reports_full_brightness():
    state = BerbelState.parse(FRAME_DOWN_FULL)
    assert state.down_brightness == 0xFF
    assert state.top_brightness == 0
    assert state.effect_brightness == 0xFF
    assert state.fan_level == 2


def test_top_light_frame_reports_full_brightness():
    state = BerbelState.parse(FRAME_TOP_FULL)
    assert state.top_brightness == 0xFF
    assert state.down_brightness == 0
    assert state.fan_level == 2


def test_fan_boost_frame_reports_level_four():
    state = BerbelState.parse(FRAME_FAN_BOOST)
    assert state.fan_level == 4
    assert state.fan_run_on is False


def test_fan_run_on_frame_reports_delayed_shutoff():
    state = BerbelState.parse(FRAME_FAN_RUN_ON)
    assert state.fan_level == 1
    assert state.fan_run_on is True


def test_effect_color_frame_reports_color_and_brightness():
    state = BerbelState.parse(FRAME_EFFECT_PINK)
    assert state.effect_rgb == (0xA8, 0x00, 0xFF)
    assert state.effect_brightness == 0xFF
    assert state.effect_white_brightness == 0
    assert state.fan_level == 0


def test_effect_white_mode_frame_reports_white_brightness():
    state = BerbelState.parse(FRAME_EFFECT_WHITE_MODE)
    assert state.effect_white_brightness == 0xFF
    assert state.effect_brightness == 0x4F
    assert state.effect_rgb == (0x5C, 0xFF, 0x60)


def test_all_off_frame_reports_every_light_and_the_fan_off():
    state = BerbelState.parse(FRAME_ALL_OFF)
    assert state.down_brightness == 0
    assert state.effect_white_brightness == 0
    assert state.top_brightness == 0
    assert state.effect_brightness == 0
    assert state.fan_level == 0
    assert state.fan_run_on is False


def test_stopped_mid_travel_frame_reports_position_between_the_end_stops():
    state = BerbelState.parse(FRAME_STOPPED_MID_TRAVEL)
    assert state.lift_motion == LiftMotion.STOPPED
    assert state.lift_position_raw == 0x83
    assert 0x4F < state.lift_position_raw < 0x91
    assert state.is_lift_moving_up is False
    assert state.is_lift_moving_down is False


@pytest.mark.parametrize(
    ("motion", "position", "moving_up", "moving_down"),
    [
        (LiftMotion.MOVING_UP, 0x7A, True, False),
        (LiftMotion.MOVING_DOWN, 0x7A, False, True),
        (LiftMotion.MOVING_UP_END, 0x52, True, False),
        (LiftMotion.MOVING_DOWN_END, 0x8E, False, True),
    ],
)
def test_motion_states_during_movement(motion, position, moving_up, moving_down):
    state = BerbelState.parse(moving_frame(motion, position))
    assert state.lift_motion == motion
    assert state.lift_position_raw == position
    assert state.is_lift_moving_up is moving_up
    assert state.is_lift_moving_down is moving_down


def test_lift_motion_enum_matches_the_protocol_values():
    assert LiftMotion.IDLE_TOP == 1
    assert LiftMotion.STOPPED == 2
    assert LiftMotion.MOVING_UP == 3
    assert LiftMotion.MOVING_DOWN == 4
    assert LiftMotion.MOVING_UP_END == 5
    assert LiftMotion.MOVING_DOWN_END == 6


def test_state_parse_rejects_a_short_frame():
    with pytest.raises(ValueError):
        BerbelState.parse(FRAME_FAN_LEVEL_2[:19])


def test_state_parse_accepts_the_minimum_length():
    state = BerbelState.parse(FRAME_FAN_LEVEL_2[:20])
    assert state.fan_level == 2
    assert state.fan_run_on is False


@pytest.mark.parametrize(
    ("data", "down", "effect", "top"),
    [
        (SETTINGS_DOWN_COLD, 0x1A, 0xFF, 0x23),
        (SETTINGS_DOWN_WARM, 0xD6, 0xFF, 0x23),
        (SETTINGS_EFFECT_COLD, 0xCD, 0x25, 0x23),
        (SETTINGS_TOP_WARM, 0xCD, 0xC7, 0xCF),
    ],
)
def test_settings_frames_report_the_three_color_temperatures(data, down, effect, top):
    settings = BerbelSettings.parse(data)
    assert settings.raw == data
    assert settings.down_color_temp == down
    assert settings.effect_color_temp == effect
    assert settings.top_color_temp == top


def test_settings_parse_rejects_a_short_frame():
    with pytest.raises(ValueError):
        BerbelSettings.parse(SETTINGS_DOWN_COLD[:8])


def test_settings_parse_accepts_the_minimum_length():
    settings = BerbelSettings.parse(SETTINGS_DOWN_COLD[:9])
    assert settings.top_color_temp == 0x23
