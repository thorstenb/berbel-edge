# Info on Berbel Skyline BLE communication protocol

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
__main__ INFO: connected to SKE_P (9C:9E:...)
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
__main__ INFO: disconnected

## Additional notes:

- there's references to 'test1' and 'test2' in the trace above. Those
  were set manually as SCENE1 and SCENE2 by me via the Berbel Android
  app. UUID target addresses: 3 and 4, but on this destination:
  f007f00 XYZ.
- not sure we need to deal with presets / scenes from HomeAssistant,
  given that we can easily control multiple properties there.
