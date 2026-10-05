"""Light platform for the Berbel Skyline integration.

The skyline edge hood has three light channels. The hob light and the
up light are white lights with a brightness byte in the main state
frame and a color temperature byte in the settings frame. The effect
light has two modes: a color mode with an RGB value and its own
brightness byte, and a white mode with a separate brightness byte and
a color temperature byte.

For the effect light, it seems the mode whose brightness byte is
nonzero is the active one.

ToDo: support the moving RGB light thingit for the effect light.

"""

from __future__ import annotations

from typing import Any

from homeassistant.components.light import (
    ATTR_BRIGHTNESS,
    ATTR_COLOR_TEMP_KELVIN,
    ATTR_RGB_COLOR,
    ColorMode,
    LightEntity,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import BerbelConfigEntry
from .berbel_ble import BerbelDevice, BerbelSettings
from .const import MAX_KELVIN, MIN_KELVIN, byte_to_kelvin, kelvin_to_byte
from .entity import BerbelEntity


async def async_setup_entry(
    hass: HomeAssistant,
    entry: BerbelConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the three light entities for a configured hood."""
    device = entry.runtime_data
    async_add_entities(
        [
            BerbelDownLight(device),
            BerbelTopLight(device),
            BerbelEffectLight(device),
        ]
    )


class BerbelLightBase(BerbelEntity, LightEntity):
    """Common behaviour of the hood light entities.

    The device pushes a fresh state frame after every write, so the
    entities report the pushed values.

    """

    _attr_min_color_temp_kelvin = MIN_KELVIN
    _attr_max_color_temp_kelvin = MAX_KELVIN

    def __init__(self, device: BerbelDevice, unique_id_suffix: str) -> None:
        """Store the device and derive the unique id from the device address."""
        super().__init__(device)
        self._attr_unique_id = f"{device.address}_{unique_id_suffix}"

    async def async_added_to_hass(self) -> None:
        """Register for settings frame updates in addition to the base registrations.

        The base entity registers the state and availability
        callbacks. The color temperatures live in the settings frame,
        so the lights also refresh when a new settings frame arrives.

        """
        await super().async_added_to_hass()
        self.async_on_remove(
            self._device.register_settings_callback(self._handle_settings_update)
        )

    @callback
    def _handle_settings_update(self, settings: BerbelSettings) -> None:
        """Update the entity state when the hood pushes a new settings frame."""
        self.async_write_ha_state()


class BerbelWhiteLight(BerbelLightBase):
    """A white light channel with brightness and color temperature.

    Subclasses bind the four accessors below to one channel of the device.
    """

    _attr_color_mode = ColorMode.COLOR_TEMP
    _attr_supported_color_modes = {ColorMode.COLOR_TEMP}

    def _read_brightness(self) -> int | None:
        """Return the channel brightness byte from the last state frame."""
        raise NotImplementedError

    def _read_color_temp_byte(self) -> int | None:
        """Return the channel color temperature byte from the last settings frame."""
        raise NotImplementedError

    async def _write_brightness(self, brightness: int) -> None:
        """Write the channel brightness byte. Zero switches the light off."""
        raise NotImplementedError

    async def _write_color_temp_byte(self, value: int) -> None:
        """Write the channel color temperature byte. A higher value is warmer."""
        raise NotImplementedError

    @property
    def is_on(self) -> bool | None:
        """The light is on while its brightness byte is nonzero."""
        brightness = self._read_brightness()
        if brightness is None:
            return None
        return brightness > 0

    @property
    def brightness(self) -> int | None:
        """The brightness byte, which already uses the 0 to 255 scale."""
        return self._read_brightness()

    @property
    def color_temp_kelvin(self) -> int | None:
        """The color temperature in Kelvin, mapped from the settings byte."""
        byte = self._read_color_temp_byte()
        if byte is None:
            return None
        return byte_to_kelvin(byte)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on, applying a requested color temperature and brightness."""
        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            await self._write_color_temp_byte(
                kelvin_to_byte(kwargs[ATTR_COLOR_TEMP_KELVIN])
            )
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is None:
            brightness = self._read_brightness() or 255
        await self._write_brightness(brightness)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off by writing a zero brightness byte."""
        await self._write_brightness(0)


class BerbelDownLight(BerbelWhiteLight):
    """The hob light, at the bottom of the hood."""

    _attr_translation_key = "down_light"

    def __init__(self, device: BerbelDevice) -> None:
        """Bind the entity to the down light channel."""
        super().__init__(device, "down_light")

    def _read_brightness(self) -> int | None:
        state = self._device.state
        return None if state is None else state.down_brightness

    def _read_color_temp_byte(self) -> int | None:
        settings = self._device.settings
        return None if settings is None else settings.down_color_temp

    async def _write_brightness(self, brightness: int) -> None:
        await self._device.set_down_light(brightness)

    async def _write_color_temp_byte(self, value: int) -> None:
        await self._device.set_down_color_temp(value)


class BerbelTopLight(BerbelWhiteLight):
    """The light at the top of the hob, illuminating the ceiling."""

    _attr_translation_key = "top_light"

    def __init__(self, device: BerbelDevice) -> None:
        """Bind the entity to the top light channel."""
        super().__init__(device, "top_light")

    def _read_brightness(self) -> int | None:
        state = self._device.state
        return None if state is None else state.top_brightness

    def _read_color_temp_byte(self) -> int | None:
        settings = self._device.settings
        return None if settings is None else settings.top_color_temp

    async def _write_brightness(self, brightness: int) -> None:
        await self._device.set_top_light(brightness)

    async def _write_color_temp_byte(self, value: int) -> None:
        await self._device.set_top_color_temp(value)


class BerbelEffectLight(BerbelLightBase):
    """The effect light on the side of the hood, which runs in either color mode or in white mode."""

    _attr_translation_key = "effect_light"
    _attr_supported_color_modes = {ColorMode.RGB, ColorMode.COLOR_TEMP}

    def __init__(self, device: BerbelDevice) -> None:
        """Bind the entity to the effect light channel."""
        super().__init__(device, "effect_light")

    @property
    def is_on(self) -> bool | None:
        """The light is on while either mode's brightness byte is nonzero."""
        state = self._device.state
        if state is None:
            return None
        return state.effect_brightness > 0 or state.effect_white_brightness > 0

    @property
    def color_mode(self) -> ColorMode | None:
        """Color mode while the color-mode brightness byte is nonzero, else white mode."""
        state = self._device.state
        if state is None:
            return None
        if state.effect_brightness > 0:
            return ColorMode.RGB
        return ColorMode.COLOR_TEMP

    @property
    def brightness(self) -> int | None:
        """The brightness byte of the active mode, on the 0 to 255 scale."""
        state = self._device.state
        if state is None:
            return None
        if state.effect_brightness > 0:
            return state.effect_brightness
        return state.effect_white_brightness

    @property
    def rgb_color(self) -> tuple[int, int, int] | None:
        """The color-mode RGB value from the last state frame."""
        state = self._device.state
        return None if state is None else state.effect_rgb

    @property
    def color_temp_kelvin(self) -> int | None:
        """The white-mode color temperature in Kelvin, mapped from the settings byte."""
        settings = self._device.settings
        if settings is None:
            return None
        return byte_to_kelvin(settings.effect_color_temp)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the light on in the requested mode.

        A requested color temperature selects white mode. A requested
        RGB color selects color mode, as does turning on while color
        mode is already active. Otherwise the light comes on in white
        mode.

        """
        brightness = kwargs.get(ATTR_BRIGHTNESS)
        if brightness is None:
            brightness = self.brightness or 255

        if ATTR_COLOR_TEMP_KELVIN in kwargs:
            await self._device.set_effect_color_temp(
                kelvin_to_byte(kwargs[ATTR_COLOR_TEMP_KELVIN])
            )
            await self._device.set_effect_white(brightness)
            return

        state = self._device.state
        rgb = kwargs.get(ATTR_RGB_COLOR)
        in_color_mode = state is not None and state.effect_brightness > 0
        if rgb is not None or in_color_mode:
            if rgb is None:
                rgb = state.effect_rgb if state is not None else (255, 255, 255)
            await self._device.set_effect_color(tuple(rgb), brightness)
            return

        await self._device.set_effect_white(brightness)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the light off by zeroing both mode brightness bytes.

        Writing a zero white-mode brightness also zeroes the
        color-mode brightness, so one write switches the light off
        whatever mode it was in. Seems to work.

        """
        await self._device.set_effect_white(0)
