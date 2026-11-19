#!/usr/bin/env python3
"""Render the animated README media for Kurogane K-7.

Outputs (in mockup/renders/):
  kurogane-hero.gif      front view: antennas extend, modules slide in, terminal boots
  kurogane-exploded.gif  isometric stack separating and closing
  kurogane-hero.png      still of the assembled front view
  kurogane-exploded.png  still of the exploded view

Needs: rsvg-convert (librsvg) and ffmpeg on PATH. Fonts: DejaVu Sans / Sans Mono.
Run from the repo root:  python3 tools/render_readme_media.py
"""
import math
import os
import shutil
import subprocess
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "mockup", "renders")
FPS = 12
SANS = "DejaVu Sans, Arial, sans-serif"
MONO = "DejaVu Sans Mono, Consolas, monospace"
ORANGE = "#ff8a1f"


def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def ease(v):
    v = clamp(v)
    return v * v * (3 - 2 * v)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def rect(x, y, w, h, fill, rx=0, extra=""):
    return f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{fill}" {extra}/>'


def text(x, y, s, size, fill, anchor="start", weight="400", family=SANS, extra=""):
    return (f'<text x="{x:.2f}" y="{y:.2f}" font-family="{family}" font-size="{size}" fill="{fill}" '
            f'text-anchor="{anchor}" font-weight="{weight}" {extra}>{esc(s)}</text>')


DEFS = """
<defs>
  <linearGradient id="alu" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#d3d6da"/><stop offset="0.45" stop-color="#a3a8ae"/>
    <stop offset="0.6" stop-color="#dfe2e5"/><stop offset="1" stop-color="#949aa1"/>
  </linearGradient>
  <linearGradient id="aluv" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#a7acb2"/><stop offset="1" stop-color="#7d828a"/>
  </linearGradient>
  <linearGradient id="cell" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#3aa5c8"/><stop offset="0.55" stop-color="#1d6f8c"/><stop offset="1" stop-color="#0f4a5e"/>
  </linearGradient>
  <linearGradient id="glass" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#0a3d47"/><stop offset="1" stop-color="#04161b"/>
  </linearGradient>
  <linearGradient id="silver" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="#e6e9ec"/><stop offset="1" stop-color="#9aa0a7"/>
  </linearGradient>
  <radialGradient id="ball" cx="0.35" cy="0.35" r="0.7">
    <stop offset="0" stop-color="#ffffff"/><stop offset="0.45" stop-color="#d9dce0"/><stop offset="1" stop-color="#8d939a"/>
  </radialGradient>
  <radialGradient id="bg" cx="0.5" cy="0.4" r="0.75">
    <stop offset="0" stop-color="#23262b"/><stop offset="1" stop-color="#0e0f11"/>
  </radialGradient>
</defs>"""

# ===================================================================== HERO
KEYS = [
    [("Esc", ""), ("1", "F1"), ("2", "F2"), ("3", "F3"), ("4", "F4"), ("5", "F5"), ("6", "F6"), ("7", "F7"), ("8", "F8"), ("9", "F9"), ("0", "F10"), ("-", "F11"), ("Bksp", "Del")],
    [("Tab", ""), ("Q", ""), ("W", ""), ("E", ""), ("R", ""), ("T", ""), ("Y", ""), ("U", "PgUp"), ("I", "Ins"), ("O", ""), ("P", ""), ("[", "{"), ("]", "}")],
    [("Ctrl", "Caps"), ("A", ""), ("S", ""), ("D", ""), ("F", ""), ("G", ""), ("H", "Home"), ("J", "End"), ("K", "PgDn"), ("L", ""), (";", ":"), ("'", '"'), ("Enter", "")],
    [("Shift", ""), ("Z", ""), ("X", ""), ("C", ""), ("V", ""), ("B", ""), ("N", ""), ("M", ""), (",", "<"), (".", ">"), ("/", "?"), ("↑", ""), ("Shift", "")],
    [("Fn", ""), ("Ctrl", ""), ("Alt", ""), ("Sup", ""), ("", "", 5), ("Alt", ""), ("←", ""), ("↓", ""), ("→", "")],
]

