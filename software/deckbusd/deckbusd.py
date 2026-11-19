#!/usr/bin/env python3
"""deckbusd - DeckBus v1 module detector for Kurogane K-7 (skeleton).

Watches each bay's MOD_DET# GPIO; on insert, selects the bay's PCA9546A channel,
reads the 24C32 ID EEPROM at 0x50, and loads the device-tree overlay it names.
On removal it unloads that overlay.

Needs: python3-smbus2, python3-gpiod (libgpiod v2), root (for dtoverlay).
Pin numbers below are placeholders: set them from the mainboard schematic.
"""
import subprocess
import time

import gpiod          # libgpiod v2 bindings
from smbus2 import SMBus, i2c_msg

I2C_BUS = 1
MUX_ADDR = 0x70       # PCA9546A
EEPROM_ADDR = 0x50
BAYS = {"L": {"det_gpio": 5, "mux_ch": 0}, "R": {"det_gpio": 6, "mux_ch": 1}}  # placeholders
CHIP = "/dev/gpiochip0"
POLL_S = 0.25

loaded = {}  # bay -> overlay name


def select_channel(bus, ch):
    bus.write_byte(MUX_ADDR, 1 << ch)


def read_eeprom(bus, length=0x58):
    bus.i2c_rdwr(i2c_msg.write(EEPROM_ADDR, [0x00, 0x00]))
    rd = i2c_msg.read(EEPROM_ADDR, length)
    bus.i2c_rdwr(rd)
    raw = bytes(rd)
    if raw[0:4] != b"DKB1":
        raise ValueError("bad magic %r" % raw[0:4])
    s = lambda a, n: raw[a:a + n].split(b"\0")[0].decode("utf-8", "replace")
    return {"vendor": s(0x04, 16), "product": s(0x14, 24), "version": s(0x2C, 8), "overlay": s(0x34, 32)}


def dtoverlay(args):
    subprocess.run(["dtoverlay"] + args, check=False)


def main():
    chip = gpiod.Chip(CHIP)
    lines = {b: chip.request_lines(consumer="deckbusd",
                                   config={c["det_gpio"]: gpiod.LineSettings(direction=gpiod.line.Direction.INPUT)})
             for b, c in BAYS.items()}
    with SMBus(I2C_BUS) as bus:
        while True:
            for bay, cfg in BAYS.items():
                present = lines[bay].get_value(cfg["det_gpio"]) == gpiod.line.Value.INACTIVE  # active low
                if present and bay not in loaded:
                    time.sleep(0.3)  # let the deck's power delay finish
                    try:
                        select_channel(bus, cfg["mux_ch"])
                        info = read_eeprom(bus)
                    except Exception as e:  # noqa: BLE001
                        print("bay %s: no valid ID EEPROM (%s)" % (bay, e), flush=True)
                        loaded[bay] = None
                        continue
                    print("bay %s: %s %s v%s -> %s" % (bay, info["vendor"], info["product"],
                                                     info["version"], info["overlay"]), flush=True)
                    if info["overlay"]:
                        dtoverlay([info["overlay"]])
                    loaded[bay] = info["overlay"] or None
                elif not present and bay in loaded:
                    ov = loaded.pop(bay)
                    print("bay %s: removed" % bay, flush=True)
                    if ov:
                        dtoverlay(["-r", ov])
            time.sleep(POLL_S)


if __name__ == "__main__":
    main()
