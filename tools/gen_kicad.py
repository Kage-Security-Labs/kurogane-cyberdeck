#!/usr/bin/env python3
"""Generate the Kurogane K-7 KiCad 8 project skeletons.

Run from the repo root:  python3 tools/gen_kicad.py
Re-running overwrites the generated files, so do it only before you start
drawing real schematics/layout (or change OUT to a scratch folder).

What it makes
  hardware/mainboard/      6-layer CM5 carrier: hierarchical sheets + board outline,
                           mounting holes, placement zones on Dwgs.User
  hardware/keyboard/       input board: sheets + outline + key/button position guides
                           + key_positions.csv (x, y, label, matrix row/col)
  hardware/deckbus_module/ DeckBus v1 module template: 20 contact pads with nets,
                           M3 holes, EEPROM note
All geometry is in millimetres; edit the parameters below and re-run.
"""
import csv
import json
import os
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "hardware")


def U():
    return str(uuid.uuid4())


def q(s):
    """Quote a string for KiCad s-expressions."""
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


# ---------------------------------------------------------------- project file
def write_pro(path, name, netclasses):
    classes = []
    for nc in netclasses:
        d = {
            "name": nc[0], "clearance": nc[1], "track_width": nc[2],
            "via_diameter": 0.6, "via_drill": 0.3,
            "diff_pair_width": nc[3], "diff_pair_gap": nc[4], "diff_pair_via_gap": 0.25,
            "microvia_diameter": 0.3, "microvia_drill": 0.1,
            "bus_width": 12, "wire_width": 6, "line_style": 0,
            "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)",
            "priority": 2147483647 if nc[0] == "Default" else len(classes),
        }
        classes.append(d)
    pro = {
        "meta": {"filename": name + ".kicad_pro", "version": 1},
        "net_settings": {"classes": classes, "meta": {"version": 3},
                         "net_colors": None, "netclass_assignments": None,
                         "netclass_patterns": []},
        "text_variables": {"PROJECT": "Kurogane K-7", "REV": "A"},
    }
    with open(path, "w") as f:
        json.dump(pro, f, indent=2)


# ---------------------------------------------------------------- schematics
def sch_text(text, x, y, size=1.5):
    return ("  (text %s (exclude_from_sim no) (at %.2f %.2f 0)\n"
            "    (effects (font (size %.2f %.2f)) (justify left top)) (uuid %s))\n"
            % (q(text), x, y, size, size, q(U())))


def write_sheet_file(path, title, body_lines, sheet_uuid=None, paper="A4"):
    s = ["(kicad_sch (version 20231120) (generator \"eeschema\") (generator_version \"8.0\")\n",
         "  (uuid %s)\n" % q(sheet_uuid or U()),
         "  (paper %s)\n" % q(paper),
         "  (title_block (title %s) (rev \"A\") (company \"Kurogane K-7\"))\n" % q(title),
         "  (lib_symbols)\n",
         sch_text(title, 15, 15, 3),
         sch_text("\n".join(body_lines), 15, 25, 1.5)]
    return s


def write_root_sch(folder, project, title, sheets, intro):
    """sheets: list of (name, filename, notes[])"""
    root_uuid = U()
    s = write_sheet_file(None, title, intro, root_uuid, paper="A3")
    x, y, w, h = 30.0, 90.0, 60.0, 30.0
    col = 0
    for i, (name, fname, notes) in enumerate(sheets):
        sx = x + col * (w + 20)
        s.append(
            "  (sheet (at %.2f %.2f) (size %.2f %.2f) (fields_autoplaced yes)\n"
            "    (stroke (width 0.1524) (type solid)) (fill (color 0 0 0 0.0000))\n"
            "    (uuid %s)\n"
            "    (property \"Sheetname\" %s (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) (justify left bottom)))\n"
            "    (property \"Sheetfile\" %s (at %.2f %.2f 0) (effects (font (size 1.27 1.27)) (justify left top)))\n"
            "    (instances (project %s (path %s (page %s)))))\n"
            % (sx, y, w, h, q(U()), q(name), sx, y - 0.7, q(fname), sx, y + h + 0.6,
               q(project), q("/" + root_uuid), q(str(i + 2))))
        col += 1
        if col == 4:
            col = 0
            y += h + 25
        child = write_sheet_file(None, name, notes)
        child.append(")\n")
        with open(os.path.join(folder, fname), "w") as f:
            f.write("".join(child))
    s.append("  (sheet_instances (path \"/\" (page \"1\")))\n)\n")
    with open(os.path.join(folder, project + ".kicad_sch"), "w") as f:
        f.write("".join(s))


