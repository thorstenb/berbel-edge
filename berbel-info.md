# Info on Berbel Skyline BLE communication protocol

## Basic BLE comms params

     BLE Packet Trace Analysis Summary

     Devices Involved
     ┌───────────────────┬───────────────────┬──────────────────────┐
     │       Role        │    MAC Address    │         Name         │
     ├───────────────────┼───────────────────┼──────────────────────┤
     │ berbel Range Hood │ 9c:9e:...         │ SKE_P (SKYLINE_EDGE) │
     └───────────────────┴───────────────────┴──────────────────────┘
     Custom berbel BLE Service


     Base UUID: f006f0XX-5745-4053-8043-62657262656c
     The last 6 bytes 62:65:72:62:65:6c decode to ASCII "berbel".

     Characteristics in protocol
     ┌────────┬──────────┬───────────────────────────────────┐
     │ Handle │   UUID   │              Purpose              │
     ├────────┼──────────┼───────────────────────────────────┤
     │ 0x0013 │ f006f002 │ Device name/extended info         │
     ├────────┼──────────┼───────────────────────────────────┤
     │ 0x0016 │ f006f003 │ Scene configuration data          │
     ├────────┼──────────┼───────────────────────────────────┤
     │ 0x0019 │ f006f004 │ Status data block 1 (31 bytes)    │
     ├────────┼──────────┼───────────────────────────────────┤
     │ 0x001c │ f006f005 │ Command write endpoint            │
     ├────────┼──────────┼───────────────────────────────────┤
     │ 0x001f │ f006f006 │ Status data block 2 (13 bytes)    │
     ├────────┼──────────┼───────────────────────────────────┤
     │ 0x0022 │ f006f006 │ Main status (indications enabled) │
     ├────────┼──────────┼───────────────────────────────────┤
     │ 0x0025 │ f006f007 │ Secondary status data             │
     └────────┴──────────┴───────────────────────────────────┘


     Status Data Format (31 bytes)

     Example: 01:4f:00:00:ff:00:00:00:05:00:ff:8b:00:00:00:00:01:00:01:00...

     ┌────────┬─────────────┬─────────────────────────────┐
     │ Offset │   Sample    │       Interpretation        │
     ├────────┼─────────────┼─────────────────────────────┤
     │ 0      │ 01          │ Status flag                 │
     ├────────┼─────────────┼─────────────────────────────┤
     │ 1      │ 4f          │ Device type ('O')           │
     ├────────┼─────────────┼─────────────────────────────┤
     │ 4      │ 00/ff       │ Light state (00=off, ff=on) │
     ├────────┼─────────────┼─────────────────────────────┤
     │ 8      │ 05          │ Current fan speed level     │
     ├────────┼─────────────┼─────────────────────────────┤
     │ 16-17  │ 00:00→04:00 │ Running counter/timer       │
 	 └────────┴─────────────┴─────────────────────────────┘


## Retrieved info from running berbel-ctrl

The below was retrieved by running berbel-ctrl against a live Berbel
Skyline.

- below shows which byte in the status update affects which control
  (indent is relevant):

- Raw: 01:4f:00:00:00:00:00:00:05:00:ff:4e:00:00:00:00:02:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                                                       fan
- Raw: 01:4f:00:00:00:00:00:01:05:00:ff:4e:00:00:00:00:02:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                           effect
- Raw: 01:4f:00:00:00:00:00:00:05:00:ff:4e:00:ff:00:00:02:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                                                side
- Raw: 01:4f:00:00:ff:00:00:00:05:00:ff:4e:00:ff:00:00:02:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                      down
- Raw: 01:4f:00:00:00:00:ff:00:05:00:ff:4e:00:00:00:00:02:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                            top
- Raw: 01:4f:00:00:00:00:ff:00:05:00:ff:4e:00:00:00:00:03:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                                                         fan 3
- Raw: 01:4f:00:00:00:00:ff:00:05:00:ff:4e:00:00:00:00:04:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                                                         fan boost
- Raw: 01:4f:00:00:00:00:ff:00:05:00:ff:4e:00:00:00:00:01:01:01:00:00:00:00:00:00:00:00:00:00:00:00
                                                           wait-fan
