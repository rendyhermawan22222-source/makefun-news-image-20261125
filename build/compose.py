#!/usr/bin/env python3
"""Draw the make.fun news-image-20261125 front page and write /output/entry.png.

One self-contained Pillow program: no network, no clock, no randomness, so
running it twice produces byte-identical output.  It draws a dense 1024x1024
newspaper front page summing up world news of Wednesday 25 November 2026:
36 verified stories, 7 regions, 13 illustrations drawn in code, a world map
with numbered pins, a UTC timeline, a numbers strip and a DATE CHECK box.

Usage:
    python3 main.py                 # writes /output/entry.png
    MAKEFUN_OUTPUT_DIR=/tmp/out python3 main.py
    python3 main.py --check         # draw and report size/hash without writing
"""

from __future__ import annotations

import argparse
import hashlib
import os
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

W, H = 1024, 1024

# --- palette ---------------------------------------------------------------
CREAM = (247, 241, 222)
PAPER = (252, 248, 236)
INK = (20, 20, 20)
NAVY = (18, 40, 75)
NAVY2 = (28, 58, 104)
RED = (179, 35, 27)
GOLD = (201, 162, 39)
TEAL = (15, 122, 92)
GREY = (110, 108, 96)
LINE = (60, 58, 48)
LIGHT_LINE = (205, 198, 175)

REGION_COLORS = {
    "Europe": (31, 78, 121),
    "Asia-Pacific": (15, 122, 92),
    "Middle East": (179, 84, 30),
    "Africa": (138, 109, 0),
    "North America": (123, 45, 139),
    "Latin America": (46, 125, 50),
    "Oceania": (0, 131, 143),
}

FONT_DIR = "/usr/share/fonts/truetype/dejavu"
NOTO_DIR = "/usr/share/fonts/truetype/noto"


def font(name: str, size: int, folder: str = FONT_DIR) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(os.path.join(folder, name), size)


SERIF_B = lambda s: font("DejaVuSerif-Bold.ttf", s)      # noqa: E731
SERIF = lambda s: font("DejaVuSerif.ttf", s)             # noqa: E731
SERIF_I = lambda s: font("NotoSerif-Italic.ttf", s, NOTO_DIR)  # noqa: E731
SANS_B = lambda s: font("DejaVuSans-Bold.ttf", s)         # noqa: E731
SANS = lambda s: font("DejaVuSans.ttf", s)               # noqa: E731

# --- text helpers ----------------------------------------------------------


def text_w(draw: ImageDraw.ImageDraw, s: str, fnt) -> int:
    return int(draw.textlength(s, font=fnt))


def wrap(draw: ImageDraw.ImageDraw, s: str, fnt, max_w: int):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = s.split()
    lines, cur = [], ""
    for word in words:
        trial = (cur + " " + word).strip()
        if text_w(draw, trial, fnt) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, s, fnt, x, y, max_w, fill, leading=None, max_lines=None):
    lines = wrap(draw, s, fnt, max_w)
    if max_lines:
        lines = lines[:max_lines]
    lh = leading or int(fnt.size * 1.22)
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += lh
    return y


def badge(draw, x, y, label, color, fnt=None):
    """Small confidence badge: coloured block + white text. Returns width."""
    fnt = fnt or SANS_B(9)
    w = text_w(draw, label, fnt) + 10
    draw.rounded_rectangle([x, y, x + w, y + 15], radius=2, fill=color)
    draw.text((x + 5, y + 2), label, font=fnt, fill=(255, 255, 255))
    return w


def num_circle(draw, cx, cy, n, color, r=11):
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=color, outline=(255, 255, 255), width=1)
    s = str(n)
    fnt = SANS_B(12 if len(s) < 2 else 10)
    tw = text_w(draw, s, fnt)
    draw.text((cx - tw / 2, cy - (7 if len(s) < 2 else 6)), s, font=fnt, fill=(255, 255, 255))


def conf_color(conf: str):
    if conf.startswith("CONFIRMED"):
        return (34, 120, 34)
    if conf.startswith("OFFICIAL"):
        return (180, 120, 0)
    return (179, 35, 27)


def kicker_line(draw, x, y, num, place, region, conf, width):
    """Numbered circle + place kicker + confidence badge, one row."""
    color = REGION_COLORS[region]
    num_circle(draw, x + 11, y + 8, num, color)
    fnt = SANS_B(10)
    draw.text((x + 26, y + 3), place.upper(), font=fnt, fill=color)
    bfnt = SANS_B(9)
    bw = text_w(draw, conf, bfnt) + 10
    badge(draw, x + width - bw, y + 1, conf, conf_color(conf), bfnt)
    return y + 18


