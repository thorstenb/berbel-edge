"""Parsed views of the Berbel Skyline state and settings frames.

Both dataclasses keep the raw frame they were parsed from, so a write
helper can change a few bytes and send the frame back with every
unknown byte unmodified.

"""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum

from .const import (
    MIN_MAIN_STATE_LENGTH,
    MIN_SETTINGS_LENGTH,
    SETTINGS_OFFSET_DOWN_COLOR_TEMP,
    SETTINGS_OFFSET_EFFECT_COLOR_TEMP,
    SETTINGS_OFFSET_TOP_COLOR_TEMP,
    STATE_OFFSET_DOWN_BRIGHTNESS,
    STATE_OFFSET_EFFECT_BLUE,
    STATE_OFFSET_EFFECT_BRIGHTNESS,
    STATE_OFFSET_EFFECT_GREEN,
    STATE_OFFSET_EFFECT_RED,
    STATE_OFFSET_EFFECT_WHITE_BRIGHTNESS,
    STATE_OFFSET_FAN_LEVEL,
    STATE_OFFSET_FAN_RUN_ON,
    STATE_OFFSET_LIFT_MOTION,
    STATE_OFFSET_LIFT_POSITION,
    STATE_OFFSET_TOP_BRIGHTNESS,
)


class LiftMotion(IntEnum):
    """Lift motion states reported in byte 0 of the main state frame."""

    IDLE_TOP = 1
    STOPPED = 2
    MOVING_UP = 3
    MOVING_DOWN = 4
    MOVING_UP_END = 5
    MOVING_DOWN_END = 6


@dataclass(frozen=True)
class BerbelState:
    """One parsed main state frame from the hood."""

    raw: bytes
    lift_motion: int
    lift_position_raw: int
    down_brightness: int
    effect_white_brightness: int
    top_brightness: int
    effect_rgb: tuple[int, int, int]
    effect_brightness: int
    fan_level: int
    fan_run_on: bool

    @property
    def is_lift_moving_up(self) -> bool:
        """Whether the lift is moving up, in the open range or the end-approach zone."""
        return self.lift_motion in (LiftMotion.MOVING_UP, LiftMotion.MOVING_UP_END)

    @property
    def is_lift_moving_down(self) -> bool:
        """Whether the lift is moving down, in the open range or the end-approach zone."""
        return self.lift_motion in (LiftMotion.MOVING_DOWN, LiftMotion.MOVING_DOWN_END)

    @classmethod
    def parse(cls, data: bytes) -> BerbelState:
        """Parse a main state frame. Raises ValueError when the frame is too short."""
        if len(data) < MIN_MAIN_STATE_LENGTH:
            raise ValueError(
                f"main state frame too short: {len(data)} bytes, "
                f"need at least {MIN_MAIN_STATE_LENGTH}"
            )
        raw = bytes(data)
        return cls(
            raw=raw,
            lift_motion=raw[STATE_OFFSET_LIFT_MOTION],
            lift_position_raw=raw[STATE_OFFSET_LIFT_POSITION],
            down_brightness=raw[STATE_OFFSET_DOWN_BRIGHTNESS],
            effect_white_brightness=raw[STATE_OFFSET_EFFECT_WHITE_BRIGHTNESS],
            top_brightness=raw[STATE_OFFSET_TOP_BRIGHTNESS],
            effect_rgb=(
                raw[STATE_OFFSET_EFFECT_RED],
                raw[STATE_OFFSET_EFFECT_GREEN],
                raw[STATE_OFFSET_EFFECT_BLUE],
            ),
            effect_brightness=raw[STATE_OFFSET_EFFECT_BRIGHTNESS],
            fan_level=raw[STATE_OFFSET_FAN_LEVEL],
            fan_run_on=raw[STATE_OFFSET_FAN_RUN_ON] != 0,
        )


@dataclass(frozen=True)
class BerbelSettings:
    """One parsed settings frame from the hood. A higher color temperature is warmer."""

    raw: bytes
    down_color_temp: int
    effect_color_temp: int
    top_color_temp: int

    @classmethod
    def parse(cls, data: bytes) -> BerbelSettings:
        """Parse a settings frame. Raises ValueError when the frame is too short."""
        if len(data) < MIN_SETTINGS_LENGTH:
            raise ValueError(
                f"settings frame too short: {len(data)} bytes, "
                f"need at least {MIN_SETTINGS_LENGTH}"
            )
        raw = bytes(data)
        return cls(
            raw=raw,
            down_color_temp=raw[SETTINGS_OFFSET_DOWN_COLOR_TEMP],
            effect_color_temp=raw[SETTINGS_OFFSET_EFFECT_COLOR_TEMP],
            top_color_temp=raw[SETTINGS_OFFSET_TOP_COLOR_TEMP],
        )