TERM = [
    ("$ deckbus status", True),
    ("bay L  gnss-lora   v1.2  ok", False),
    ("bay R  rtl-sdr-v4  v1.0  ok", False),
    ("$ gpspipe -w | head -1", True),
    ("fix 3D  sats 14  hdop 0.8", False),
    ("$ meshtastic --nodes", True),
    ("4 nodes heard, snr +6.5", False),
    ("$ battery", True),
    ("87%  7.71 V  -1.31 A  4h05m", False),
]


def hero_frame(t, T):
    BX, BY, BW, BH = 162, 230, 636, 756
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="720" height="952" viewBox="30 0 900 1190">', DEFS,
           rect(30, 0, 900, 1190, "url(#bg)")]

    # timeline
    ant = ease((t - 0.0) / 0.8) * (1 - ease((t - (T - 1.0)) / 0.7))
    mod_in = ease((t - 0.6) / 0.9)
    mod_out = ease((t - (T - 1.3)) / 0.7)
    mod = mod_in * (1 - mod_out)
    power = ease((t - 0.9) / 0.4) * (1 - ease((t - (T - 0.6)) / 0.4))
    typing_t = t - 1.4
    clear = t > T - 1.2

    # ---- antennas (behind body), base at y=230
    base = BY
    whips = [(BX + 85, 40), (BX + 185, 16), (BX + 285, 4), (BX + 385, 16), (BX + 485, 52)]
    for x, top0 in whips:
        top = base - (base - top0) * ant
        h = base - top
        if h < 16:
            out.append(rect(x - 9, base - 14, 18, 14, "#6d7178", 2))
            continue
        sleeve = min(52, h * 0.3)
        cap = min(74, h * 0.42)
        out.append(rect(x - 2, top + cap - 2, 4, max(0, h - cap - sleeve), "#141516"))
        out.append(rect(x - 9, top, 18, cap, "#141516", 9))
        out.append(rect(x - 8, base - 14 - sleeve, 16, sleeve, "#141516", 6))
        out.append(rect(x - 9, base - 14, 18, 14, "#6d7178", 2))
    puck_h = 90 * ant
    out.append(rect(BX + 551, base - max(puck_h, 6), 56, max(puck_h, 6), "#141516", 12))

    # ---- side modules (slide on rails)
    off = 150 * (1 - mod)
    for side in ("L", "R"):
        if side == "L":
            mx, label, led_x = 56 - off, "GNSS + LORA", 106 - off
            out.append(rect(mx + 43, 372, 16, 96, "#141516", 8))  # stubby LoRa antenna
            out.append(rect(mx + 42, 466, 18, 14, "#6d7178", 2))
        else:
            mx, label, led_x = 802 + off, "RTL-SDR", 852 + off
            out.append(rect(mx + 49, 292, 4, 176, "#141516"))
            out.append(f'<circle cx="{mx + 51}" cy="290" r="5" fill="#141516"/>')
            out.append(rect(mx + 42, 466, 18, 14, "#6d7178", 2))
        out.append(rect(mx, 480, 100, 330, "url(#alu)", 16, 'stroke="#7d828a" stroke-width="2"'))
        stripe_x = mx + 94 if side == "L" else mx
        out.append(rect(stripe_x, 486, 6, 318, ORANGE, 2))
        out.append(rect(mx + 23, 502, 54, 54, "none", 10, 'stroke="#5a5e64" stroke-width="2"'))
        out.append(text(mx + 50, 534, "GNSS" if side == "L" else "SDR", 11, ORANGE, "middle", "700"))
        cx, cy = mx + 50, 650
        rot = -90 if side == "L" else 90
        out.append(f'<text x="{cx}" y="{cy}" font-family="{SANS}" font-size="13" fill="#141516" '
                   f'text-anchor="middle" letter-spacing="3" transform="rotate({rot} {cx} {cy})">{esc(label)}</text>')
        led = "#38d39f" if (mod_in > 0.97 and mod_out < 0.05) else "#3a3e43"
        out.append(f'<circle cx="{led_x}" cy="782" r="5" fill="{led}"/>')

    # ---- side ports
    for (x, y, w, h, c) in [(154, 262, 10, 18, "#2a2c2f"), (154, 296, 10, 26, "#2a2c2f"), (154, 338, 10, 12, "#2a2c2f"),
                            (154, 366, 10, 40, "#2a2c2f"), (796, 262, 10, 18, "#2a2c2f"), (796, 296, 10, 44, "#2a2c2f"),
                            (796, 360, 10, 22, ORANGE)]:
        out.append(rect(x, y, w, h, c, 2))

    # ---- battery grip
    out.append(rect(210, 960, 540, 114, "url(#aluv)", 26))
    out.append(text(480, 1052, "BATTERY GRIP · 2S2P · 43 WH", 12, "#141516", "middle", "700", extra='letter-spacing="2"'))

    # ---- body
    out.append(f'<g transform="translate({BX},{BY})">')
    out.append(rect(0, 0, BW, BH, "url(#alu)", 22, 'stroke="#7d828a" stroke-width="3"'))
    # crown window onto the antenna PCB
    out.append(rect(24, 8, 588, 32, "#0f1011", 6, 'stroke="#5a5e64" stroke-width="2"'))
    out.append('<g fill="none" stroke="#d4a64a" stroke-opacity="0.55" stroke-width="1">'
               '<path d="M34 30H144V18H224M34 34H154V22H284M324 16V30H444M464 30H604M354 34H584V20"/></g>')
    for sx in (85, 185, 285, 385, 485, 579):
        out.append(f'<circle cx="{sx}" cy="24" r="5" fill="#d4a64a"/>')
    blink = 1 if int(t * 2) % 2 == 0 else 0.25
    out.append(f'<circle cx="234" cy="24" r="2.5" fill="#38d39f" opacity="{0.3 + 0.7 * power}"/>')
    out.append(f'<circle cx="246" cy="24" r="2.5" fill="#38d39f" opacity="{blink * power:.2f}"/>')
    out.append(f'<circle cx="258" cy="24" r="2.5" fill="{ORANGE}" opacity="{0.3 + 0.7 * power}"/>')
    for (lx, lab) in ((85, "WIFI"), (185, "LTE M"), (285, "LTE D"), (385, "AUX 1"), (485, "AUX 2"), (579, "GNSS")):
        out.append(text(lx, 52, lab, 9, ORANGE, "middle", "700", extra='letter-spacing="1"'))
    # torx screws
    for (sx, sy) in ((20, 20), (616, 20), (20, 736), (616, 736)):
        out.append(f'<circle cx="{sx}" cy="{sy}" r="8" fill="#8d939a"/><circle cx="{sx}" cy="{sy}" r="3.5" fill="#2a2c2f"/>')
    # bezel + screen
    out.append(rect(20, 58, 596, 346, "#0b0c0d", 16, 'stroke="#2c2f33" stroke-width="2"'))
    for gx in (42, 594):
        for j in range(5):
            for k in (0, 1):
                out.append(f'<circle cx="{gx - 5 + 10 * k}" cy="{198 + 11 * j}" r="2.5" fill="#2c2f33"/>')
    out.append(rect(86, 100, 464, 261, "#020607", 3))
    if power > 0.01:
        out.append(f'<g opacity="{power:.2f}">')
        out.append(rect(86, 100, 464, 261, "#04161b", 3))
        out.append(rect(86, 100, 464, 20, "#0a2a31"))
        out.append(text(96, 114, "kurogane · cm5 · 2.4 GHz · 48 °C", 10, "#bff6fb", family=MONO))
        out.append(text(540, 114, "LTE ▂▄▆  87%  14:42", 10, "#bff6fb", "end", family=MONO))
        out.append(rect(379, 120, 1, 241, "#0f3b44"))
        # terminal typing
        if not clear and typing_t > 0:
            budget = int(typing_t * 38)
            y = 138
            for line, prompt in TERM:
                if budget <= 0:
                    break
                shown = line[:budget]
                budget -= len(line) + 4
                out.append(text(98, y, shown, 10.5, "#ffb066" if prompt else "#7fe7f2", family=MONO))
                y += 16
            if budget > 0 and blink > 0.5:
                out.append(text(98, y, "$ █", 10.5, "#ffb066", family=MONO))
        elif blink > 0.5:
            out.append(text(98, 138, "$ █", 10.5, "#ffb066", family=MONO))
        # SDR panel
        out.append(text(390, 136, "SDR 433.92 MHz", 10, "#bff6fb", family=MONO))
        for i in range(24):
            h = 14 + 30 * abs(math.sin(t * 3.1 + i * 0.55)) * (1.6 if 8 < i < 14 else 0.8) * mod
            out.append(rect(390 + i * 6.4, 224 - h, 5, h, "#2fc6d6"))
        out.append(rect(390, 224, 152, 1, "#0f3b44"))
        for r in range(14):
            shade = 0.15 + 0.6 * abs(math.sin(r * 0.9 + t * 2.4)) * mod
            out.append(rect(390, 230 + r * 9, 152, 8, "#2fc6d6", 1, f'opacity="{shade:.2f}"'))
        out.append('</g>')
    out.append(text(318, 386, "KUROGANE · K-7  ·  KAGE SECURITY LAB", 10, "#5a5e64", "middle", "700", extra='letter-spacing="4"'))

    # gamepad strip
    g = '<g transform="translate(20,412)">'
    g += rect(52, 12, 28, 88, "#101112", 6) + rect(22, 42, 88, 28, "#101112", 6)
    g += f'<circle cx="152" cy="40" r="22" fill="#101112"/>' + text(152, 46, "L", 15, "#e8e8e8", "middle", "700")
    g += f'<circle cx="182" cy="80" r="22" fill="#101112"/>' + text(182, 86, "R", 15, "#e8e8e8", "middle", "700")
    g += rect(258, 6, 80, 64, "#101112", 18)
    pulse = 0.55 + 0.45 * math.sin(t * 4)
    g += f'<circle cx="298" cy="38" r="20" fill="none" stroke="{ORANGE}" stroke-width="3" opacity="{pulse:.2f}"/>'
    g += '<circle cx="298" cy="38" r="17" fill="url(#ball)"/>'
    for i in range(3):
        g += rect(246 + 37 * i, 80, 30, 16, "#101112", 4)
    g += rect(380, 34, 52, 16, "#101112", 8) + text(406, 45, "SELECT", 8, "#8a8f96", "middle")
    g += rect(380, 58, 52, 16, "#101112", 8) + text(406, 69, "START", 8, "#8a8f96", "middle")
    for (bx, by, bl) in ((520, 22, "X"), (486, 56, "Y"), (554, 56, "A"), (520, 90, "B")):
        g += f'<circle cx="{bx}" cy="{by}" r="16" fill="#101112"/>' + text(bx, by + 5, bl, 13, "#e8e8e8", "middle", "700")
    g += '</g>'
    out.append(g)

    # keyboard
    out.append(rect(20, 528, 596, 208, "#141516", 12))
    kx0, ky0, cw, rh, gap = 28, 536, 40.0, 34.4, 5
    for r, row in enumerate(KEYS):
        col = 0
        for key in row:
            lab, sub = key[0], key[1]
            span = key[2] if len(key) > 2 else 1
            x = kx0 + col * (cw + gap)
            w = span * cw + (span - 1) * gap
            y = ky0 + r * (rh + gap)
            out.append(rect(x, y, w, rh, "#0c0d0e", 6, 'stroke="#2c2f33" stroke-width="1"'))
            if sub:
                out.append(text(x + 4, y + 10, sub, 7.5, ORANGE))
            if lab:
                out.append(text(x + w / 2, y + rh / 2 + 5, lab, 13 if len(lab) <= 2 else 9.5, "#f2f2f2", "middle", "500"))
            col += span
    out.append('</g>')

    # caption
    out.append(text(70, 1132, "KUROGANE K-7", 30, "#f2f2f2", weight="700", extra='letter-spacing="2"'))
    out.append(text(70, 1162, "Open, modular CM5 cyberdeck · Kage Security Lab", 15, "#a9aeb4"))
    out.append(text(890, 1132, "7 in · CM5 · 6× SMA", 14, ORANGE, "end", "700"))
    out.append(text(890, 1162, "DeckBus hot-swap modules", 14, "#a9aeb4", "end"))
    out.append('</svg>')
    return "\n".join(out)