- Raw: 01:4f:00:00:00:00:c6:00:05:00:ff:4e:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                          dimmed
- Raw: 01:4f:00:00:00:00:00:00:05:a8:00:ff:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                                     [ pink ]
- Raw: 01:4f:00:00:00:00:00:00:05:00:ff:4e:00:ff:00:00:02:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                                     [ green]
- Raw: 01:4f:00:00:00:00:00:00:05:ff:15:00:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00
                                     [ red  ]

Some example states, with description on what the physical hardware
did:

- status update line, just effect lights on (in green):
  - Raw: 01:4f:00:00:00:00:00:00:05:00:ff:71:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00

- status update line, everything switched off:
  - Raw: 01:4f:00:00:00:00:00:00:05:00:ff:71:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00


## full BLE service_explorer trace

Here's the full BLE service_explorer dump, showing all BLE API
endpoints (with some amount of descriptions). Code used was this one:
https://github.com/hbldh/bleak/blob/develop/examples/service_explorer.py

__main__ INFO: starting scan...
__main__ INFO: connecting to device...
__main__ INFO: connected to SKE_P (9C:9E:..)
__main__ INFO: [Service] 0000180a-0000-1000-8000-00805f9b34fb (Handle: 10): Device Information
__main__ INFO:   [Characteristic] 00002a27-0000-1000-8000-00805f9b34fb (Handle: 13): Hardware Revision String (read), Value: bytearray(b'X.X.X')
__main__ INFO:   [Characteristic] 00002a26-0000-1000-8000-00805f9b34fb (Handle: 15): Firmware Revision String (read), Value: bytearray(b'1.0.5')
__main__ INFO:   [Characteristic] 00002a24-0000-1000-8000-00805f9b34fb (Handle: 11): Model Number String (read), Value: bytearray(b'SKYLINE_P')
__main__ INFO: [Service] 00001801-0000-1000-8000-00805f9b34fb (Handle: 6): Generic Attribute Profile
__main__ INFO:   [Characteristic] 00002a05-0000-1000-8000-00805f9b34fb (Handle: 7): Service Changed (indicate)
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 9): Client Characteristic Configuration, Value: bytearray(b'\x02\x00')
__main__ INFO: [Service] f007f000-5745-4053-8043-62657262656c (Handle: 42): Unknown
__main__ INFO:   [Characteristic] f007f004-5745-4053-8043-62657262656c (Handle: 52): Unknown (read,write,indicate), Value: bytearray(b'test2\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x83\xba\x00\x00\xc9\xc7A\x00\x05\xff\\\xff`\x00\xff\x02')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 54): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f014-5745-4053-8043-62657262656c (Handle: 82): Unknown (read,write,indicate), Value: bytearray(b'SCENE_14\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 84): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f002-5745-4053-8043-62657262656c (Handle: 46): Unknown (read,write,indicate), Value: bytearray(b'SCENE_2\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x02\x00\x00\x00\x00\x00\x00\x00\x00\xf1\x00\x00\x00\x00\x00\x00\xff\x03')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 48): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f010-5745-4053-8043-62657262656c (Handle: 70): Unknown (read,write,indicate), Value: bytearray(b'SCENE_10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 72): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f005-5745-4053-8043-62657262656c (Handle: 55): Unknown (read,write,indicate), Value: bytearray(b'SCENE_5\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 57): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f015-5745-4053-8043-62657262656c (Handle: 85): Unknown (read,write,indicate), Value: bytearray(b'SCENE_15\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 87): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f011-5745-4053-8043-62657262656c (Handle: 73): Unknown (read,write,indicate), Value: bytearray(b'SCENE_11\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 75): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f009-5745-4053-8043-62657262656c (Handle: 67): Unknown (read,write,indicate), Value: bytearray(b'SCENE_9\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 69): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f006-5745-4053-8043-62657262656c (Handle: 58): Unknown (read,write,indicate), Value: bytearray(b'SCENE_6\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 60): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f001-5745-4053-8043-62657262656c (Handle: 43): Unknown (read,write,indicate), Value: bytearray(b'SCENE_1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x19\xff\x00\x00222\xf0\x05\x00c\x9b\x00\x00\xff\x03')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 45): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f008-5745-4053-8043-62657262656c (Handle: 64): Unknown (read,write,indicate), Value: bytearray(b'SCENE_8\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 66): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f016-5745-4053-8043-62657262656c (Handle: 88): Unknown (read,write,indicate), Value: bytearray(b'SCENE_16\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 90): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f003-5745-4053-8043-62657262656c (Handle: 49): Unknown (read,write,indicate), Value: bytearray(b'test1\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00O\x00\x00\x00\xcd\xc7A\x00\x05\xff\\\xff`\x00\xff\x02')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 51): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f013-5745-4053-8043-62657262656c (Handle: 79): Unknown (read,write,indicate), Value: bytearray(b'SCENE_13\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 81): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f012-5745-4053-8043-62657262656c (Handle: 76): Unknown (read,write,indicate), Value: bytearray(b'SCENE_12\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 78): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f007f007-5745-4053-8043-62657262656c (Handle: 61): Unknown (read,write,indicate), Value: bytearray(b'SCENE_7\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 63): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO: [Service] f006f000-5745-4053-8043-62657262656c (Handle: 17): Unknown
__main__ INFO:   [Characteristic] f006f007-5745-4053-8043-62657262656c (Handle: 36): Unknown (read,write,indicate), Value: bytearray(b'O\x90\x00\x00\x00\x00\xb9\xc7=\x00\x00\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 38): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f006f005-5745-4053-8043-62657262656c (Handle: 30): Unknown (read,indicate), Value: bytearray(b'\x00\x00\x00\x00\x10\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 32): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f006f008-5745-4053-8043-62657262656c (Handle: 39): Unknown (read,write,indicate), Value: bytearray(b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 41): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f006f006-5745-4053-8043-62657262656c (Handle: 33): Unknown (read,write,indicate), Value: bytearray(b'\x01O\x00\x00\xff\x00\x00\x00\x05\x00\xffq\x00\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 35): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f006f002-5745-4053-8043-62657262656c (Handle: 21): Unknown (read,write,indicate), Value: bytearray(b'SKYLINE_EDGE\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 23): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f006f001-5745-4053-8043-62657262656c (Handle: 18): Unknown (read,indicate), Value: bytearray(b'SKYLINE_EDGE\x00\x00\x00\x00\x00\x00\x00\x00_100_PLAY\x00\x00\x00_BUF')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 20): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f006f003-5745-4053-8043-62657262656c (Handle: 24): Unknown (read,indicate), Value: bytearray(b'\x00\x00\x00\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 26): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] f006f004-5745-4053-8043-62657262656c (Handle: 27): Unknown (read,write,indicate), Value: bytearray(b'\x00\x00')
__main__ INFO:     [Descriptor] 00002902-0000-1000-8000-00805f9b34fb (Handle: 29): Client Characteristic Configuration, Value: bytearray(b'\x00\x00')
__main__ INFO: [Service] 00001800-0000-1000-8000-00805f9b34fb (Handle: 1): Generic Access Profile
__main__ INFO:   [Characteristic] 00002a01-0000-1000-8000-00805f9b34fb (Handle: 4): Appearance (read), Value: bytearray(b'\x00\x00')
__main__ INFO:   [Characteristic] 00002a00-0000-1000-8000-00805f9b34fb (Handle: 2): Device Name (read), Value: bytearray(b'Skyline')
__main__ INFO: disconnecting...
__main__ INFO: disconnecte


## Additional notes:

- there's references to 'test1' and 'test2' in the trace above. Those
  were set manually as SCENE1 and SCENE2 by me via the Berbel Android
  app. UUID target addresses: 3 and 4, but on this destination:
  f007f00 XYZ.
- not sure we need to deal with presets / scenes from HomeAssistant,
  given that we can easily control multiple properties there.


## Personal Bluetooth trace analysis

If known, bus activity is annotated with the physical action taking
place at the time:

- switched on suction: level 1,2,3,P
  0x02 - 0x05 is fan level

- then back to 0, then switch fan off / overridden the delay-off mode
  0x0c (sent twice, first to switch off, then delayed-off mode)

- switched on down light
  0x0a
  - changed light temp to warm, then back to cold
    "btatt.uuid128": "f0:06:f0:07:57:45:40:53:80:43:62:65:72:62:65:6c"
    "btatt.value": "4f:90:00:00:00:00:1a:ff:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
    then
    "btatt.value": "4f:90:00:00:00:00:c6:ff:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
    "btatt.value": "4f:90:00:00:00:00:d6:ff:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
    "btatt.value": "4f:90:00:00:00:00:cd:ff:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
  - reduced level, increased level
    "btatt.uuid128": "f0:06:f0:06:57:45:40:53:80:43:62:65:72:62:65:6c"
    "btatt.value": "01:4f:00:00:99:00:00:00:05:00:ff:8b:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
    then
    "btatt.value": "01:4f:00:00:63:00:00:00:05:00:ff:8b:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
    "btatt.value": "01:4f:00:00:ff:00:00:00:05:00:ff:8b:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"

- switched off down light
  - entirely unclear - 0x0a again?

- switched on effect light
   "btatt.uuid128": "f0:06:f0:06:57:45:40:53:80:43:62:65:72:62:65:6c"
   "btatt.value": "01:4f:00:00:00:00:00:00:05:00:ff:8b:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
  - changed color in 3-4 ways
    "btatt.value": "01:4f:00:00:00:00:00:00:05:ff:50:86:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
    "btatt.value": "01:4f:00:00:00:00:00:00:05:53:6a:ff:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
    "btatt.value": "01:4f:00:00:00:00:00:00:05:ff:cd:46:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
    "btatt.value": "01:4f:00:00:00:00:00:00:05:5c:ff:60:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"

  - reduced level
    "btatt.value": "01:4f:00:00:00:00:00:00:05:5c:ff:60:00:9e:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
    "btatt.value": "01:4f:00:00:00:00:00:00:05:5c:ff:60:00:4f:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"

  - changed mode from RGB to white
    "btatt.value": "01:4f:00:00:00:ff:00:00:05:5c:ff:60:00:4f:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"

  - changed light temp to warm
    "btatt.uuid128": "f0:06:f0:07:57:45:40:53:80:43:62:65:72:62:65:6c"
    "btatt.value": "4f:90:00:00:00:00:cd:ff:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"

  - reduced level
    "btatt.uuid128": "f0:06:f0:07:57:45:40:53:80:43:62:65:72:62:65:6c"
    "btatt.value": "4f:90:00:00:00:00:cd:25:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
    then
    "btatt.value": "4f:90:00:00:00:00:cd:de:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
    "btatt.value": "4f:90:00:00:00:00:cd:c7:23:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"


- switched off down light
  - unclear, no record

- switched on top light
  - unclear, no record
  - changed light temp to warm, then back to cold
    "btatt.uuid128": "f0:06:f0:06:57:45:40:53:80:43:62:65:72:62:65:6c"
    "btatt.value": "01:4f:00:00:00:80:00:00:05:5c:ff:60:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
    then
    "btatt.value": "01:4f:00:00:00:4d:00:00:05:5c:ff:60:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
    "btatt.value": "01:4f:00:00:00:00:00:00:05:5c:ff:60:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
    - reduced level, increased level
      the above?

- moved lift down (til end position reached)
  "btatt.uuid128": "f0:06:f0:04:57:45:40:53:80:43:62:65:72:62:65:6c"
  "btatt.value": "00:12"

- moved lift up (til end position reached)
  "btatt.value": "00:00"
  no, that is unlikely. 00:00 appears way too often in the trace.

Screne:

- switched on effect light, moved hood down a bit
  - stored as testscene1
    "btatt.uuid128": "f0:06:f0:07:57:45:40:53:80:43:62:65:72:62:65:6c"
    "btatt.value": "4f:90:00:00:00:00:cd:c7:24:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
    "btatt.value": "4f:90:00:00:00:00:cd:c7:cf:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
    "btatt.value": "4f:90:00:00:00:00:cd:c7:cc:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
    "btatt.value": "4f:90:00:00:00:00:cd:c7:40:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
    "btatt.value": "4f:90:00:00:00:00:cd:c7:41:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"

- switched on effect light, switched on down light, moved hood down a bit
	- stored as testscene2
      "btatt.uuid128": "f0:06:f0:06:57:45:40:53:80:43:62:65:72:62:65:6c"
      "btatt.value": "01:4f:00:00:00:00:91:00:05:5c:ff:60:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
      "btatt.value": "01:4f:00:00:00:00:c9:00:05:5c:ff:60:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
      "btatt.value": "01:4f:00:00:00:00:4f:00:05:5c:ff:60:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"

Other values encountered (for uuid" "f0:06:f0:04:57:45:40:53:80:43:62:65:72:62:65:6c")
- "btatt.value": "00:12" (switch on top light?)
- "btatt.value": "00:0d" (switch on down light, low-intensity mode?)
- "btatt.value": "00:09" (lift down?)

then:
- "btatt.uuid128": "f0:06:f0:06:57:45:40:53:80:43:62:65:72:62:65:6c"
  "btatt.value": "01:4f:00:00:00:4d:00:00:05:5c:ff:60:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
  "btatt.value": "01:4f:00:00:00:4d:00:00:05:5c:ff:60:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"

then:
- "btatt.uuid128": "f0:07:f0:03:57:45:40:53:80:43:62:65:72:62:65:6c"
  "btatt.value": "74:65:73:74:31:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:4f:00:00:00:cd:c7:41:00:05:ff:5c:ff:60:00:00:02"
- "btatt.uuid128": "f0:06:f0:06:57:45:40:53:80:43:62:65:72:62:65:6c"
  "btatt.value": "01:4f:00:00:00:00:00:00:05:5c:ff:60:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:03:00:00"

then:
- "btatt.value": "00:0d"
- "btatt.value": "00:0a"

then:
- "btatt.uuid128": "f0:06:f0:07:57:45:40:53:80:43:62:65:72:62:65:6c"
  "btatt.value": "4f:90:00:00:00:00:c9:c7:41:00:00:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00"
- "btatt.uuid128": "f0:06:f0:06:57:45:40:53:80:43:62:65:72:62:65:6c"
  "btatt.value": "02:83:00:00:a8:00:00:00:05:5c:ff:60:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
  "btatt.value": "02:83:00:00:ba:00:00:00:05:5c:ff:60:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"
- "btatt.uuid128": "f0:07:f0:04:57:45:40:53:80:43:62:65:72:62:65:6c"
  "btatt.value": "74:65:73:74:32:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:00:83:ba:00:00:c9:c7:41:00:05:ff:5c:ff:60:00:00:02"
- "btatt.uuid128": "f0:06:f0:06:57:45:40:53:80:43:62:65:72:62:65:6c"
  "btatt.value": "02:83:00:00:ba:00:00:00:05:5c:ff:60:00:ff:00:00:00:00:01:00:00:00:00:00:00:00:00:00:04:00:00"

then:
- "btatt.value": "00:01"

then:
- "btatt.uuid128": "f0:06:f0:06:57:45:40:53:80:43:62:65:72:62:65:6c"
  "btatt.value": "01:4f:00:00:ba:00:00:00:05:5c:ff:60:00:00:00:00:00:00:01:00:00:00:00:00:00:00:00:00:00:00:00"

then:
- "btatt.value": "00:0a"