# --- illustration scenes (flat shapes, each carries a fact) ----------------
# Every scene draws on a fixed 300x110 canvas; card code scales it into the
# box, so the same art works for lead cards and small cards alike.

SCENE_W, SCENE_H = 300, 110


def scene_ebola(d):
    d.rectangle([0, 0, 300, 110], fill=(214, 232, 222))
    d.rectangle([14, 30, 286, 102], fill=(255, 255, 255), outline=NAVY, width=2)
    d.rectangle([14, 30, 286, 46], fill=NAVY)
    d.text((20, 33), "AKWE HOSPITAL", font=SANS_B(10), fill=(255, 255, 255))
    d.rectangle([248, 52, 270, 74], fill=RED)
    d.rectangle([254, 46, 264, 80], fill=RED)
    for i, cx in enumerate([36, 62, 88]):
        d.ellipse([cx, 58, cx + 13, 71], fill=NAVY)
        d.rectangle([cx + 2, 71, cx + 11, 100], fill=TEAL if i != 1 else GOLD)
    d.text((8, 4), "3 DAYS", font=SANS_B(24), fill=RED)


def scene_shenzhou(d):
    d.rectangle([0, 0, 300, 110], fill=(16, 32, 64))
    for sx, sy in [(20, 14), (60, 8), (120, 18), (170, 10), (210, 22), (260, 8)]:
        d.ellipse([sx, sy, sx + 3, sy + 3], fill=(255, 255, 255))
    d.arc([30, -40, 280, 140], 200, 340, fill=GOLD, width=2)
    d.polygon([(40, 102), (52, 22), (64, 102)], fill=(255, 255, 255))
    d.rectangle([46, 44, 58, 62], fill=RED)
    d.polygon([(34, 80), (46, 58), (46, 80)], fill=(255, 170, 60))
    d.polygon([(58, 80), (58, 58), (70, 80)], fill=(255, 170, 60))
    d.ellipse([222, 16, 282, 52], fill=(200, 210, 220), outline=GOLD, width=2)
    d.rectangle([212, 30, 222, 38], fill=GOLD)
    d.rectangle([282, 30, 292, 38], fill=GOLD)
    d.text((150, 80), "03:56 UTC", font=SANS_B(22), fill=(255, 255, 255))


def scene_rosstat(d):
    d.rectangle([0, 0, 300, 110], fill=(232, 226, 208))
    d.rectangle([12, 34, 96, 100], fill=(255, 255, 255), outline=INK, width=1)
    d.rectangle([12, 34, 96, 50], fill=RED)
    d.text((18, 37), "ROSSTAT", font=SANS_B(10), fill=(255, 255, 255))
    for i in range(5):
        d.line([20, 60 + i * 8, 88, 60 + i * 8], fill=(150, 148, 136), width=2)
    d.rectangle([104, 34, 150, 100], fill=(255, 255, 255), outline=INK, width=1)
    d.text((110, 38), "LEAK", font=SANS_B(10), fill=RED)
    for i in range(4):
        d.line([110, 56 + i * 8, 144, 56 + i * 8], fill=(150, 148, 136), width=2)
    bars = [18, 34, 52, 78]
    for i, bh in enumerate(bars):
        d.rectangle([168 + i * 30, 96 - bh, 188 + i * 30, 96], fill=RED if i == 3 else NAVY)
    d.text((168, 4), "490,334", font=SANS_B(24), fill=RED)


def scene_solomons(d):
    d.rectangle([0, 0, 300, 110], fill=(222, 234, 244))
    d.rectangle([16, 14, 96, 66], fill=(0, 40, 104), outline=(255, 255, 255), width=2)
    for sx, sy in [(30, 26), (52, 22), (74, 30), (44, 44), (66, 48)]:
        d.ellipse([sx, sy, sx + 5, sy + 5], fill=(255, 255, 255))
    d.rectangle([110, 14, 190, 66], fill=(0, 90, 60), outline=(255, 255, 255), width=2)
    for sx, sy in [(124, 26), (146, 22), (168, 30), (138, 46), (160, 48)]:
        d.ellipse([sx, sy, sx + 5, sy + 5], fill=(255, 255, 255))
    d.line([96, 40, 110, 40], fill=GOLD, width=3)
    d.text((200, 80), "A$740M", font=SANS_B(24), fill=NAVY)


