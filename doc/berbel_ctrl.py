#!/usr/bin/env python3
"""
berbel+ Range Hood BLE Controller

Hacked-up attempt to control berbel SKYLINE EDGE (and perhaps similar?) range
hoods via Bluetooth Low Energy. See berbel-info.md for some reverse-engineered
protocol bits this is based on.
"""

import asyncio
import argparse
import sys
from bleak import BleakClient, BleakScanner
from bleak.backends.characteristic import BleakGATTCharacteristic

# Base UUID: f006f0XX-5745-4053-8043-62657262656c ("berbel" encoded in last 6 bytes)
SERVICE_UUID = "f006f000-5745-4053-8043-62657262656c"
CHAR_DEVICE_INFO_LONG = "f006f001-5745-4053-8043-62657262656c"
CHAR_DEVICE_INFO = "f006f002-5745-4053-8043-62657262656c"
CHAR_ACK = "f006f003-5745-4053-8043-62657262656c"
CHAR_COMMAND = "f006f004-5745-4053-8043-62657262656c"
CHAR_FLAGS = "f006f005-5745-4053-8043-62657262656c"
CHAR_STATUS = "f006f006-5745-4053-8043-62657262656c"
CHAR_SETTINGS = "f006f007-5745-4053-8043-62657262656c"

# Command codes, from the BLE trace (see berbel-info.md).
#
# Each command is a button press: 0x00 plus the code, followed about
# some 50 ms later by 0x00 0x00, the button release.
COMMANDS = {
    "off": 0x0c,           # fan off; a further press toggles run-on mode
    "speed1": 0x02,
    "speed2": 0x03,
    "speed3": 0x04,
    "boost": 0x05,         # intensive level P
    "light": 0x0a,         # toggle down light
    "light_top": 0x12,     # toggle top light
    "light_effect": 0x06,  # toggle effect light (from notes, not in the trace)
    "lift_up": 0x09,
    "lift_down": 0x0d,     # the same direction again stops a moving lift?
}


def parse_status(data: bytes) -> dict:
    if len(data) < 20:
        return {"raw": data.hex(":")}

    return {
        "raw": data.hex(":"),
        # 01 idle at top, 02 stopped mid-travel, 03 moving up,
        # 04 moving down, 05 and 06 the same in the end-approach zone
        "lift_motion": data[0],
        # 0x4f fully up, rising while the lift moves down
        "lift_position": data[1],
        "down_brightness": data[4],
        "effect_white_brightness": data[5],
        "top_brightness": data[6],
        "effect_color": (data[9], data[10], data[11]),
        "effect_brightness": data[13],
        "fan_speed": data[16],
        "fan_run_on": data[17] == 0x01,
    }

i = 0

def status_callback(characteristic: BleakGATTCharacteristic, data: bytearray):
    global i
    status = parse_status(bytes(data))
    print(f"\n[Status Update {i}]")
    print(f"  Raw: {status['raw']}")
    print(f"  Fan: level {status.get('fan_speed', '?')}, run-on {status.get('fan_run_on', '?')}")
    print(f"  Lights: down {status.get('down_brightness', '?')}, top {status.get('top_brightness', '?')}, "
          f"effect {status.get('effect_brightness', '?')} rgb {status.get('effect_color', '?')} "
          f"white {status.get('effect_white_brightness', '?')}")
    print(f"  Lift: position {status.get('lift_position', '?')}, motion {status.get('lift_motion', '?')}")


async def scan_for_berbel(timeout: float = 10.0) -> list:
    print(f"Scanning for berbel devices ({timeout}s)...")

    devices = []
    discovered = await BleakScanner.discover(timeout=timeout, return_adv=True)

    for device, adv_data in discovered.values():
        name = adv_data.local_name or device.name or ""
        # berbel devices have names like "SKE_P" (SKYLINE EDGE) or contain "berbel"
        if any(x in name.upper() for x in ["SKE", "BERBEL", "SKYLINE", "BKE", "BIH"]):
            devices.append((device, name))
            print(f"  Found: {name} [{device.address}]")

    # Also check for devices advertising the berbel service UUID
    for device, adv_data in discovered.values():
        if SERVICE_UUID.lower() in [str(u).lower() for u in (adv_data.service_uuids or [])]:
            if device not in [d[0] for d in devices]:
                name = adv_data.local_name or device.name or "Unknown"
                devices.append((device, name))
                print(f"  Found (by service): {name} [{device.address}]")

    return devices