# ===================================================================== EXPLODED
TH, PH = math.radians(-38), math.radians(56)
MA, MB, MC, MD = math.cos(TH), math.sin(TH) * math.cos(PH), -math.sin(TH), math.cos(TH) * math.cos(PH)
SZ = math.sin(PH)
OX, OY, SC = 170, 560, 0.78


def layer(z, body):
    return (f'<g transform="matrix({MA * SC:.4f},{MB * SC:.4f},{MC * SC:.4f},{MD * SC:.4f},{OX},{OY - z * SZ * SC:.2f})">'
            f'{body}</g>')


def badge(x, y, n):
    return f'<circle cx="{x}" cy="{y}" r="14" fill="{ORANGE}"/>' + text(x, y + 5, str(n), 14, "#141516", "middle", "700")


LEGEND = [
    ("1", "Back shell + battery grip", "bead-blasted 6061, hatches A/B"),
    ("2", "2S2P 18650 pack", "43 Wh, protected, fused"),
    ("3", "Aluminium heat plate", "fins over the CM5, blower out the top"),
    ("4", "Mainboard + CM5", "6 layers, M.2 NVMe + LTE underneath"),
    ("5", "Input board", "61 keys, gamepad, PIM447 trackball"),
    ("6", "Touch Display 2", "7 in, 1280 × 720 landscape"),
    ("7", "Key caps", "black, orange Fn legends"),
    ("8", "Front frame + antenna crown", "6 × SMA, exposed Torx"),
    ("9", "DeckBus modules", "hot-swap sleds on dovetail rails"),
]


