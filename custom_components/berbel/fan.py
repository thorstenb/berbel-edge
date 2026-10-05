"""Fan platform for the Berbel Skyline integration.

The hood has one fan with three regular speed levels, and one
turbo-boost power level P. There's additionally a run-on mode that
keeps the fan running for a while before it switches off on its own.

"""

from __future__ import annotations

import math
from typing import Any

from homeassistant.components.fan import FanEntity, FanEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.util.percentage import (
    percentage_to_ranged_value,
    ranged_value_to_percentage,
)

from . import BerbelConfigEntry
from .berbel_ble import BerbelDevice
from .entity import BerbelEntity

# The hood reports fan levels 1 to 3 as plain speeds. Level 4 is the
# power-boost level P, which is exposed as a preset mode rather than a
# speed.
SPEED_RANGE = (1, 3)
FAN_LEVEL_INTENSIVE = 4

PRESET_MODE_INTENSIVE = "intensive"
PRESET_MODE_RUN_ON = "run_on"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BerbelConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the fan entity for a config entry."""
    device = entry.runtime_data
    async_add_entities([BerbelFan(device)])


class BerbelFan(BerbelEntity, FanEntity):
    """The extractor fan of the hood."""

    _attr_name = None
    _attr_supported_features = (
        FanEntityFeature.SET_SPEED
        | FanEntityFeature.TURN_ON
        | FanEntityFeature.TURN_OFF
        | FanEntityFeature.PRESET_MODE
    )
    _attr_speed_count = 3
    _attr_preset_modes = [PRESET_MODE_INTENSIVE, PRESET_MODE_RUN_ON]

    def __init__(self, device: BerbelDevice) -> None:
        """Set up the fan entity for the given device."""
        super().__init__(device)
        self._attr_unique_id = f"{device.address}_fan"

    @property
    def is_on(self) -> bool | None:
        """Whether the fan is running, at any speed level including intensive."""
        state = self._device.state
        if state is None:
            return None
        return state.fan_level > 0

    @property
    def percentage(self) -> int | None:
        """The current speed as a percentage. Zero means the fan is off. While the
        intensive level is active the speed is outside the plain 1 to 3 range, so no
        percentage is reported."""
        state = self._device.state
        if state is None:
            return None
        if state.fan_level == FAN_LEVEL_INTENSIVE:
            return None
        if state.fan_level == 0:
            return 0
        return ranged_value_to_percentage(SPEED_RANGE, state.fan_level)

    @property
    def preset_mode(self) -> str | None:
        """The active preset mode: intensive while the fan runs at level P, run_on while
        the delayed shutoff is counting down, and None otherwise."""
        state = self._device.state
        if state is None:
            return None
        if state.fan_level == FAN_LEVEL_INTENSIVE:
            return PRESET_MODE_INTENSIVE
        if state.fan_run_on:
            return PRESET_MODE_RUN_ON
        return None

    async def async_set_percentage(self, percentage: int) -> None:
        """Set the fan speed. Zero percent switches the fan hard off."""
        if percentage == 0:
            await self._device.fan_off()
            return
        level = math.ceil(percentage_to_ranged_value(SPEED_RANGE, percentage))
        await self._device.set_fan_level(level)

    async def async_set_preset_mode(self, preset_mode: str) -> None:
        """Activate a preset mode: the intensive level P or the run-on delayed shutoff."""
        if preset_mode == PRESET_MODE_INTENSIVE:
            await self._device.set_fan_boost()
        elif preset_mode == PRESET_MODE_RUN_ON:
            await self._device.fan_run_on()

    async def async_turn_on(
        self,
        percentage: int | None = None,
        preset_mode: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Turn the fan on, at the requested speed or preset, or at level 1 when the
        call names neither."""
        if preset_mode is not None:
            await self.async_set_preset_mode(preset_mode)
            return
        if percentage is not None:
            await self.async_set_percentage(percentage)
            return
        await self._device.set_fan_level(1)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch the fan hard off, past the run-on delayed shutoff."""
        await self._device.fan_off()
