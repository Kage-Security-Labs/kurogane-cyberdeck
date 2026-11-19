# DeckBus v1: module interface

DeckBus is the side-rail module standard of the Kurogane K-7. Each side of the lower body has
two dovetail rails (110 mm) and a 2 x 10 spring pogo block. A module is a 34 x 110 x 30 mm
side grip with a 28 x 100 mm 2-layer ENIG PCB whose inner face carries 20 flat pads.

## Contacts

Deck side: 2 x 10 spring pogo pins, 2.54 mm pitch.
Module side: 1.8 x 1.8 mm round-rect ENIG pads, 2.54 mm pitch, centred on the PCB
(footprint `DeckBus:DeckBus_v1_Pads_2x10_P2.54mm`, placed in `hardware/deckbus_module`).
Odd pins are the column nearer the front of the deck; pin 1 is at the top.

| Pin | Signal | Dir (deck view) | Limit / level |
|----:|--------|-----------------|---------------|
| 1 | GND | | |
| 2 | GND | | |
| 3 | VSYS | out | 6.0-8.4 V, eFuse TPS25947, 2 A |
| 4 | VSYS | out | (paired with 3) |
| 5 | +5V | out | TPS22965 load switch, 2 A |
| 6 | +5V | out | (paired with 5) |
| 7 | +3V3 | out | 300 mA |
| 8 | GND | | |
| 9 | USB2 D+ | bidir | 90 ohm diff, from USB2514B |
| 10 | USB2 D- | bidir | |
| 11 | GND | | |
| 12 | I2C SDA | bidir | 3.3 V, 100 kHz, PCA9546A channel per bay |
| 13 | I2C SCL | out | |
| 14 | UART TX | out | 3.3 V, deck to module |
| 15 | UART RX | in | 3.3 V |
| 16 | GPIO A | bidir | 3.3 V, PWM capable |
| 17 | GPIO B / IRQ | bidir | 3.3 V, PPS or interrupt |
| 18 | MOD_DET# | in | module ties to GND; deck pull-up 10 k |
| 19 | VCHG_IN | in | 5-12 V from battery/solar modules to charger input 2 |
| 20 | GND | | |

## Rules

1. Every module has a 24C32 EEPROM at 0x50 on the bay's I2C channel. Content (UTF-8, NUL padded):
   `0x000 magic "DKB1"`, `0x004 vendor[16]`, `0x014 product[24]`, `0x02C version[8]`,
   `0x034 overlay[32]` (device-tree overlay name), `0x054 max_5v_ma u16`, `0x056 max_vsys_ma u16`.
2. Power is applied only after MOD_DET# has been low for about 200 ms (RC + Schmitt on the deck).
   Modules must tolerate power arriving after data lines see the deck.
3. Modules never drive VSYS, +5V or +3V3. A module that supplies energy does so only on VCHG_IN.
4. All logic is 3.3 V. Put a TVS on USB and on any pin that leaves the module.
5. Anything with an antenna brings its own SMA bulkhead on the module's outer face.
6. Budget: a module may draw at most 2 A from +5V and 2 A from VSYS, and 300 mA from +3V3.

## Software

`software/deckbusd/deckbusd.py` watches the two MOD_DET# GPIOs, reads the EEPROM through the
PCA9546A, and loads the overlay named in it with `dtoverlay`. Removing a module unloads it.