def exploded_frame(t, T):
    # stacked -> exploded -> hold -> stacked -> hold
    e = ease((t - 0.6) / 1.6) * (1 - ease((t - (T - 2.2)) / 1.6))
    gap = 6 + 46 * e
    hl = int(((t - 2.4) / ((T - 4.8) / 9))) if 2.4 < t < T - 2.4 else -1
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="880" height="660" viewBox="0 0 1100 825">', DEFS,
           rect(0, 0, 1100, 825, "url(#bg)")]
    out.append(text(40, 54, "KUROGANE K-7 · INSIDE AND OUT", 24, "#f2f2f2", weight="700", extra='letter-spacing="2"'))
    out.append(text(40, 80, "Every board reachable from a hatch. Bare metal by design.", 14, "#a9aeb4"))

    def hlw(k, base=''):
        return 'stroke="#ff8a1f" stroke-width="4"' if hl == k else base

    # 1 back shell
    b = rect(0, 0, 424, 504, "url(#alu)", 16, hlw(0, 'stroke="#6d7178" stroke-width="2"'))
    b += rect(62, 40, 300, 180, "#55595f", 6) + rect(40, 256, 160, 84, "none", 6, 'stroke="#6d7178" stroke-width="2"')
    b += rect(224, 256, 160, 84, "none", 6, 'stroke="#6d7178" stroke-width="2"')
    b += rect(32, 364, 360, 200, "url(#aluv)", 20, 'stroke="#5a5e64" stroke-width="2"') + badge(22, 22, 1)
    out.append(layer(0, b))
    # 2 battery
    b = ""
    for i in range(2):
        for j in range(2):
            b += rect(77 + i * 136, 410 + j * 41, 133, 38, "url(#cell)", 18, hlw(1))
    b += badge(60, 420, 2)
    out.append(layer(gap * 1, b))
    # 3 heat plate
    b = rect(62, 40, 300, 180, "#d9dde1", 6, hlw(2, 'stroke="#6d7178" stroke-width="2"'))
    for i in range(15):
        b += rect(70 + i * 19.5, 46, 6, 168, "#8f949b", 2)
    b += badge(44, 52, 3)
    out.append(layer(gap * 2, b))
    # 4 mainboard + side modules
    b = rect(22, 52, 380, 210, "#0f1011", 10, hlw(3, 'stroke="#2c2f33" stroke-width="1"'))
    b += rect(158, 102, 110, 80, "#0d5a3a", 6) + rect(182, 110, 30, 30, "url(#silver)", 3) + rect(218, 110, 26, 30, "#1a1a1c", 2)
    b += rect(218, 146, 30, 24, "url(#silver)", 3) + rect(182, 68, 34, 9, "#d9cfb4", 1)
    for i in range(20):
        b += rect(270 + i * 5.1, 134, 3, 10, "#d4a64a")
    for (ix, iy) in ((42, 76), (72, 108), (102, 108)):
        b += rect(ix, iy, 14, 14, "#45484d", 3)
    b += rect(20, 172, 42, 32, "url(#silver)", 2) + rect(376, 122, 28, 30, "url(#silver)", 2)
    for i in range(30):
        b += f'<circle cx="{40 + (i * 37) % 340}" cy="{70 + (i * 53) % 180}" r="1.6" fill="#d4a64a"/>'
    b += badge(36, 68, 4)
    b += rect(-96, 280, 68, 220, "url(#alu)", 14, hlw(8)) + rect(-34, 286, 6, 208, ORANGE, 2)
    b += rect(452, 280, 68, 220, "url(#alu)", 14, hlw(8)) + rect(452, 286, 6, 208, ORANGE, 2)
    b += rect(-76, 240, 10, 40, "#141516", 5) + rect(484, 210, 4, 70, "#141516") + badge(-62, 390, 9)
    out.append(layer(gap * 3, b))
    # 5 input board
    b = rect(16, 272, 392, 224, "#0f1011", 8, hlw(4, 'stroke="#2c2f33" stroke-width="1"'))
    for r in range(5):
        for c in range(13):
            b += f'<circle cx="{28 + c * 29.4}" cy="{362 + r * 27}" r="4" fill="#c9ced4"/>'
    b += rect(187, 280, 50, 44, "#121212", 6, 'stroke="#d4a64a" stroke-width="1"') + '<circle cx="212" cy="302" r="12" fill="url(#ball)"/>'
    for (bx, by) in ((50, 300), (70, 300), (60, 290), (60, 310), (340, 290), (360, 300), (340, 310), (320, 300)):
        b += f'<circle cx="{bx}" cy="{by}" r="4" fill="#c9ced4"/>'
    b += badge(30, 286, 5)
    out.append(layer(gap * 4, b))
    # 6 display
    b = rect(22, 28, 379, 240, "#06171c", 4, hlw(5, 'stroke="#8d939a" stroke-width="3"'))
    b += rect(56, 54, 310, 174, "url(#glass)", 2, 'stroke="#2fc6d6" stroke-width="1"')
    for i in range(7):
        b += rect(70, 70 + i * 16, 60 + (i * 47) % 140, 5, "#7fe7f2" if i % 2 else "#ffb066", 2, 'opacity="0.8"')
    b += badge(36, 42, 6)
    out.append(layer(gap * 5, b))
    # 7 key caps
    b = ""
    for r in range(5):
        for c in range(13):
            b += rect(18 + c * 30, 354 + r * 27.6, 27, 24, "#141516", 3, hlw(6) if (r == 0 and c == 0) else "")
    b += badge(4, 360, 7)
    out.append(layer(gap * 6, b))
    # 8 front frame + antennas
    b = ""
    for (x, y, w, h) in ((0, 0, 424, 28), (0, 0, 22, 504), (402, 0, 22, 504), (0, 270, 424, 82), (0, 496, 424, 8)):
        b += rect(x, y, w, h, "url(#alu)", 6, hlw(7))
    b += rect(40, 292, 40, 40, "#2a2c2f", 6) + '<circle cx="121" cy="298" r="11" fill="#2a2c2f"/><circle cx="141" cy="324" r="11" fill="#2a2c2f"/>'
    b += rect(190, 282, 44, 36, "#2a2c2f", 10) + '<circle cx="357" cy="311" r="27" fill="none" stroke="#2a2c2f" stroke-width="16"/>'
    for (x, h) in ((58, 110), (118, 140), (178, 150), (238, 140), (298, 110)):
        b += rect(x, -h, 7, h, "#141516", 3)
    b += rect(346, -44, 30, 44, "#141516", 8)
    for (sx, sy) in ((11, 11), (413, 11), (11, 493), (413, 493)):
        b += f'<circle cx="{sx}" cy="{sy}" r="5" fill="#2a2c2f"/>'
    b += badge(-22, 14, 8)
    out.append(layer(gap * 7, b))

    # legend
    for i, (n, ttl, d) in enumerate(LEGEND):
        y = 150 + i * 66
        active = (hl == i)
        out.append(rect(840, y - 26, 236, 58, "#2a2d31" if active else "#1b1d20", 8,
                        f'stroke="{ORANGE}" stroke-width="2"' if active else ''))
        out.append(badge(862, y, n))
        out.append(text(884, y - 2, ttl, 13, "#f2f2f2", weight="700"))
        out.append(text(884, y + 16, d, 10.5, "#a9aeb4"))
    out.append('</svg>')
    return "\n".join(out)