# ---------------------------------------------------------------- PCB helpers
LAYERS_6 = [(0, "F.Cu", "signal"), (1, "In1.Cu", "power"), (2, "In2.Cu", "signal"),
            (3, "In3.Cu", "signal"), (4, "In4.Cu", "power"), (31, "B.Cu", "signal")]
LAYERS_2 = [(0, "F.Cu", "signal"), (31, "B.Cu", "signal")]
USER_LAYERS = [(32, "B.Adhes", "user", "B.Adhesive"), (33, "F.Adhes", "user", "F.Adhesive"),
               (34, "B.Paste", "user"), (35, "F.Paste", "user"),
               (36, "B.SilkS", "user", "B.Silkscreen"), (37, "F.SilkS", "user", "F.Silkscreen"),
               (38, "B.Mask", "user"), (39, "F.Mask", "user"),
               (40, "Dwgs.User", "user", "User.Drawings"), (41, "Cmts.User", "user", "User.Comments"),
               (42, "Eco1.User", "user", "User.Eco1"), (43, "Eco2.User", "user", "User.Eco2"),
               (44, "Edge.Cuts", "user"), (45, "Margin", "user"),
               (46, "B.CrtYd", "user", "B.Courtyard"), (47, "F.CrtYd", "user", "F.Courtyard"),
               (48, "B.Fab", "user"), (49, "F.Fab", "user")]


def pcb_header(copper, nets=None):
    out = ["(kicad_pcb (version 20240108) (generator \"pcbnew\") (generator_version \"8.0\")\n",
           "  (general (thickness 1.6) (legacy_teardrops no))\n",
           "  (paper \"A3\")\n  (layers\n"]
    for l in copper + USER_LAYERS:
        out.append("    (%d %s %s%s)\n" % (l[0], q(l[1]), l[2], (" " + q(l[3])) if len(l) > 3 else ""))
    out.append("  )\n  (setup (pad_to_mask_clearance 0) (allow_soldermask_bridges_in_footprints no))\n")
    out.append("  (net 0 \"\")\n")
    for i, n in enumerate(nets or []):
        out.append("  (net %d %s)\n" % (i + 1, q(n)))
    return out


def gr_rect(x1, y1, x2, y2, layer, width=0.1):
    return ("  (gr_rect (start %.3f %.3f) (end %.3f %.3f) (stroke (width %.2f) (type default))"
            " (fill none) (layer %s) (uuid %s))\n" % (x1, y1, x2, y2, width, q(layer), q(U())))


def gr_text(t, x, y, layer="Dwgs.User", size=1.5):
    return ("  (gr_text %s (at %.3f %.3f 0) (layer %s) (uuid %s)\n"
            "    (effects (font (size %.2f %.2f) (thickness %.2f))))\n"
            % (q(t), x, y, q(layer), q(U()), size, size, size * 0.15))


def outline_rounded(w, h, r):
    """Board outline with radius-r corners on Edge.Cuts."""
    s = []
    lines = [((r, 0), (w - r, 0)), ((w, r), (w, h - r)), ((w - r, h), (r, h)), ((0, h - r), (0, r))]
    for (a, b) in lines:
        s.append("  (gr_line (start %.3f %.3f) (end %.3f %.3f) (stroke (width 0.1) (type default))"
                 " (layer \"Edge.Cuts\") (uuid %s))\n" % (a[0], a[1], b[0], b[1], q(U())))
    import math
    corners = [((r, r), 180), ((w - r, r), 270), ((w - r, h - r), 0), ((r, h - r), 90)]
    for (cx, cy), ang in corners:
        a0, a1 = math.radians(ang), math.radians(ang + 90)
        am = (a0 + a1) / 2
        p = lambda a: (cx + r * math.cos(a), cy + r * math.sin(a))
        s0, m, e = p(a0), p(am), p(a1)
        s.append("  (gr_arc (start %.4f %.4f) (mid %.4f %.4f) (end %.4f %.4f) (stroke (width 0.1) (type default))"
                 " (layer \"Edge.Cuts\") (uuid %s))\n" % (s0[0], s0[1], m[0], m[1], e[0], e[1], q(U())))
    return s


