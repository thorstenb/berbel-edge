# Home Assistant integration for Berbel Skyline extractor hoods

This is a Home Assistant integration for my **Berbel Skyline Edge**
island range hood. It might, or might not work with other Berbel
models.


## Overview

Currently, the following functions are supported (see below for
missing bits):

### Lights

- up-light as well as hob light have separate level and color
  temperature controls
- the effect light also has a continuous RGB light control
- light status is near-live updated via BLE status broadcasts, and
  cooperates with the normal device remote

### Extractor fan

- Fan speed control has three levels
- run-on mode, and turbo boost level can be selected separately
- Fan status is near-live updated via BLE status broadcasts, and
  cooperates with the normal device remote

### Lift function

- the hood lift can be controlled via a HA 'cover' entity
- lift status is near-live updated via BLE status broadcasts, and
  cooperates with the normal device remote. Configured end positions
  are detected, and shown for the cover entity


## Installation

### HACS

1. Install HACS for your Home Assistant (see
   https://www.hacs.xyz/docs/use/) - since HA 2026.11, no need for any
   additional setup (https://www.hacs.xyz/docs/marketplace/)
2. Go to HACS (either top level, or under Settings -> Marketplace)
3. Click on the 3 dots in the top right corner
4. Select "Custom repositories"
5. Add this repo URL to the repository: `https://github.com/thorstenb/berbel-edge`
6. Select the correct type: needs to be "Integration"
7. Click the "ADD" button
8. Restart Home Assistant

### Manual Installation

1. Download the latest release from GitHub
2. Extract the `custom_components/berbel` folder to your Home Assistant `custom_components` directory
3. Restart Home Assistant


## Details

This integration uses a HA config flow to auto-detect a BLE-visible
Berbel range hood in the vicinity. Under **Settings**, then **Devices
& Services**, any newly-detected Berbel device should show up. If you
click on "Configure", a setup wizard should guide you through the
initial configuration.

Under normal operation, the Berbel broadcasts status updates via BLE,
which this integration subscribes to. That means, even when using the
built-in remote, or one of the gestures (for fan, hob light or lift),
the Home Assistant status should stay up-to-date.

What is missing currently, is support for the effect light's moving
light feature, as well as setup and recall of scenes. But see the
[documentation](doc/berbel-info.md) for some initial analysis, how
that possibly works on the protocol level.


## Development

Code is below `custom_components/berbel`, split into pure BLE protocol
bits (`custom_components/berbel/berbel_ble`) and a rather bog-standard
HA integration on top of that.

Please run `tox` and fix all problems before submitting a PR. Please
add a test below `tests` if you add a new function, or implement an
additional part of the protocol.


## License

Unless otherwise noted in individual files, this project is licensed
under the MIT License. The [LICENSE](LICENSE) file has all the details.


## ⚠️ Disclaimer

This integration is not officially affiliated with or endorsed by
berbel Ablufttechnik GmbH. Use at your own risk - the developers are
not responsible for any damage to your device or property.
