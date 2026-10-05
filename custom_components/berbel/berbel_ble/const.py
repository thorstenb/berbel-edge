"""Protocol constants for the Berbel Skyline Bluetooth Low Energy service.

The hood exposes one vendor GATT service whose UUID suffix spells "berbel" in ASCII. All
control and state traffic goes through the characteristics listed here, plus the standard
Device Information service for model and firmware strings.
"""

SERVICE_UUID = "f006f000-5745-4053-8043-62657262656c"

CHAR_DEVICE_INFO_LONG = "f006f001-5745-4053-8043-62657262656c"
CHAR_DEVICE_INFO = "f006f002-5745-4053-8043-62657262656c"
CHAR_ACKNOWLEDGMENT = "f006f003-5745-4053-8043-62657262656c"
CHAR_COMMAND = "f006f004-5745-4053-8043-62657262656c"
CHAR_FLAGS = "f006f005-5745-4053-8043-62657262656c"
CHAR_MAIN_STATE = "f006f006-5745-4053-8043-62657262656c"
CHAR_SETTINGS = "f006f007-5745-4053-8043-62657262656c"

DEVICE_INFORMATION_SERVICE_UUID = "0000180a-0000-1000-8000-00805f9b34fb"
CHAR_MODEL_NUMBER = "00002a24-0000-1000-8000-00805f9b34fb"
CHAR_FIRMWARE_REVISION = "00002a26-0000-1000-8000-00805f9b34fb"
CHAR_HARDWARE_REVISION = "00002a27-0000-1000-8000-00805f9b34fb"

# A command is written to the command characteristic as the pair 0x00
# plus the code, and every press is followed by a release pair (0x00,
# 0x00) fifty milliseconds later. This emulates the
# button-down/button-up events of the Berbel remote control.
#
# The light toggle codes 0x0a, 0x12 and 0x06 exist on the hood but the
# lights are controlled by writing the main state frame instead.
COMMAND_RELEASE = 0x00
COMMAND_FAN_LEVEL_1 = 0x02
COMMAND_FAN_LEVEL_2 = 0x03
COMMAND_FAN_LEVEL_3 = 0x04
COMMAND_FAN_BOOST = 0x05
COMMAND_FAN_OFF = 0x0C
COMMAND_LIFT_UP = 0x09
COMMAND_LIFT_DOWN = 0x0D

FAN_LEVEL_COMMANDS = {
    1: COMMAND_FAN_LEVEL_1,
    2: COMMAND_FAN_LEVEL_2,
    3: COMMAND_FAN_LEVEL_3,
}

PRESS_RELEASE_GAP_SECONDS = 0.05

# Byte offsets in the 31-byte main state frame. The lift position raw value rises while
# the lift moves down, so the top end stop is the smaller number.
STATE_OFFSET_LIFT_MOTION = 0
STATE_OFFSET_LIFT_POSITION = 1
STATE_OFFSET_DOWN_BRIGHTNESS = 4
STATE_OFFSET_EFFECT_WHITE_BRIGHTNESS = 5
STATE_OFFSET_TOP_BRIGHTNESS = 6
STATE_OFFSET_EFFECT_PROGRAM = 7
STATE_OFFSET_EFFECT_RED = 9
STATE_OFFSET_EFFECT_GREEN = 10
STATE_OFFSET_EFFECT_BLUE = 11
STATE_OFFSET_EFFECT_BRIGHTNESS = 13
STATE_OFFSET_FAN_LEVEL = 16
STATE_OFFSET_FAN_RUN_ON = 17

# Byte offsets in the 26-byte settings frame. A higher color temperature byte is warmer.
SETTINGS_OFFSET_DOWN_COLOR_TEMP = 6
SETTINGS_OFFSET_EFFECT_COLOR_TEMP = 7
SETTINGS_OFFSET_TOP_COLOR_TEMP = 8

MAIN_STATE_FRAME_LENGTH = 31
SETTINGS_FRAME_LENGTH = 26

MIN_MAIN_STATE_LENGTH = 20
MIN_SETTINGS_LENGTH = 9

# Default lift calibration values (simply some semi-plausible low and
# some high value). Both values are installation-defined and move
# after recalibration or repair, so they serve only as the starting
# calibration until the real end stops have been observed.
DEFAULT_LIFT_TOP_RAW = 0x0F
DEFAULT_LIFT_BOTTOM_RAW = 0xE0

RECONNECT_BACKOFF_BASE_SECONDS = 1.0
RECONNECT_BACKOFF_CAP_SECONDS = 60.0

FAN_OFF_STATE_TIMEOUT_SECONDS = 2.0
