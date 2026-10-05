"""Cover platform for the lift of a Berbel Skyline.

The lift is the height-adjustable part of the hood. It moves between two end stops and
reports its position in every main state frame, so the entity is fully stateful. There is
no command to move to an arbitrary position, so the entity offers open, close and stop
only.
"""

from __future__ import annotations

from typing import Any

from homeassistant.components.cover import CoverEntity, CoverEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BerbelConfigEntry
from .berbel_ble import BerbelDevice
from .entity import BerbelEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BerbelConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the lift cover entity for a config entry."""
    async_add_entities([BerbelLiftCover(entry.runtime_data)])


class BerbelLiftCover(BerbelEntity, CoverEntity):
    """The lift of the hood. Open is fully up and closed is at the bottom end stop."""

    _attr_translation_key = "lift"
    _attr_supported_features = (
        CoverEntityFeature.OPEN | CoverEntityFeature.CLOSE | CoverEntityFeature.STOP
    )

    def __init__(self, device: BerbelDevice) -> None:
        """Create the lift entity for the given device."""
        super().__init__(device)
        self._attr_unique_id = f"{device.address}_lift"

    @property
    def current_cover_position(self) -> int | None:
        """The lift position as a percentage: 100 fully up, 0 at the bottom end stop.

        None until the first state frame has arrived.
        """
        return self._device.lift_position_pct()

    @property
    def is_closed(self) -> bool | None:
        """True when the lift sits at the bottom end stop, None while the position is
        unknown."""
        position = self._device.lift_position_pct()
        if position is None:
            return None
        return position == 0

    @property
    def is_opening(self) -> bool:
        """True while the lift is moving up."""
        state = self._device.state
        return state is not None and state.is_lift_moving_up

    @property
    def is_closing(self) -> bool:
        """True while the lift is moving down."""
        state = self._device.state
        return state is not None and state.is_lift_moving_down

    async def async_open_cover(self, **kwargs: Any) -> None:
        """Start the lift moving up. It runs to the top end stop on its own."""
        await self._device.lift_up()

    async def async_close_cover(self, **kwargs: Any) -> None:
        """Start the lift moving down. It runs to the bottom end stop on its own."""
        await self._device.lift_down()

    async def async_stop_cover(self, **kwargs: Any) -> None:
        """Stop the lift mid-travel."""
        await self._device.lift_stop()