# ===================================================================== render
def render(name, frame_fn, T, width):
    tmp = tempfile.mkdtemp()
    n = int(T * FPS)
    for i in range(n):
        svg = frame_fn(i / FPS, T)
        sp = os.path.join(tmp, "f%04d.svg" % i)
        with open(sp, "w", encoding="utf-8") as f:
            f.write(svg)
        subprocess.run(["rsvg-convert", "-w", str(width), "-o", os.path.join(tmp, "f%04d.png" % i), sp], check=True)
    gif = os.path.join(OUT, name + ".gif")
    pal = os.path.join(tmp, "pal.png")
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%04d.png"),
                    "-vf", "palettegen=max_colors=192:stats_mode=diff", pal], check=True)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS), "-i", os.path.join(tmp, "f%04d.png"),
                    "-i", pal, "-lavfi", "paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle",
                    "-loop", "0", gif], check=True)
    return tmp


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    T1, T2 = 9.0, 9.0
    d1 = render("kurogane-hero", hero_frame, T1, 720)
    shutil.copy(os.path.join(d1, "f%04d.png" % int(6.0 * FPS)), os.path.join(OUT, "kurogane-hero.png"))
    d2 = render("kurogane-exploded", exploded_frame, T2, 880)
    shutil.copy(os.path.join(d2, "f%04d.png" % int(3.0 * FPS)), os.path.join(OUT, "kurogane-exploded.png"))
    print("written to", OUT)