def hole(ref, x, y, d=2.7, value="M2.5"):
    return ("  (footprint \"MountingHole:MountingHole_%.1fmm\" (layer \"F.Cu\") (uuid %s) (at %.3f %.3f)\n"
            "    (property \"Reference\" %s (at 0 %.2f 0) (layer \"F.SilkS\") (uuid %s) (effects (font (size 1 1) (thickness 0.15))))\n"
            "    (property \"Value\" %s (at 0 %.2f 0) (layer \"F.Fab\") (uuid %s) (effects (font (size 1 1) (thickness 0.15))))\n"
            "    (attr exclude_from_pos_files exclude_from_bom)\n"
            "    (fp_circle (center 0 0) (end %.3f 0) (stroke (width 0.05) (type solid)) (fill none) (layer \"F.CrtYd\") (uuid %s))\n"
            "    (pad \"\" np_thru_hole circle (at 0 0) (size %.2f %.2f) (drill %.2f) (layers \"*.Cu\" \"*.Mask\") (uuid %s)))\n"
            % (d, q(U()), x, y, q(ref), -d / 2 - 1.5, q(U()), q(value), d / 2 + 1.5, q(U()),
               d / 2 + 0.5, q(U()), d, d, d, q(U())))


# ================================================================ MAINBOARD
def mainboard():
    folder = os.path.join(OUT, "mainboard")
    os.makedirs(folder, exist_ok=True)
    proj = "kurogane_mainboard"
    write_pro(os.path.join(folder, proj + ".kicad_pro"), proj, [
        ("Default", 0.15, 0.15, 0.1, 0.2),
        ("USB3_90R", 0.15, 0.15, 0.127, 0.15),   # set width/gap from your fab's impedance calculator
        ("PCIe_85R", 0.15, 0.15, 0.127, 0.15),
        ("MIPI_100R", 0.15, 0.15, 0.1, 0.18),
        ("USB2_90R", 0.15, 0.15, 0.15, 0.15),
        ("PWR_5V", 0.2, 1.0, 0.2, 0.2),
        ("PWR_VSYS", 0.2, 1.0, 0.2, 0.2),
    ])
    sheets = [
        ("CM5_Connectors", "cm5_connectors.kicad_sch", [
            "2 x 100-pin 0.4 mm receptacles: Hirose DF40HC(3.0)-100DS-0.4V(51) or Amphenol 10164227-1004A1RLF.",
            "START HERE: copy the CM5 connector symbols/footprints and pin naming from the official",
            "CM5 IO Board KiCad files (pip.raspberrypi.com, 'CM5 IO Board, revision 2, KiCAD files').",
            "Expose as hierarchical labels: USB3_0, USB3_1, USB2, PCIE, MIPI0, MIPI1, HDMI0, ETH,",
            "I2C1 (GPIO2/3), I2S (GPIO18-21), UART2, UART3, GPIO40 header, FAN_PWM/TACH, RTC_VBAT,",
            "PWR_BUT, nRPIBOOT, GLOBAL_EN, VIN 5V (6 A path), 3V3/1V8 outputs.",
            "Wi-Fi antenna: CM5 U.FL -> SMA pigtail (no PCB routing).",
        ]),
        ("Power", "power.kicad_sch", [
            "USB-C sink: CH224K requests 12 V (fallback 9 V/5 V) -> BQ25792 VAC1.",
            "DeckBus VCHG_IN L/R -> LM66100 x2 (OR-ing) -> BQ25792 VAC2.",
            "BQ25792 (2S, VREG 8.4 V, ICHG 3 A, NVDC) SYS -> net VSYS. TS <- pack NTC.",
            "LTC2944 coulomb counter, 10 mOhm high-side shunt in BAT+ (I2C1, addr 0x64).",
            "Buck A TPS566238 -> +5V_A 6 A (CM5 VIN, display). EN <- hard-kill switch.",
            "Buck B TPS566238 -> +5V_B 6 A (USB VBUS switches, DeckBus 5 V, keyboard).",
            "Buck C TPS566238 -> +3V3_P 6 A (M.2 B/M, codec, DeckBus 3V3).",
            "Put 0R links on each rail output for staged bring-up; test points on every PG.",
            "Battery connector: 6-pin (BAT+ x2, BAT- x2, NTC, BAL_MID) to pack board DM-BP.",
        ]),
        ("USB_Hubs", "usb_hubs.kicad_sch", [
            "USB3_0 -> VL817 (4 ports): P1 M.2 B-key modem, P2 rear USB-A, P3 left USB-A, P4 internal USB-C.",
            "USB3_1 -> right USB-C host port (5 Gb/s), VBUS 1.5 A via current-limit switch.",
            "USB2 -> TS3USB221 mux: SEL=nRPIBOOT switch. A: USB2514B hub, B: charge-port USB-C D+/D-.",
            "USB2514B: P1 keyboard (FPC), P2 DeckBus L, P3 DeckBus R, P4 internal header.",
            "Per-port VBUS current-limit switches from +5V_B; ESD arrays at every external connector.",
        ]),
        ("Storage_Modem", "storage_modem.kicad_sch", [
            "M.2 M-key 2230/2242 NVMe on PCIE (Gen 2 x1), 3.3 V from +3V3_P, PERST#, CLKREQ#.",
            "M.2 B-key 3042/3052 (USB3 + USB2 from VL817 P1), nano-SIM push-push holder,",
            "W_DISABLE#, FULL_CARD_POWER_OFF# on GPIO, RESET#; 3.3 V bulk 470 uF for TX bursts.",
            "Antennas from the modem by U.FL pigtails (MAIN, DIV, GNSS) to the top SMA panel.",
        ]),
        ("Display_Camera", "display_camera.kicad_sch", [
            "MIPI1 4-lane -> 22-pin 0.5 mm DSI FPC for Raspberry Pi Touch Display 2 (I2C for touch on the FPC).",
            "Display 5 V from +5V_A via 2-pin JST-GH.",
            "MIPI0 4-lane -> 22-pin CSI FPC (optional camera).",
            "Length-match lanes to the clock pair; 100 ohm differential.",
        ]),
        ("Audio", "audio.kicad_sch", [
            "WM8960 on I2S (GPIO18 BCLK, 19 LRCLK, 20 DIN, 21 DOUT) + I2C1 (0x1A).",
            "Class-D speaker outs -> 2 x 1 W 8 ohm speakers (JST-SH 2-pin).",
            "Headphone out + mic in -> 3.5 mm TRRS jack with jack-detect to GPIO.",
            "Own analog ground pour; keep away from Buck A/B inductors.",
        ]),
        ("IO_Ports", "io_ports.kicad_sch", [
            "Gigabit Ethernet: CM5 ETH pairs -> RJ45 with integrated magnetics (HR911105A class), LEDs.",
            "HDMI0 -> full-size HDMI type A, TPD12S016-class ESD/level shifter, 5 V 55 mA.",
            "Charge-port USB-C (CC to CH224K, D+/D- to mux), host USB-C (USB3_1), USB-A x2 from VL817.",
            "Side switches: BOOT (nRPIBOOT), hard-kill (Buck A EN). Fan header 4-pin. RTC ML2032 holder.",
            "Status LEDs on the top IO board via 10-pin FPC.",
        ]),
        ("DeckBus", "deckbus.kicad_sch", [
            "Two bays, identical. 2x10 pogo block per bay, pinout in docs/deckbus_v1.md.",
            "Per bay: TPS25947 eFuse on VSYS (2 A), TPS22965 on +5V_B (2 A), 3V3 via 300 mA limit,",
            "USB2 from USB2514B, I2C via PCA9546A channel (bay L = ch0, bay R = ch1), UART2 (L) / UART3 (R),",
            "GPIO A/B, MOD_DET# with 200 ms RC + Schmitt to eFuse/load-switch EN and to a CM5 GPIO.",
            "VCHG_IN -> LM66100 ideal diode -> BQ25792 VAC2 (in Power sheet).",
            "TVS on every pogo pin; 0R in series on data lines for hot-plug tuning.",
        ]),
        ("Keyboard_GPIO", "keyboard_gpio.kicad_sch", [
            "Keyboard link: 10-pin 0.5 mm FPC: +5V_B x2, GND x3, USB D+/D-, PWR_KEY (-> CM5 PWR_BUT), spare x2.",
            "40-pin HAT header (internal bay) with ID EEPROM pins; mark 5 V current limit on silk.",
            "Spare GPIOs to test pads.",
        ]),
    ]
    intro = [
        "Kurogane K-7 mainboard rev A: CM5 carrier, 6 layers (L1 sig / L2 GND / L3 sig+pwr / L4 pwr / L5 GND / L6 sig).",
        "Board 190 x 105 mm sits behind the 7 in display. Placement zones are on Dwgs.User in the PCB.",
        "Each sheet below lists what goes in it. Copy proven blocks from the CM5 IO Board reference design.",
        "Net map: docs/cm5_signal_map.csv. Power design: build plan doc, 'Power system'.",
    ]
    write_root_sch(folder, proj, "Kurogane K-7 mainboard (CM5 carrier)", sheets, intro)

    W, H = 190.0, 105.0
    s = pcb_header(LAYERS_6)
    s += outline_rounded(W, H, 4.0)
    for i, (x, y) in enumerate([(4, 4), (W - 4, 4), (4, H - 4), (W - 4, H - 4), (W / 2, 4), (W / 2, H - 4)]):
        s.append(hole("H%d" % (i + 1), x, y))
    zones = [
        ("CM5 module 55 x 40 (place connectors from CM5IO footprint)", 68, 30, 123, 70),
        ("Power: CH224K, BQ25792, 3x buck, LTC2944", 8, 12, 60, 50),
        ("Battery + NTC connector", 8, 54, 40, 66),
        ("VL817 + USB2514B + mux", 130, 12, 170, 36),
        ("M.2 B-key 3042 + SIM (bottom side)", 128, 40, 182, 72),
        ("M.2 M-key 2242 (bottom side)", 68, 74, 125, 96),
        ("DSI FPC (to display)", 75, 8, 115, 16),
        ("CSI FPC", 120, 8, 128, 26),
        ("WM8960 audio", 8, 70, 40, 92),
        ("Left edge: USB-C charge, USB-A, jack, RJ45", 0, 20, 6, 90),
        ("Right edge: USB-C host, HDMI, switches", 184, 20, 190, 80),
        ("DeckBus L pogo + eFuse", 42, 74, 64, 100),
        ("DeckBus R pogo + eFuse", 130, 76, 182, 100),
        ("HAT 40-pin header zone", 140, 40, 182, 46),
    ]
    for label, x1, y1, x2, y2 in zones:
        s.append(gr_rect(x1, y1, x2, y2, "Dwgs.User", 0.15))
        s.append(gr_text(label, x1 + 1, y1 + 2.0 if y2 - y1 > 6 else y1 - 1.5, "Dwgs.User", 1.0))
    s.append(gr_text("Kurogane K-7 mainboard rev A - zones are guides, not final placement", 2, -4, "Cmts.User", 1.5))
    s.append(")\n")
    with open(os.path.join(folder, proj + ".kicad_pcb"), "w") as f:
        f.write("".join(s))


