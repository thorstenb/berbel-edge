"""Bluetooth Low Energy protocol library for Berbel extractor hoods.

Deliberately kept free of Home Assistant imports. The const and models
modules are importable without bleak installed; all bleak use lives in
the device module. BerbelDevice is therefore exported lazily, so
importing the package does not pull in bleak.

"""

from typing import TYPE_CHECKING

from .models import BerbelSettings, BerbelState, LiftMotion

if TYPE_CHECKING:
    from .device import BerbelDevice

__all__ = [
    "BerbelDevice",
    "BerbelSettings",
    "BerbelState",
    "LiftMotion",
]


def __getattr__(name: str):
    """Import BerbelDevice on first access, so bleak loads only when needed."""
    if name == "BerbelDevice":
        from .device import BerbelDevice

        return BerbelDevice
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