def scene_kospi(d):
    d.rectangle([0, 0, 300, 110], fill=(244, 226, 224))
    pts = [(8, 16), (40, 22), (72, 14), (104, 34), (136, 52), (168, 98)]
    d.line(pts, fill=RED, width=4, joint="curve")
    for px, py in pts:
        d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=RED)
    d.text((8, 76), "-6.2%", font=SANS_B(28), fill=RED)
    d.text((180, 6), "SAMSUNG -9.9%", font=SANS_B(10), fill=INK)
    d.text((180, 22), "SK HYNIX -11.1%", font=SANS_B(10), fill=INK)


def scene_tariffs(d):
    d.rectangle([0, 0, 300, 110], fill=(222, 232, 244))
    d.rectangle([10, 76, 290, 88], fill=NAVY)
    d.polygon([(14, 76), (30, 76), (22, 58)], fill=NAVY)
    for i, col in enumerate([RED, GOLD, TEAL, NAVY]):
        d.rectangle([36 + i * 34, 48, 64 + i * 34, 74], fill=col, outline=(255, 255, 255), width=1)
    d.text((8, 4), "20%", font=SANS_B(28), fill=RED)
    d.text((90, 10), "CHINA", font=SANS_B(12), fill=INK)
    d.text((90, 28), "14 ECONOMIES", font=SANS_B(10), fill=GREY)


def scene_ukcap(d):
    d.rectangle([0, 0, 300, 110], fill=(250, 238, 210))
    d.polygon([(24, 46), (84, 16), (144, 46)], fill=NAVY)
    d.rectangle([32, 46, 136, 100], fill=(255, 255, 255), outline=NAVY, width=2)
    d.rectangle([72, 64, 96, 100], fill=NAVY)
    d.polygon([(168, 16), (160, 34), (172, 34), (162, 54), (178, 30), (166, 30)], fill=GOLD)
    d.text((150, 80), "£2,166", font=SANS_B(24), fill=RED)


def scene_hormuz(d):
    d.rectangle([0, 0, 300, 110], fill=(18, 58, 96))
    d.rectangle([0, 84, 300, 110], fill=(10, 40, 70))
    d.rectangle([14, 40, 86, 64], fill=(120, 30, 25))
    d.rectangle([20, 28, 40, 40], fill=(200, 200, 200))
    d.rectangle([110, 46, 182, 70], fill=(90, 90, 90))
    d.rectangle([116, 34, 136, 46], fill=(200, 200, 200))
    for fx, fy in [(88, 26), (184, 32)]:
        d.polygon([(fx, fy + 16), (fx + 6, fy), (fx + 12, fy + 16)], fill=(255, 170, 40))
        d.polygon([(fx + 3, fy + 16), (fx + 6, fy + 6), (fx + 9, fy + 16)], fill=(255, 60, 20))
    for mx, my in [(100, 92), (150, 96), (60, 94)]:
        d.ellipse([mx, my, mx + 8, my + 8], fill=(30, 30, 30), outline=GOLD, width=1)
    d.text((8, 2), "2 HIT", font=SANS_B(22), fill=(255, 255, 255))


def scene_cricket(d):
    d.rectangle([0, 0, 300, 110], fill=(226, 240, 214))
    d.ellipse([12, 12, 288, 98], fill=(255, 255, 255), outline=TEAL, width=2)
    d.polygon([(66, 18), (84, 18), (78, 88), (60, 88)], fill=(210, 170, 110))
    d.rectangle([64, 12, 86, 26], fill=(120, 70, 20))
    d.ellipse([120, 26, 138, 44], fill=RED)
    d.text((8, 70), "204", font=SANS_B(28), fill=NAVY)
    d.text((170, 80), "28 SIXES", font=SANS_B(12), fill=RED)


def scene_cia(d):
    d.rectangle([0, 0, 300, 110], fill=(232, 232, 238))
    d.rectangle([24, 16, 168, 84], fill=(30, 30, 40))
    d.rectangle([30, 22, 162, 78], fill=(120, 200, 255))
    d.text((40, 30), "OSINT", font=SANS_B(13), fill=NAVY)
    for i in range(3):
        d.line([40, 52 + i * 8, 150, 52 + i * 8], fill=(255, 255, 255), width=2)
    d.ellipse([180, 30, 220, 62], outline=RED, width=4)
    d.line([204, 56, 224, 76], fill=RED, width=4)
    d.text((185, 86), "BREACHED", font=SANS_B(18), fill=RED)


def scene_pce(d):
    d.rectangle([0, 0, 300, 110], fill=(238, 240, 232))
    vals = [22, 30, 38, 46, 58]
    for i, vh in enumerate(vals):
        d.rectangle([16 + i * 30, 94 - vh, 36 + i * 30, 94], fill=RED if i == 4 else NAVY)
    d.text((8, 4), "3.8%", font=SANS_B(28), fill=RED)
    d.text((180, 10), "CORE 3.3%", font=SANS_B(11), fill=INK)
    d.text((180, 28), "GDP 4.3%", font=SANS_B(11), fill=INK)


