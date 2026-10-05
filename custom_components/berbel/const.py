"""Misc. constants and color temperature helpers for the Berbel
   Skyline integration.

"""

from __future__ import annotations

DOMAIN = "berbel"

# The hood advertises only its local name, never the berbel service
# UUID. These are the name prefixes that identify a Berbel hood,
# matched without regard to case.
DEVICE_NAME_PREFIXES: tuple[str, ...] = ("SKE", "SKYLINE", "BERBEL")

# Config entry option keys for the lift end-stop calibration. Each
# option stores a raw position byte from the main state frame.
CONF_LIFT_TOP_RAW = "lift_top_raw"
CONF_LIFT_BOTTOM_RAW = "lift_bottom_raw"

# Default lift calibration values (simply some semi-plausible low and
# some high value). The top value is the raw position byte while the
# lift is fully up, and the bottom value is the byte at the bottom end
# stop. Both are installation-defined, so they only serve as a
# starting point until the real end stops have been observed.
DEFAULT_LIFT_TOP_RAW = 0x0F
DEFAULT_LIFT_BOTTOM_RAW = 0xE0

# The settings frame stores each white color temperature as a single
# byte where a higher value means a warmer light. Lets assume we can
# map the byte range linearly onto this Kelvin range.
MIN_KELVIN = 2700
MAX_KELVIN = 6500


def kelvin_to_byte(kelvin: int) -> int:
    """Map a color temperature in Kelvin onto the settings frame byte.

    The byte scale runs opposite to the Kelvin scale: 0 is the coldest
    temperature (MAX_KELVIN) and 255 the warmest (MIN_KELVIN). The
    result is clamped to 0-255.

    """
    byte = round((MAX_KELVIN - kelvin) * 255 / (MAX_KELVIN - MIN_KELVIN))
    return max(0, min(255, byte))


def byte_to_kelvin(byte: int) -> int:
    """Map a settings frame color temperature byte onto Kelvin.

    This is the inverse of kelvin_to_byte. The result is clamped to
    the range from MIN_KELVIN to MAX_KELVIN.

    """
    kelvin = round(MAX_KELVIN - byte * (MAX_KELVIN - MIN_KELVIN) / 255)
    return max(MIN_KELVIN, min(MAX_KELVIN, kelvin))
