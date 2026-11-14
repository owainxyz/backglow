# Protocol

AOC AGON monitors expose Light FX over DDC/CI (VESA MCCS 2.2) on the display cable's i2c bus, at the standard DDC/CI address `0x37`. The features are manufacturer-specific and use three-byte VCP codes instead of the usual single byte.

## Framing

Standard DDC/CI framing applies. Host to monitor:

```
51  80|n  payload[n]  checksum
```

The checksum is `0x6E` XOR every byte from `0x51` through the last payload byte.

Monitor to host:

```
6E  80|n  payload[n]  checksum
```

The checksum is `0x50` XOR every byte from `0x6E` through the checksum itself, which must give zero.

## Extended features

| Operation | Payload                     |
|-----------|-----------------------------|
| Get       | `01 F8 E1 cc`               |
| Set       | `03 F8 E1 cc hi lo`         |

A get reply payload is `02 00 F8 cc max_hi max_lo cur_hi cur_lo`. Byte 3 is `00` on success.

Wait at least 50 ms after a get before reading, and about 80 ms between consecutive sets. Faster writes are dropped.

## Light FX codes

| Code | Feature       | Values                                            |
|------|---------------|---------------------------------------------------|
| `60` | Strength      | 0 off, 1 low, 2 medium, 3 strong                  |
| `61` | Effect        | 0 to max; the list depends on max (below)         |
| `62` | Pattern       | 0 red, 1 green, 2 blue, 3 rainbow, 4 custom       |
| `63` | Secondary R   | 0 to 100                                          |
| `64` | Secondary G   | 0 to 100                                          |
| `65` | Secondary B   | 0 to 100                                          |
| `66` | Custom R      | 0 to 100                                          |
| `67` | Custom G      | 0 to 100                                          |
| `68` | Custom B      | 0 to 100                                          |

On the AG276QKD2 the secondary colour does not accept writes while the effect is Static.

## Effect lists

The maximum value reported for `61` selects the list:

| Max | Effects |
|-----|---------|
| 12  | Static, Simple Shift, Gradient Shift, Simple Filling, 1 Way Filling, 2 Way Filling, Breathing, Motion Point, Zoom, Discolor, Water Wave, Flashing, Demo |
| 13  | Audio, then the max 12 list |
| 14  | Audio 1, Audio 2, Static, Dark Point Sweep, Gradient Shift, Spread Fill, Drip Fill, Spreading Drip Fill, Breathing, Light Point Sweep, Zoom, Rainbow, Wave, Flashing, Demo |
| 15  | LoL, then the max 14 list |
| 16  | CS, then the max 14 list |

## Capabilities

The AG276QKD2 advertises its extended features in its capabilities string as `F8E1xx` entries, for example `F8E161(00 01 ... 0E)`. Light FX codes that are not listed may still respond.

## Verification

Each code was confirmed on an AG276QKD2 by setting it and observing the LEDs, and by changing the setting in the monitor's on-screen menu and reading it back.