def scene_drones(d):
    d.rectangle([0, 0, 300, 110], fill=(14, 22, 48))
    for sx, sy in [(16, 10), (60, 20), (110, 8), (150, 16), (180, 10), (240, 14), (270, 20)]:
        d.ellipse([sx, sy, sx + 3, sy + 3], fill=(255, 255, 255))
    for dx, dy in [(30, 34), (80, 28), (130, 40), (165, 30), (210, 36)]:
        d.ellipse([dx, dy, dx + 10, dy + 6], fill=(180, 180, 180))
        d.line([dx - 6, dy + 3, dx + 16, dy + 3], fill=(180, 180, 180), width=2)
        d.ellipse([dx + 2, dy + 8, dx + 8, dy + 12], fill=RED)
    d.rectangle([10, 92, 290, 104], fill=(40, 40, 60))
    for bx in [20, 60, 100, 140, 180, 220]:
        d.rectangle([bx, 76, bx + 22, 92], fill=(60, 60, 90))
    d.text((8, 52), "88/112", font=SANS_B(22), fill=(255, 255, 255))


def scene_gaza(d):
    d.rectangle([0, 0, 300, 110], fill=(240, 228, 210))
    for bx, bw, bh in [(14, 44, 46), (64, 36, 64), (106, 48, 38), (160, 34, 56), (200, 44, 48), (250, 36, 60)]:
        d.rectangle([bx, 98 - bh, bx + bw, 98], fill=(150, 140, 120))
        for wy in range(2):
            for wx in range(3):
                d.rectangle([bx + 6 + wx * 12, 98 - bh + 8 + wy * 14, bx + 14 + wx * 12, 98 - bh + 18 + wy * 14], fill=(250, 240, 210))
    d.ellipse([70, 6, 110, 30], fill=(120, 120, 120))
    d.ellipse([88, -6, 122, 16], fill=(90, 90, 90))
    d.text((8, 78), "CHIEF KILLED", font=SANS_B(17), fill=RED)


def render_scene(num: int, w: int, h: int) -> Image.Image:
    """Draw one illustration on its fixed canvas, then scale into (w, h)."""
    canvas = Image.new("RGB", (SCENE_W, SCENE_H), (255, 255, 255))
    d = ImageDraw.Draw(canvas)
    SCENES[num](d)
    return canvas.resize((w, h), Image.LANCZOS)


SCENES = {
    1: scene_ebola, 2: scene_shenzhou, 3: scene_rosstat, 4: scene_solomons,
    5: scene_kospi, 6: scene_tariffs, 7: scene_ukcap, 8: scene_hormuz,
    9: scene_cricket, 10: scene_cia, 11: scene_pce, 12: scene_drones, 13: scene_gaza,
}

# --- story data ------------------------------------------------------------

# (num, place, region, confidence, headline, dek, source)
LEADS = [
    (1, "Akwe, Ituri, DR Congo", "Africa", "OFFICIAL · WHO",
     "WHO pulls Ebola teams out of a Congo hospital",
     "After three days sheltering in a maternity ward, WHO staff reach safety.",
     "WHO · UN News"),
    (2, "Jiuquan, China", "Asia-Pacific", "CONFIRMED · CMSA",
     "Shenzhou-24 docks with first Pakistani astronaut",
     "Launched 00:18 UTC, docked 03:56 UTC; Muhammad Zeeshan Ali is the first foreigner aboard Tiangong.",
     "CMSA · Xinhua · AP"),
    (3, "Moscow, Russia", "Europe", "CONFIRMED · BBC",
     "Leak puts Russian war dead at 490,334",
     "Hacked Rosstat records, analysed by BBC Russian; with the missing, the toll tops 700,000.",
     "BBC Russian · Mediazona"),
]