# ================================================================ KEYBOARD
KEY_ROWS = [
    ["Esc", "1", "2", "3", "4", "5", "6", "7", "8", "9", "0", "-", "Bksp"],
    ["Tab", "Q", "W", "E", "R", "T", "Y", "U", "I", "O", "P", "[", "]"],
    ["Ctrl", "A", "S", "D", "F", "G", "H", "J", "K", "L", ";", "'", "Enter"],
    ["Shift", "Z", "X", "C", "V", "B", "N", "M", ",", ".", "/", "Up", "Shift"],
    ["Fn", "Ctrl", "Alt", "Super", "Space", "Alt", "Left", "Down", "Right"],
]
SPANS = {(4, 4): 5}  # row 4, index 4 (Space) spans 5 columns


def keyboard():
    folder = os.path.join(OUT, "keyboard")
    os.makedirs(folder, exist_ok=True)
    proj = "kurogane_input"
    write_pro(os.path.join(folder, proj + ".kicad_pro"), proj, [
        ("Default", 0.15, 0.2, 0.15, 0.15), ("USB2_90R", 0.15, 0.2, 0.2, 0.15), ("PWR", 0.2, 0.5, 0.2, 0.2)])
    sheets = [
        ("RP2040_Core", "rp2040_core.kicad_sch", [
            "RP2040 + W25Q16JV flash + 12 MHz crystal + 1V1 internal LDO; BOOTSEL via Esc key at plug-in (QMK) + test pad.",
            "USB from mainboard FPC (D+/D- 27 ohm series), 5 V -> AP2112K-3.3 LDO.",
            "SWD on test pads for recovery.",
        ]),
        ("Matrix", "matrix.kicad_sch", [
            "6 rows x 13 cols matrix with 1N4148W (SOD-123) per switch, COL2ROW.",
            "Rows 0-4 = keyboard (61 keys, see key_positions.csv). Row 5 = gamepad: Up, Down, Left, Right, L, R,",
            "Select, Start, X, Y, A, B, Mouse1, Mouse2, Mouse3 (15 on 13 cols: put Mouse2/3 on spare GPIO direct pins).",
            "Switches: low-profile SMD tactile (5.2 x 5.2 mm class); caps are printed/silicone.",
            "Power key: separate GPIO-free line to FPC -> CM5 PWR_BUT (works when RP2040 is off).",
        ]),
        ("Trackball_IO", "trackball_io.kicad_sch", [
            "Pimoroni PIM447 trackball on RP2040 I2C1 (GP2 SDA / GP3 SCL), 100-250 kHz, INT to a spare GPIO.",
            "Optional: backlight LED driver, Caps/Fn LED.",
            "10-pin FPC to mainboard: +5V x2, GND x3, D+, D-, PWR_KEY, spare x2.",
        ]),
    ]
    write_root_sch(folder, proj, "Kurogane K-7 input board (keyboard + gamepad)", sheets,
                   ["2-layer, 196 x 112 mm. Top 36 mm = gamepad strip, lower 72 mm = 5-row keyboard.",
                    "Key positions are on Dwgs.User and in key_positions.csv; drop your switch footprint on each.",
                    "Firmware: QMK, rp2040 platform, pointing device driver pimoroni_trackball."])

    W, H = 196.0, 112.0
    s = pcb_header(LAYERS_2)
    s += outline_rounded(W, H, 3.0)
    for i, (x, y) in enumerate([(3.5, 3.5), (W - 3.5, 3.5), (3.5, H - 3.5), (W - 3.5, H - 3.5)]):
        s.append(hole("H%d" % (i + 1), x, y))
    rows_csv = []
    pitch_x, pitch_y = 14.6, 13.6
    x0, y0 = (W - 13 * pitch_x) / 2, 38.0
    for r, row in enumerate(KEY_ROWS):
        col = 0
        for i, label in enumerate(row):
            span = SPANS.get((r, i), 1)
            cx = x0 + (col + span / 2.0) * pitch_x
            cy = y0 + (r + 0.5) * pitch_y
            s.append(gr_rect(cx - span * pitch_x / 2 + 0.6, cy - pitch_y / 2 + 0.6,
                             cx + span * pitch_x / 2 - 0.6, cy + pitch_y / 2 - 0.6, "Dwgs.User", 0.1))
            s.append(gr_text(label, cx, cy, "Dwgs.User", 1.2))
            rows_csv.append([label, round(cx, 3), round(cy, 3), r, col, span])
            col += span
    pad = [("Up", 22, 8), ("Down", 22, 24), ("Left", 14, 16), ("Right", 30, 16),
           ("L", 48, 10), ("R", 56, 22), ("Mouse1", 86, 30), ("Mouse2", 98, 30), ("Mouse3", 110, 30),
           ("Select", 132, 12), ("Start", 132, 22),
           ("X", 170, 6), ("Y", 160, 16), ("A", 180, 16), ("B", 170, 26)]
    for i, (label, x, y) in enumerate(pad):
        s.append(gr_rect(x - 4, y - 4, x + 4, y + 4, "Dwgs.User", 0.1))
        s.append(gr_text(label, x, y, "Dwgs.User", 1.0))
        rows_csv.append([label, x, y, 5, i, 1])
    s.append(gr_rect(86, 4, 110, 26, "Dwgs.User", 0.15))
    s.append(gr_text("PIM447 trackball 25 x 22", 98, 15, "Dwgs.User", 1.0))
    s.append(gr_rect(150, 90, 170, 104, "Dwgs.User", 0.15))
    s.append(gr_text("RP2040 + flash (bottom side)", 160, 97, "Dwgs.User", 1.0))
    s.append(gr_rect(84, 106.5, 112, 111, "Dwgs.User", 0.15))
    s.append(gr_text("10-pin FPC to mainboard", 98, 108.8, "Dwgs.User", 1.0))
    s.append(")\n")
    with open(os.path.join(folder, proj + ".kicad_pcb"), "w") as f:
        f.write("".join(s))
    with open(os.path.join(folder, "key_positions.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["label", "x_mm", "y_mm", "matrix_row", "matrix_col_or_index", "span_cols"])
        w.writerows(rows_csv)


# ================================================================ DECKBUS MODULE
DECKBUS_PINS = ["GND", "GND", "VSYS", "VSYS", "+5V", "+5V", "+3V3", "GND", "USB_DP", "USB_DN",
                "GND", "I2C_SDA", "I2C_SCL", "UART_TX", "UART_RX", "GPIO_A", "GPIO_B", "MOD_DET#",
                "VCHG_IN", "GND"]


def deckbus_module():
    folder = os.path.join(OUT, "deckbus_module")
    os.makedirs(folder, exist_ok=True)
    proj = "kurogane_module"
    write_pro(os.path.join(folder, proj + ".kicad_pro"), proj, [
        ("Default", 0.15, 0.2, 0.15, 0.15), ("USB2_90R", 0.15, 0.2, 0.2, 0.15), ("PWR", 0.2, 0.6, 0.2, 0.2)])
    write_root_sch(folder, proj, "DeckBus v1 module template", [
        ("Contacts_ID", "contacts_id.kicad_sch", [
            "J1 = 20 gold pads (footprint already placed in PCB with nets).",
            "24C32 EEPROM on I2C at 0x50: vendor, product, version, overlay name (deckbusd reads it).",
            "Tie MOD_DET# to GND on the module. 10 uF on +5V and VSYS near the pads, TVS on USB.",
            "Never back-feed VSYS/+5V/+3V3. Battery/solar modules output only on VCHG_IN (5-12 V).",
        ]),
        ("Payload", "payload.kicad_sch", ["Your module circuit: GNSS, LoRa, SDR, sensors, battery..."]),
    ], ["Module PCB 28 x 100 mm, 2-layer, ENIG (gold pads). Sled: enclosure/kurogane_k7.scad module_sled()."])

    W, H = 28.0, 100.0
    nets = sorted(set(DECKBUS_PINS))
    netnum = {n: i + 1 for i, n in enumerate(nets)}
    s = pcb_header(LAYERS_2, nets)
    s += outline_rounded(W, H, 2.0)
    s.append(hole("H1", W / 2, 6, 3.2, "M3"))
    s.append(hole("H2", W / 2, H - 6, 3.2, "M3"))
    # 2 x 10 pads, 2.54 mm pitch, centred; odd pins left column, even right
    px, py = 2.54, 2.54
    cx, cy = W / 2, H / 2
    fp = ["  (footprint \"DeckBus:DeckBus_v1_Pads_2x10_P2.54mm\" (layer \"B.Cu\") (uuid %s) (at %.3f %.3f)\n" % (q(U()), cx, cy),
          "    (property \"Reference\" \"J1\" (at 0 -15 0) (layer \"B.SilkS\") (uuid %s) (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))\n" % q(U()),
          "    (property \"Value\" \"DeckBus_v1\" (at 0 15 0) (layer \"B.Fab\") (uuid %s) (effects (font (size 1 1) (thickness 0.15)) (justify mirror)))\n" % q(U()),
          "    (attr smd)\n"]
    for i, net in enumerate(DECKBUS_PINS):
        n = i + 1
        r, c = i // 2, i % 2
        x = (c - 0.5) * px
        y = (r - 4.5) * py
        fp.append("    (pad %s smd roundrect (at %.3f %.3f) (size 1.8 1.8) (layers \"B.Cu\" \"B.Mask\") (roundrect_rratio 0.15)"
                  " (net %d %s) (uuid %s))\n" % (q(str(n)), x, y, netnum[net], q(net), q(U())))
    fp.append("    (fp_rect (start -3 -13.5) (end 3 13.5) (stroke (width 0.05) (type solid)) (fill none) (layer \"B.CrtYd\") (uuid %s))\n" % q(U()))
    fp.append("  )\n")
    s += fp
    s.append(gr_text("DeckBus v1 - pads on bottom (inner face), pin 1 = top-left", W / 2, 14, "Cmts.User", 1.0))
    s.append(gr_rect(2, 16, 26, 36, "Dwgs.User", 0.1))
    s.append(gr_text("EEPROM + protection", 14, 26, "Dwgs.User", 1.0))
    s.append(gr_rect(2, 64, 26, 92, "Dwgs.User", 0.1))
    s.append(gr_text("Payload area / SMA edge", 14, 78, "Dwgs.User", 1.0))
    s.append(")\n")
    with open(os.path.join(folder, proj + ".kicad_pcb"), "w") as f:
        f.write("".join(s))


if __name__ == "__main__":
    mainboard()
    keyboard()
    deckbus_module()
    print("KiCad skeletons written to", OUT)