async def connect_and_control(address: str, command: str = None, interactive: bool = False):
    print(f"Connecting to {address}...")

    async with BleakClient(address) as client:
        print(f"Connected: {client.is_connected}")

        # Read device info
        try:
            info = await client.read_gatt_char(CHAR_DEVICE_INFO)
            device_name = info.split(b'\x00')[0].decode('utf-8', errors='ignore')
            print(f"Device: {device_name}")
        except Exception as e:
            print(f"Could not read device info: {e}")

        # Subscribe to status updates
        try:
            await client.start_notify(CHAR_STATUS, status_callback)
            print("Subscribed to status updates")
        except Exception as e:
            print(f"Could not subscribe to status: {e}")

        # Read initial status
        try:
            status_data = await client.read_gatt_char(CHAR_STATUS)
            status = parse_status(status_data)
            print(f"Current state - Fan: {status.get('fan_speed', '?')}, "
                  f"Lights (down/top/effect): {status.get('down_brightness', '?')}/"
                  f"{status.get('top_brightness', '?')}/{status.get('effect_brightness', '?')}, "
                  f"Lift: {status.get('lift_position', '?')}")
        except Exception as e:
            print(f"Could not read status: {e}")

        # Send command if specified
        if command:
            await send_command(client, command)

        # Interactive mode
        if interactive:
            await interactive_mode(client)
        elif command:
            # Wait a moment for status update after command
            await asyncio.sleep(1.0)


async def send_command(client: BleakClient, command: str):
    if command not in COMMANDS:
        # Try to parse as raw hex or number
        try:
            if command.startswith("0x"):
                code = int(command, 16)
            else:
                code = int(command)
        except ValueError:
            print(f"Unknown command: {command}")
            print(f"Available commands: {', '.join(COMMANDS.keys())}")
            return
    else:
        code = COMMANDS[command]

    data = bytes([0x00, code])
    print(f"Sending command: {command} (0x{code:02x})")

    try:
        await client.write_gatt_char(CHAR_COMMAND, data, response=True)
        # Every command is a button press. The matching release follows
        # about 50 ms later, the same spacing the vendor app uses; a
        # held button makes the hood dim lights slowly instead.
        await asyncio.sleep(0.05)
        await client.write_gatt_char(CHAR_COMMAND, bytes([0x00, 0x00]), response=True)
        print("Command sent successfully")
    except Exception as e:
        print(f"Failed to send command: {e}")


async def interactive_mode(client: BleakClient):
    print("\n=== Interactive Mode ===")
    print("Commands: off, speed1-3, boost, light, light_top, light_effect, lift_up, lift_down")
    print("Or enter raw hex code (e.g., 0x0a)")
    print("Type 'quit' or 'q' to exit\n")

    while True:
        try:
            cmd = await asyncio.get_event_loop().run_in_executor(
                None, lambda: input("berbel> ").strip().lower()
            )
        except EOFError:
            break

        if cmd in ('quit', 'q', 'exit'):
            break
        if not cmd:
            continue

        if cmd == 'status':
            try:
                status_data = await client.read_gatt_char(CHAR_STATUS)
                status = parse_status(status_data)
                print(f"Fan: {status.get('fan_speed', '?')}, "
                      f"Lights (down/top/effect): {status.get('down_brightness', '?')}/"
                      f"{status.get('top_brightness', '?')}/{status.get('effect_brightness', '?')}, "
                      f"Lift: {status.get('lift_position', '?')}")
            except Exception as e:
                print(f"Error reading status: {e}")
        elif cmd == 'help':
            print("Commands: off, speed1-3, boost, light, light_top, light_effect, "
                  "lift_up, lift_down, status, quit")
        else:
            await send_command(client, cmd)
            await asyncio.sleep(0.5)


async def main():
    parser = argparse.ArgumentParser(
        description="Control berbel range hoods via BLE",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  off           Switch the fan off (a further press toggles run-on mode)
  speed1-3      Set fan level 1-3
  boost         Intensive level P
  light         Toggle the down light
  light_top     Toggle the top light
  light_effect  Toggle the effect light
  lift_up       Move the lift up (the same direction again stops it)
  lift_down     Move the lift down (the same direction again stops it)

Examples:
  %(prog)s --scan                    # Scan for devices
  %(prog)s -a AA:BB:CC:DD:EE:FF speed3   # Set speed to 3
  %(prog)s -a AA:BB:CC:DD:EE:FF -i   # Interactive mode
        """
    )
    parser.add_argument("--scan", "-s", action="store_true", help="Scan for berbel devices")
    parser.add_argument("--address", "-a", type=str, help="Device MAC address")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("command", nargs="?", help="Command to send")

    args = parser.parse_args()

    if args.scan:
        devices = await scan_for_berbel()
        if not devices:
            print("No berbel devices found")
        return

    if not args.address:
        # Try to find a device automatically
        devices = await scan_for_berbel(timeout=5.0)
        if not devices:
            print("No berbel devices found. Use --address to specify manually.")
            sys.exit(1)
        if len(devices) > 1:
            print("\nMultiple devices found. Please specify with --address:")
            for dev, name in devices:
                print(f"  {dev.address}  {name}")
            sys.exit(1)
        args.address = devices[0][0].address
        print(f"Using device: {devices[0][1]} [{args.address}]")

    if not args.command and not args.interactive:
        print("No command specified. Use --interactive or provide a command.")
        print("Use --help for usage information.")
        sys.exit(1)

    await connect_and_control(args.address, args.command, args.interactive)


if __name__ == "__main__":
    asyncio.run(main())