SMALL = [
    (4, "Canberra", "Oceania", "OFFICIAL · PMs",
     "Solomons pick Australia as security partner",
     "No foreign base on Solomons soil; A$740m over 10 years.", "PM of Australia · AP"),
    (5, "Seoul", "Asia-Pacific", "CONFIRMED · AP",
     "Kospi plunges 6.2% in AI rout",
     "Samsung -9.9%, SK Hynix -11.1%; Taiex -5%, Nikkei -2.8%.", "AP · Korea Exchange"),
    (6, "Washington", "North America", "CONFIRMED · USTR",
     "US proposes tariffs on 14 economies",
     "China 20%, EU 15%, Vietnam up to 35%; hearings in January.", "USTR · Reuters"),
    (7, "London", "Europe", "OFFICIAL · Ofgem",
     "UK energy bills to jump 26% in January",
     "Cap rises to £2,166 a year; gas +37.5%, power +24.2%.", "Ofgem · WSJ"),
    (8, "Hormuz", "Middle East", "CLAIM · IRGC",
     "Two tankers hit mines in the Strait",
     "IRGC navy says both struck mines and caught fire.", "IRGC · Reuters"),
    (9, "Doha", "Asia-Pacific", "CONFIRMED · Cricinfo",
     "Sooryavanshi, 15, smashes 204 off 53 balls",
     "Fastest List A 100 (28 balls) and 200 (52); 28 sixes.", "ESPNcricinfo · BBC"),
    (10, "Washington", "North America", "REPORTED · NYT",
     "CIA breach hits unclassified network",
     "Open-source intelligence system hit; no classified data.", "NYT · AP"),
    (11, "Washington", "North America", "OFFICIAL · BEA",
     "US inflation heats up: PCE 3.8%",
     "Core PCE 3.3%, above forecast; Q3 GDP revised to 4.3%.", "BEA · Reuters"),
    (12, "Kyiv", "Europe", "CONFIRMED · Kyiv",
     "88 of 112 drones downed overnight",
     "Kyiv flats hit, 3 hurt; Odesa strike kills 2.", "Ukrainian Air Force"),
    (13, "Gaza City", "Middle East", "REPORTED · Gaza",
     "Israeli strike kills Hamas security chief",
     "Naeem Abu Nahel killed with family members in Gaza City.", "Gaza officials · AP"),
]

# Each one-liner is kept short so it fits on one 8pt line in its column.
ALSO = [
    (14, "Damazin", "RSF drones kill 19 in Blue Nile.", "E. Lawyers"),
    (15, "Cartagena", "All hostages freed in supermarket siege.", "police"),
    (16, "Bogor", "Flooded mine toll 6; ~20 miners trapped.", "rescuers"),
    (17, "New York", "Huawei guilty on 10 of 12 counts.", "US court"),
    (18, "Dakar", "CAS restores Senegal as AFCON champions.", "CAS"),
    (19, "Madrid", "Real Madrid hit PSV for five, 5-1.", "UEFA"),
    (20, "Berlin", "Merz warns on Russia's aims.", "Bundestag"),
    (21, "Warsaw", "Poland seeks permanent US base.", "Warsaw"),
    (22, "Benghazi", "LNA vows revenge for two dead officers.", "LNA"),
    (23, "Ras Tanura", "Houthis claim refinery attack.", "Houthis"),
    (24, "London", "Britain sanctions Houthis, 4 officials.", "London"),
    (25, "Baghdad", "Iraq to take over Kurdish oilfields.", "Baghdad"),
    (26, "Kinshasa", "DR Congo halts cobalt exports again.", "Kinshasa"),
    (27, "Canberra", "Australia inflation rises to 4.9%.", "ABS"),
    (28, "Buenos Aires", "Argentina enters recession.", "B. Aires"),
    (29, "Texas", "Dell Q3 sales $54.9bn, up 103%.", "Dell"),
    (30, "Lusaka", "Opposition leader charged with treason.", "Lusaka"),
    (31, "Madrid", "Abrego Garcia leaves US for Spain.", "Madrid"),
    (32, "Beijing", "Shanghai party chief Chen probed.", "Beijing"),
    (33, "Mississippi", "Plane crash kills six.", "officials"),
    (34, "Vatican", "Pope laments COP31's failure.", "Vatican"),
    (35, "London", "Oil down over 20% across November.", "markets"),
    (36, "Xiamen", "China Southern unit orders 50 Boeings.", "Boeing"),
]

UTC_STRIP = [
    ("00:18", "Shenzhou-24 lifts off"),
    ("03:56", "Shenzhou-24 docks"),
    ("Dawn", "Two tankers hit mines"),
    ("07:00", "Ofgem: UK cap +26%"),
    ("10:00", "Cartagena siege ends"),
    ("13:30", "US PCE 3.8%, GDP 4.3%"),
    ("13:58", "BBC publishes Rosstat toll"),
]

NUMBERS = [
    ("490,334", "Russian soldiers dead — leaked Rosstat records, BBC"),
    ("-6.2%", "Kospi's fall in the AI rout — Korea Exchange"),
    ("£2,166", "UK energy cap from January, up 26% — Ofgem"),
    ("3.8%", "US PCE inflation; core 3.3% — BEA"),
    ("204", "Sooryavanshi's runs off 53 balls, 28 sixes"),
    ("88/112", "Russian drones downed over Ukraine overnight"),
]

REGION_CHIPS = [
    ("Europe", 10), ("Asia-Pacific", 6), ("Middle East", 4), ("Africa", 6),
    ("North America", 6), ("Latin America", 2), ("Oceania", 2),
]

DATE_CHECK_LEFT = (
    "Left out — first reported on another day: PIF Tower, Riyadh, hit again, 11 hurt (Tue 24 Nov) · "
    "COP31 ends with no climate pact (Sun 22 Nov) · Dow closes above 50,000 first time (Tue 24 Nov) · "
    "Nvidia's Jensen Huang returns as chief executive (Mon 24 Nov) · Ebola toll, 11,762 cases (figures Fri 20 Nov)."
)
DATE_CHECK_NEXT = (
    "Not yet: Wednesday's Champions League ties · the Fed's 9 Dec rate call · Shenzhou-24's crew return (next week)."
)

# World map: land spans per row, cols 0..59 (6 deg each, -180..180),
# rows 0..27 (5 deg each, 75N..-60S). Hand-drawn from a world outline.
MAP_SPANS = {
    0: [(8, 12), (20, 24), (38, 58)],
    1: [(4, 13), (20, 26), (37, 59)],
    2: [(3, 14), (28, 31), (36, 59)],
    3: [(4, 14), (27, 31), (35, 58)],
    4: [(5, 14), (27, 34), (35, 52)],
    5: [(5, 13), (27, 35), (37, 54)],
    6: [(6, 12), (27, 35), (37, 55)],
    7: [(6, 12), (27, 34), (38, 53)],
    8: [(6, 11), (28, 33), (36, 39), (41, 50), (52, 54)],
    9: [(6, 10), (28, 36), (41, 48), (50, 52)],
    10: [(6, 9), (28, 36), (42, 45), (47, 50)],
    11: [(7, 9), (28, 36), (42, 44), (47, 50)],
    12: [(8, 10), (29, 36), (47, 49)],
    13: [(9, 11), (29, 36), (48, 50)],
    14: [(10, 13), (30, 35), (48, 54)],
    15: [(11, 15), (30, 35), (49, 55)],
    16: [(11, 15), (30, 35), (51, 56)],
    17: [(11, 15), (31, 34), (52, 56)],
    18: [(12, 15), (31, 34), (51, 56)],
    19: [(12, 15), (31, 34), (51, 56)],
    20: [(12, 14), (32, 34), (52, 56)],
    21: [(13, 14), (32, 33), (52, 55)],
    22: [(13, 14), (57, 58)],
    23: [(13, 14), (57, 58)],
    24: [(13, 13)],
    25: [(13, 13)],
}

# (num, lon, lat, region) for map pins
PINS = [
    (1, 30, 1.5, "Africa"), (2, 98, 40, "Asia-Pacific"), (3, 37, 55, "Europe"),
    (4, 149, -35, "Oceania"), (5, 127, 37, "Asia-Pacific"), (6, -77, 39, "North America"),
    (7, 0, 51, "Europe"), (8, 56, 26, "Middle East"), (9, 51, 25, "Asia-Pacific"),
    (12, 30, 50, "Europe"), (13, 34, 31, "Middle East"), (14, 33, 13, "Africa"),
    (15, -75, 10, "Latin America"), (16, 107, -6, "Asia-Pacific"),
    (18, -17, 15, "Africa"), (19, -4, 40, "Europe"), (20, 13, 52, "Europe"),
    (22, 20, 32, "Africa"), (25, 44, 33, "Middle East"), (26, 15, -4, "Africa"),
    (28, -58, -35, "Latin America"), (30, 28, -15, "Africa"),
]


def draw_map(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=(226, 234, 240), outline=LINE, width=1)
    step_x = w / 60.0
    step_y = h / 28.0
    for row, spans in MAP_SPANS.items():
        cy = y + (row + 0.5) * step_y
        for c0, c1 in spans:
            for c in range(c0, c1 + 1):
                cx = x + (c + 0.5) * step_x
                d.ellipse([cx - 2, cy - 2, cx + 2, cy + 2], fill=(120, 130, 120))
    for num, lon, lat, region in PINS:
        px = x + ((lon + 180) / 360.0) * w
        py = y + ((75 - lat) / 135.0) * h
        num_circle(d, px, py, num, REGION_COLORS[region], r=9)


def draw_lead_card(img, d, x, y, w, h, story):
    num, place, region, conf, headline, dek, source = story
    d.rectangle([x, y, x + w, y + h], fill=PAPER, outline=LINE, width=1)
    img.paste(render_scene(num, w - 2, 100), (x + 1, y + 1))
    ky = y + 104
    kicker_line(d, x + 6, ky, num, place, region, conf, w - 12)
    hy = ky + 20
    hy = draw_wrapped(d, headline, SERIF_B(20), x + 8, hy, w - 16, INK, leading=23, max_lines=2)
    draw_wrapped(d, dek, SANS(12), x + 8, hy + 3, w - 16, (50, 50, 50), leading=15, max_lines=2)
    d.text((x + 8, y + h - 15), source, font=SANS(9), fill=GREY)


def draw_small_card(img, d, x, y, w, h, story):
    num, place, region, conf, headline, dek, source = story
    d.rectangle([x, y, x + w, y + h], fill=PAPER, outline=LINE, width=1)
    img.paste(render_scene(num, w - 2, 50), (x + 1, y + 1))
    ky = y + 53
    color = REGION_COLORS[region]
    num_circle(d, x + 12, ky + 8, num, color, r=10)
    d.text((x + 26, ky + 2), place.upper(), font=SANS_B(9), fill=color)
    short = conf.split(" · ")[0]
    bfnt = SANS_B(8)
    bw = text_w(d, short, bfnt) + 8
    badge(d, x + w - bw - 4, ky + 1, short, conf_color(conf), bfnt)
    hy = ky + 19
    hy = draw_wrapped(d, headline, SERIF_B(13), x + 7, hy, w - 14, INK, leading=15, max_lines=3)
    draw_wrapped(d, dek, SANS(10), x + 7, hy + 1, w - 14, (50, 50, 50), leading=12, max_lines=2)
    d.text((x + 7, y + h - 12), source, font=SANS(8), fill=GREY)


def build() -> Image.Image:
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    mx = 14
    cw = W - 2 * mx  # 996

    # 1. top bar
    d.rectangle([0, 0, W, 24], fill=NAVY)
    d.text((mx, 5), "THE WORLD IN ONE DAY", font=SANS_B(12), fill=(255, 255, 255))
    right = "36 STORIES · 7 REGIONS · 13 DRAWN · EVERY ONE FROM WEDNESDAY 25 NOVEMBER 2026"
    d.text((W - mx - text_w(d, right, SANS_B(11)), 6), right, font=SANS_B(11), fill=GOLD)

    # 2. masthead
    title = "Wednesday 25 November 2026"
    tf = SERIF_B(52)
    d.text(((W - text_w(d, title, tf)) / 2, 28), title, font=tf, fill=INK)
    sub = ("WHO pulls Ebola teams out of Congo  •  Shenzhou-24 docks with first Pakistani astronaut  •  "
           "Leak puts Russian war dead at 490,334")
    sf = SERIF_I(16)
    d.text(((W - text_w(d, sub, sf)) / 2, 90), sub, font=sf, fill=RED)

    # 3. region chips
    cx = mx
    cy = 112
    for name, count in REGION_CHIPS:
        col = REGION_COLORS[name]
        label = f"{name.upper()} {count}"
        fnt = SANS_B(10)
        wch = text_w(d, label, fnt) + 14
        d.rounded_rectangle([cx, cy, cx + wch, cy + 18], radius=9, fill=col)
        d.text((cx + 7, cy + 3), label, font=fnt, fill=(255, 255, 255))
        cx += wch + 8

    # 4. UTC strip
    uy = 136
    d.rectangle([mx, uy, mx + cw, uy + 34], fill=NAVY)
    d.text((mx + 6, uy + 10), "THE DAY IN UTC", font=SANS_B(11), fill=GOLD)
    col_w = (cw - 130) / 7.0
    for i, (t, ev) in enumerate(UTC_STRIP):
        x0 = mx + 130 + i * col_w
        d.line([x0, uy + 4, x0, uy + 30], fill=(120, 140, 170), width=1)
        d.text((x0 + 5, uy + 3), t, font=SANS_B(11), fill=(255, 255, 255))
        draw_wrapped(d, ev, SANS(8), x0 + 5, uy + 17, col_w - 8, (210, 215, 225), leading=9, max_lines=2)

    # 5. numbers strip
    ny = 174
    col_w = cw / 6.0
    for i, (num, label) in enumerate(NUMBERS):
        x0 = mx + i * col_w
        if i:
            d.line([x0, ny + 2, x0, ny + 36], fill=LIGHT_LINE, width=1)
        d.text((x0 + 6, ny), num, font=SANS_B(19), fill=RED)
        draw_wrapped(d, label, SANS(8), x0 + 6, ny + 22, col_w - 12, (60, 60, 60), leading=9, max_lines=2)

    # 6. three lead cards
    ly = 214
    lw = (cw - 24) // 3
    for i, story in enumerate(LEADS):
        draw_lead_card(img, d, mx + i * (lw + 12), ly, lw, 222, story)

    # 7. ten small cards, 2 rows of 5
    d.text((mx, 442), "THE DAY IN TEN MORE", font=SANS_B(12), fill=NAVY)
    d.text((mx + 190, 443), "Wednesday's other big stories, across seven regions", font=SERIF_I(11), fill=GREY)
    sw = (cw - 4 * 8) // 5
    for row in range(2):
        for col in range(5):
            idx = row * 5 + col
            draw_small_card(img, d, mx + col * (sw + 8), 460 + row * 148, sw, 144, SMALL[idx])

    # 8. bottom: map left, also-list right
    by = 760
    bh = 172
    d.text((mx, by - 2), "WHERE IT HAPPENED", font=SANS_B(12), fill=NAVY)
    d.text((mx + 178, by - 1), "pin = story number", font=SANS(9), fill=GREY)
    draw_map(d, mx, by + 16, 450, bh - 16)
    ax = mx + 462
    d.text((ax, by - 2), "ALSO ON WEDNESDAY 25 NOVEMBER — 23 MORE STORIES", font=SANS_B(12), fill=NAVY)
    col_w2 = (cw - 462) / 2.0
    for i, (num, place, text, src) in enumerate(ALSO):
        col = 0 if i < 12 else 1
        row = i if i < 12 else i - 12
        x0 = ax + col * col_w2
        y0 = by + 16 + row * 13
        d.text((x0, y0), f"{num}", font=SANS_B(9), fill=NAVY)
        line = f"{place}: {text} {src.upper()}"
        fnt = SANS(8)
        while text_w(d, line, fnt) > col_w2 - 20 and len(line) > 10:
            line = line[:-5].rstrip() + "…"
        d.text((x0 + 16, y0), line, font=fnt, fill=INK)

    # 9. date check
    dy = 940
    d.rectangle([mx, dy, mx + cw, dy + 44], fill=(255, 240, 238), outline=RED, width=2)
    d.rectangle([mx, dy, mx + 92, dy + 44], fill=RED)
    d.text((mx + 10, dy + 6), "DATE", font=SANS_B(13), fill=(255, 255, 255))
    d.text((mx + 8, dy + 23), "CHECK", font=SANS_B(13), fill=(255, 255, 255))
    draw_wrapped(d, DATE_CHECK_LEFT, SANS(9), mx + 100, dy + 3, cw - 108, INK, leading=11, max_lines=2)
    draw_wrapped(d, DATE_CHECK_NEXT, SANS(9), mx + 100, dy + 26, cw - 108, (90, 30, 25), leading=11, max_lines=1)

    # 10. footer legend
    fy = 992
    d.line([mx, fy, mx + cw, fy], fill=LINE, width=1)
    legend = ("CONFIRMED  2+ outlets    OFFICIAL  on the record    REPORTED  one outlet    "
              "CLAIM  one side's word  ·  Times UTC; c. = approximate  ·  "
              "Pictures and map drawn in code, not photographs.")
    d.text((mx, fy + 6), legend, font=SANS(9), fill=(60, 60, 60))
    d.text((mx, fy + 20), "Sources: AP · Reuters · BBC · Xinhua · CMSA · WHO · Ofgem · BEA · USTR · UEFA · ESPNcricinfo",
           font=SANS(8), fill=GREY)
    return img


def output_dir() -> Path:
    raw = os.environ.get("MAKEFUN_OUTPUT_DIR", "").strip()
    return Path(raw) if raw else Path("/output")


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="draw and report size/hash without writing")
    args = ap.parse_args(argv)
    img = build()
    if img.size != (1024, 1024):
        print(f"bad size: {img.size}", file=sys.stderr)
        return 1
    import io
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    data = buf.getvalue()
    digest = hashlib.sha256(data).hexdigest()
    print(f"entry.png: {len(data)} bytes, sha256 {digest}")
    if len(data) > 1048576:
        print("too large: over 1 MiB", file=sys.stderr)
        return 1
    if args.check:
        return 0
    out = output_dir()
    out.mkdir(parents=True, exist_ok=True)
    (out / "entry.png").write_bytes(data)
    print(f"wrote {out / 'entry.png'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
