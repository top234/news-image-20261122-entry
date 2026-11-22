#!/usr/bin/env python3
"""news-image-20261122 v1 — "The Sunday Ledger".

A deterministic day-ledger front page summing up Sunday 22 November 2026
world news. Draws entry.png (1024x1024, < 1 MiB) with PIL only.

Every story was verified by the coordinator against a reputable source
(AP, Reuters, BBC, USGS, AAP, AFP, ...) — see BUILD_NOTES.md in the work
directory. Each story carries a day tag: SUN = Sunday 22 Nov, SAT =
Saturday 21 Nov, FRI = Friday 20 Nov, WED = Wednesday 19 Nov, WEEK =
earlier in the week, first reported or confirmed this week.

No network, no external assets, no randomness in the output
(random.seed fixed; all coordinates are constants).
"""

import random
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

random.seed(20261122)

W, H = 1024, 1024
M = 28  # outer margin
CW = W - 2 * M  # content width = 968

# ---------- palette ----------
PAPER = (248, 244, 233)
INK = (27, 42, 65)
INK_SOFT = (58, 68, 84)
MUTED = (110, 112, 108)
HAIR = (198, 188, 164)
CARD = (255, 252, 244)
CARD_EDGE = (205, 196, 172)
RED = (178, 52, 40)
RED_SOFT = (246, 226, 222)
TEAL = (23, 107, 92)
GOLD = (169, 123, 31)
NAVY = (31, 58, 95)
OCEAN = (214, 231, 241)
LAND = (216, 226, 208)
LAND_EDGE = (178, 196, 168)
WHITE = (255, 255, 255)

REGION_COLORS = {
    "ASIA-PACIFIC": (23, 107, 92),
    "OCEANIA": (42, 98, 163),
    "EUROPE": (106, 76, 147),
    "AMERICAS": (198, 106, 24),
    "MIDDLE EAST": (178, 52, 40),
    "AFRICA": (74, 124, 50),
    "GLOBAL": (31, 58, 95),
}

# ---------- fonts ----------
FONT_DIRS = [
    "/usr/share/fonts/truetype/dejavu",
    "/usr/share/fonts/truetype/liberation",
    "/usr/share/fonts/truetype/noto",
]


def font(name, size):
    for d in FONT_DIRS:
        p = Path(d) / name
        if p.exists():
            return ImageFont.truetype(str(p), size)
    return ImageFont.load_default()


SERIF_B = "DejaVuSerif-Bold.ttf"
SANS = "DejaVuSans.ttf"
SANS_B = "DejaVuSans-Bold.ttf"
SANS_O = "DejaVuSans-Oblique.ttf"

WARNINGS = []


def warn(msg):
    WARNINGS.append(msg)
    print("WARN:", msg, file=sys.stderr)


def text_w(draw, s, f):
    return draw.textlength(s, font=f)


def wrap(draw, text, f, max_w):
    """Greedy word wrap by measured width. Returns list of lines."""
    words = text.split()
    lines, cur = [], ""
    for w_ in words:
        trial = (cur + " " + w_).strip()
        if text_w(draw, trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = w_
    if cur:
        lines.append(cur)
    return lines


def fit_lines(draw, text, f, max_w, max_lines, label):
    """Wrap text; warn if it needs more lines than allowed."""
    lines = wrap(draw, text, f, max_w)
    if len(lines) > max_lines:
        warn(f"{label}: {len(lines)} lines > {max_lines}: {text!r}")
        lines = lines[:max_lines]
    return lines


def fit_one_line(draw, text, f, max_w, label, min_size=9):
    """Shrink font until the text fits on one line; warn if it hits min_size."""
    size = f.size
    cur = f
    while text_w(draw, text, cur) > max_w and size > min_size:
        size -= 1
        cur = font(SANS, size)
    if text_w(draw, text, cur) > max_w:
        warn(f"{label}: still too wide at {size}px: {text!r}")
    return cur


# ---------- story data ----------
# (number, region, tag, headline, deck, source)
HEROES = [
    (
        1, "ASIA-PACIFIC", "SHENZHEN · PEACE DEAL",
        "Trump, Xi and Putin sign a four-point peace declaration",
        "Signed in Shenzhen by Trump, Xi and Putin — a four-point "
        "declaration that says nothing about Ukraine.",
        "AP · REUTERS",
    ),
    (
        2, "GLOBAL", "MARKETS · FRIDAY ROUT",
        "Nasdaq suffers its worst week since 2020, down 10.4%",
        "S&P 500 falls into correction; Dow drops 1,101 to 49,097, first "
        "close below 50,000 since June. Nvidia -14% under SEC probe; "
        "gold -2.8% to $3,518.50/oz.",
        "AP · REUTERS",
    ),
    (
        3, "MIDDLE EAST", "GULF WAR · WIDENS",
        "Iran drones hit a US air base in Kuwait and sites in Bahrain",
        "US jets had struck an IRGC missile site on Qeshm Island the day "
        "before. An ADNOC-linked tanker was hit in Hormuz: 1 crew "
        "missing, 11 hurt.",
        "AP · REUTERS",
    ),
]

SMALL = [
    (4, "ASIA-PACIFIC", "GENOCIDE RULING",
     "World Court: Myanmar committed genocide against the Rohingya",
     "First time any international court has found a state guilty of genocide.",
     "ICJ"),
    (5, "EUROPE", "GREENLAND",
     "Denmark votes 109-0 for new US security deal",
     "Ratified unanimously; two new American bases in Greenland.",
     "AP · REUTERS"),
    (6, "EUROPE", "ESTONIA",
     "Estonia to shut all 5 Russia border crossings",
     "From 1 Dec for 6 months, after a GRU-linked arson try on drone-maker Threod Systems.",
     "REUTERS"),
    (7, "AMERICAS", "QUAKE · PERU",
     "M6.7 quake shakes Peru's Andes",
     "34 km north of Junin, 108 km deep, 19:09 local; felt in Lima. No casualties or damage.",
     "USGS · AP"),
    (8, "GLOBAL", "COP31 · ANTALYA",
     "Climate talks go into overtime, deadlocked",
     "Nearly 200 nations stuck on fossil fuels; AI pledge fails to draw major US tech firms.",
     "AP · REUTERS"),
    (9, "EUROPE", "KERCH BRIDGE",
     "Ukraine hits the Crimea bridge a third time",
     "Third strike in four days; Zelensky calls it a 'fair response'. Berlin talks under way.",
     "AP · REUTERS"),
    (10, "GLOBAL", "IPO · NEW YORK",
     "Anthropic IPO: $81.3bn, the biggest ever",
     "Shares +39% on debut, then fall the next day.",
     "REUTERS"),
    (11, "OCEANIA", "CRICKET · MCG",
     "Record MCG chase: Australia hunt down 188",
     "Beat England by 3 wickets with a ball to spare; Chaudhary 66 off 38; crowd 39,289.",
     "AAP"),
]

# (number, one-line text incl. day tag in parens)
LIST = [
    (12, "North Korea expanding Yongbyon uranium plant, IAEA says (WEEK)"),
    (13, "Bangladesh violence flares before Hasina's planned return (WEEK)"),
    (14, "US signs new military deal with Venezuela, 10 months after Maduro's removal (WEEK)"),
    (15, "Poland: two Russian missiles and a drone land in rural Poland; PM Tusk responds (FRI)"),
    (16, "Denmark accuses Russia of plotting to kill a US-Ukrainian rapper near Copenhagen (FRI)"),
    (17, "Russian merchant ship on fire in the Gulf of Finland, likely hit by drones (SAT)"),
    (18, "FBI investigating apparent hack of its criminal database (FRI)"),
    (19, "Mexican army captures cartel kingpin Fausto Isidro Meza Flores, 'El Chapo Isidro' (WEEK)"),
    (20, "Pentagon memo: US troops to curb informal gatherings with Canadian counterparts (WEEK)"),
    (21, "Trump threatens a 'tremendous tax' on US firms building AI data centres overseas (FRI)"),
    (22, "Zscaler jumps 18% on report CrowdStrike is in talks to buy it (SAT)"),
    (23, "Modi inaugurates Nitish Setu, linking Patna and Vaishali (SUN)"),
    (24, "Cyclone Akvan: 14 flights cancelled at Ranchi airport (SUN)"),
    (25, "India face New Zealand in the 1st Test in windy Wellington (SUN)"),
    (26, "Sensex ends a two-day rally on profit booking and Fed rate worries (SUN)"),
    (27, "Cummins keeps Australia's Test captaincy with unanimous support (SUN)"),
    (28, "Snooker: Advani and Ramachandran win opening World Championship matches (SUN)"),
    (29, "Chess: Erigaisi and Praggnanandhaa win; Vaishali loses on day one (SUN)"),
    (30, "South Africa local elections: ANC fights to keep control of the cities (SUN)"),
    (31, "Mamdani reveals plan to close New York's Rikers Island jail (WEEK)"),
    (32, "Nepal PM Balendra Shah to meet Modi on his first bilateral visit (SUN)"),
    (33, "Italian boy, 11, writes to NASA with an idea to save the Hubble telescope (WEEK)"),
    (34, "US Forest Service releases its 1982 file on alleged Bigfoot footprints (WEEK)"),
    (35, "Trafalgar Square's Christmas tree sets off from Oslo for London (SAT)"),
    (36, "Man guilty of starting the Palisades fire, one of California's deadliest (FRI)"),
    (37, "Air India / AI Express extend Jeddah flight suspensions to 24 Nov (SUN)"),
    (38, "ICMR completes 100 technology transfers at its health research summit (SUN)"),
]

CHIPS = [
    ("-10.4%", "Nasdaq week"),
    ("$81.3bn", "Anthropic IPO"),
    ("6.7", "Peru quake"),
    ("109-0", "Greenland deal"),
    ("188", "MCG record chase"),
    ("$3,518.50", "gold /oz"),
]

REGIONS = [
    ("ASIA-PACIFIC", 12), ("OCEANIA", 2), ("EUROPE", 7), ("AMERICAS", 10),
    ("MIDDLE EAST", 2), ("AFRICA", 1), ("GLOBAL", 4),
]

# Map pins: (story number, lon, lat)
PINS = [
    (1, 114.1, 22.5), (2, -74.0, 40.7), (3, 56.3, 26.7), (4, 96.2, 19.8),
    (5, -42.0, 72.0), (6, 24.7, 59.4), (7, -75.2, -11.2), (8, 30.7, 36.9),
    (9, 36.5, 45.3), (10, -122.4, 37.8), (11, 145.0, -37.8),
]

# Simplified continent outlines (lon, lat) — stylised, hand-drawn.
CONTINENTS = [
    # North America
    [(-168, 66), (-140, 70), (-125, 72), (-110, 73), (-95, 72), (-85, 70),
     (-80, 73), (-65, 62), (-55, 52), (-60, 47), (-70, 44), (-75, 35),
     (-80, 32), (-81, 25), (-90, 21), (-97, 26), (-105, 23), (-110, 28),
     (-117, 33), (-125, 40), (-124, 48), (-135, 58), (-155, 58), (-165, 60)],
    # South America
    [(-80, 10), (-75, 11), (-70, 12), (-60, 8), (-52, 5), (-50, 0), (-44, -3),
     (-35, -8), (-38, -15), (-40, -22), (-48, -28), (-52, -33), (-58, -38),
     (-62, -41), (-65, -45), (-68, -50), (-70, -54), (-73, -50), (-73, -40),
     (-72, -30), (-70, -20), (-75, -15), (-80, -6), (-81, 1)],
    # Africa
    [(-17, 15), (-16, 21), (-10, 31), (-6, 36), (0, 36), (10, 37), (20, 32),
     (32, 31), (35, 28), (43, 12), (51, 11), (48, 2), (41, -2), (40, -10),
     (35, -18), (32, -26), (28, -33), (20, -35), (17, -29), (14, -22),
     (12, -10), (9, 4), (-8, 4), (-13, 8)],
    # Eurasia
    [(-10, 37), (-9, 43), (-2, 48), (-4, 50), (2, 51), (5, 53), (8, 57),
     (10, 59), (18, 56), (21, 55), (24, 58), (28, 60), (30, 70), (40, 68),
     (50, 69), (60, 69), (70, 72), (80, 73), (90, 75), (100, 77), (110, 74),
     (120, 73), (130, 72), (140, 72), (150, 70), (160, 69), (170, 67),
     (178, 65), (178, 62), (170, 60), (162, 56), (158, 52), (150, 45),
     (142, 42), (140, 35), (135, 34), (130, 33), (127, 35), (122, 38),
     (120, 32), (122, 28), (118, 25), (110, 20), (108, 12), (105, 9),
     (103, 2), (100, 7), (98, 12), (95, 16), (92, 21), (88, 22), (85, 19),
     (80, 13), (77, 8), (73, 20), (68, 23), (62, 25), (57, 26), (52, 26),
     (48, 29), (44, 29), (40, 31), (36, 36), (30, 36), (27, 37), (23, 36),
     (19, 40), (16, 42), (12, 44), (8, 44), (3, 43), (-2, 37), (-9, 37)],
    # UK
    [(-5, 50), (-3, 53), (-5, 56), (-2, 58), (0, 53), (1, 51)],
    # Japan
    [(130, 31), (133, 34), (137, 35), (140, 36), (141, 39), (142, 44),
     (145, 44), (141, 40), (139, 36), (135, 33)],
    # Indonesia
    [(95, 5), (100, 0), (105, -5), (110, -7), (115, -8), (120, -10),
     (125, -9), (130, -4), (135, -3), (140, -8), (141, -2), (136, 1),
     (130, 1), (125, 3), (120, 1), (115, 1), (110, 0), (105, 1), (100, 5)],
    # Australia
    [(114, -22), (114, -30), (118, -35), (124, -33), (129, -32), (132, -32),
     (135, -35), (138, -35), (140, -38), (145, -38), (150, -37), (153, -30),
     (153, -27), (151, -24), (146, -19), (142, -15), (142, -11), (137, -12),
     (135, -15), (132, -12), (130, -13), (126, -14), (122, -17), (118, -20)],
    # New Zealand
    [(167, -45), (172, -41), (174, -39), (178, -38), (175, -40), (172, -43)],
    # Madagascar
    [(44, -16), (47, -15), (50, -16), (49, -20), (47, -24), (44, -25), (43, -21)],
]


def draw():
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    f_paper = font(SANS_B, 11)
    f_date = font(SERIF_B, 40)
    f_strap = font(SANS_O, 13)
    f_chip_v = font(SANS_B, 14)
    f_chip_l = font(SANS, 9)
    f_region = font(SANS_B, 11)
    f_hero_h = font(SANS_B, 15)
    f_hero_d = font(SANS, 11)
    f_tag = font(SANS_B, 9)
    f_src = font(SANS_B, 8)
    f_small_h = font(SANS_B, 11)
    f_small_d = font(SANS, 9)
    f_small_s = font(SANS_B, 8)
    f_sec = font(SANS_B, 12)
    f_list = font(SANS, 10)
    f_list_n = font(SANS_B, 10)
    f_datecheck = font(SANS, 11)
    f_datecheck_b = font(SANS_B, 11)
    f_foot = font(SANS, 10)
    f_foot_b = font(SANS_B, 10)
    f_num = font(SANS_B, 12)
    f_pin = font(SANS_B, 9)

    # ================= masthead =================
    y = 22
    d.text((M, y), "THE SUNDAY LEDGER", font=f_paper, fill=INK)
    right = "ONE DAY  ·  ONE PAGE  ·  38 STORIES"
    d.text((W - M - text_w(d, right, f_paper), y), right, font=f_paper, fill=RED)
    y = 40
    title = "Sunday 22 November 2026"
    d.text(((W - text_w(d, title, f_date)) / 2, y), title, font=f_date, fill=INK)
    y = 88
    strap = ("Shenzhen peace pact says nothing of Ukraine  ·  Nasdaq's worst week since 2020  ·  "
             "Gulf war widens to Kuwait and Bahrain")
    d.text(((W - text_w(d, strap, f_strap)) / 2, y), strap, font=f_strap, fill=INK_SOFT)
    d.line([(M, 110), (W - M, 110)], fill=INK, width=2)
    d.line([(M, 114), (W - M, 114)], fill=INK, width=1)

    # ================= stat chips =================
    chip_y, chip_h, gap = 122, 28, 8
    chip_w = (CW - gap * (len(CHIPS) - 1)) / len(CHIPS)
    for i, (val, label) in enumerate(CHIPS):
        x0 = M + i * (chip_w + gap)
        d.rounded_rectangle([x0, chip_y, x0 + chip_w, chip_y + chip_h],
                            radius=6, fill=CARD, outline=CARD_EDGE, width=1)
        vw = text_w(d, val, f_chip_v)
        lw = text_w(d, label, f_chip_l)
        cx = x0 + chip_w / 2
        d.text((cx - (vw + 5 + lw) / 2, chip_y + 6), val, font=f_chip_v, fill=RED)
        d.text((cx - (vw + 5 + lw) / 2 + vw + 5, chip_y + 8), label,
               font=f_chip_l, fill=INK_SOFT)

    # ================= region bar =================
    ry = 158
    parts = []
    total_w = 0
    for name, n in REGIONS:
        s = f"{name} {n}"
        parts.append((s, REGION_COLORS[name]))
        total_w += text_w(d, s, f_region) + 14 + 22
    total_w -= 22
    x = (W - total_w) / 2
    for s, col in parts:
        d.ellipse([x, ry + 2, x + 8, ry + 10], fill=col)
        x += 12
        d.text((x, ry), s, font=f_region, fill=INK_SOFT)
        x += text_w(d, s, f_region) + 6
        d.text((x, ry), "·", font=f_region, fill=MUTED)
        x += 16
    d.line([(M, 178), (W - M, 178)], fill=HAIR, width=1)

    # ================= hero cards =================
    hero_y, hero_h = 186, 156
    hero_w = 312
    hero_gap = (CW - 3 * hero_w) / 2
    for i, (num, region, tag, head, deck, src) in enumerate(HEROES):
        x0 = M + i * (hero_w + hero_gap)
        x1, y1 = x0 + hero_w, hero_y + hero_h
        d.rounded_rectangle([x0, hero_y, x1, y1], radius=8,
                            fill=CARD, outline=CARD_EDGE, width=1)
        strip_h = 44
        d.rounded_rectangle([x0, hero_y, x1, hero_y + strip_h], radius=8,
                            fill=REGION_COLORS[region])
        d.rectangle([x0, hero_y + strip_h - 10, x1, hero_y + strip_h],
                    fill=REGION_COLORS[region])
        draw_hero_pic(d, num, x0, hero_y, hero_w, strip_h)
        bx, by = x0 + 10, hero_y + strip_h - 11
        d.ellipse([bx, by, bx + 22, by + 22], fill=RED, outline=WHITE, width=2)
        ns = str(num)
        d.text((bx + 11 - text_w(d, ns, f_num) / 2, by + 3), ns,
               font=f_num, fill=WHITE)
        d.text((x0 + 40, hero_y + strip_h + 6), tag, font=f_tag,
               fill=REGION_COLORS[region])
        hy = hero_y + strip_h + 22
        for j, ln in enumerate(fit_lines(d, head, f_hero_h, hero_w - 20, 2,
                                         f"hero{num} head")):
            d.text((x0 + 10, hy + j * 17), ln, font=f_hero_h, fill=INK)
        dy = hy + 36
        for j, ln in enumerate(fit_lines(d, deck, f_hero_d, hero_w - 20, 3,
                                         f"hero{num} deck")):
            d.text((x0 + 10, dy + j * 13), ln, font=f_hero_d, fill=INK_SOFT)
        d.text((x0 + 10, y1 - 15), "SOURCE: " + src, font=f_src, fill=MUTED)

    # ================= small cards =================
    small_y0 = 350
    small_h, small_gap_y = 78, 8
    small_w = 234
    small_gap_x = (CW - 4 * small_w) / 3
    for idx, (num, region, tag, head, deck, src) in enumerate(SMALL):
        row, col = divmod(idx, 4)
        x0 = M + col * (small_w + small_gap_x)
        y0 = small_y0 + row * (small_h + small_gap_y)
        x1, y1 = x0 + small_w, y0 + small_h
        d.rounded_rectangle([x0, y0, x1, y1], radius=6,
                            fill=CARD, outline=CARD_EDGE, width=1)
        d.rectangle([x0, y0, x0 + 4, y1], fill=REGION_COLORS[region])
        d.text((x0 + 10, y0 + 4), str(num), font=f_num, fill=RED)
        d.text((x0 + 28, y0 + 6), tag, font=f_tag, fill=REGION_COLORS[region])
        draw_mini_pic(d, num, x1 - 30, y0 + 2, 26, 16)
        hy = y0 + 19
        for j, ln in enumerate(fit_lines(d, head, f_small_h, small_w - 20, 2,
                                         f"small{num} head")):
            d.text((x0 + 10, hy + j * 13), ln, font=f_small_h, fill=INK)
        dy = hy + 27
        for j, ln in enumerate(fit_lines(d, deck, f_small_d, small_w - 20, 2,
                                         f"small{num} deck")):
            d.text((x0 + 10, dy + j * 11), ln, font=f_small_d, fill=INK_SOFT)
        d.text((x0 + 10, y1 - 11), src, font=f_small_s, fill=MUTED)

    # ================= map + list =================
    mid_y = 522
    mid_h = 362
    map_x0, map_w = M, 400
    list_x0, list_w = M + map_w + 8, CW - map_w - 8

    # ---- map panel ----
    d.rounded_rectangle([map_x0, mid_y, map_x0 + map_w, mid_y + mid_h],
                        radius=8, fill=CARD, outline=CARD_EDGE, width=1)
    d.text((map_x0 + 12, mid_y + 8), "WHERE IT HAPPENED", font=f_sec, fill=INK)
    d.text((map_x0 + 12, mid_y + 26),
           "Numbered pins mark the dateline of each story.",
           font=f_small_d, fill=MUTED)
    mx0, my0 = map_x0 + 10, mid_y + 46
    mx1, my1 = map_x0 + map_w - 10, mid_y + mid_h - 44
    d.rounded_rectangle([mx0, my0, mx1, my1], radius=6, fill=OCEAN,
                        outline=LAND_EDGE, width=1)
    for lon in range(-150, 181, 30):
        gx = mx0 + (lon + 180) / 360 * (mx1 - mx0)
        d.line([(gx, my0), (gx, my1)], fill=(196, 216, 230), width=1)
    for lat in (-60, -30, 0, 30, 60):
        gy = my0 + (85 - lat) / 145 * (my1 - my0)
        d.line([(mx0, gy), (mx1, gy)], fill=(196, 216, 230), width=1)

    def project(lon, lat):
        return (mx0 + (lon + 180) / 360 * (mx1 - mx0),
                my0 + (85 - lat) / 145 * (my1 - my0))

    for poly in CONTINENTS:
        pts = [project(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_EDGE)
    # Pins 4 (Myanmar) and 9 (Kerch) sit close to neighbours at true
    # position, so they get a leader line to an offset label circle.
    PIN_OFFSETS = {4: (-20, 14), 9: (20, -14)}
    for num, lon, lat in PINS:
        px, py = project(lon, lat)
        r = 10
        if num in PIN_OFFSETS:
            dx, dy = PIN_OFFSETS[num]
            d.ellipse([px - 3, py - 3, px + 3, py + 3], fill=RED,
                      outline=WHITE, width=1)
            d.line([(px, py), (px + dx, py + dy)], fill=RED, width=1)
            px, py = px + dx, py + dy
        d.ellipse([px - r, py - r, px + r, py + r], fill=RED,
                  outline=WHITE, width=2)
        ns = str(num)
        d.text((px - text_w(d, ns, f_pin) / 2, py - 6), ns,
               font=f_pin, fill=WHITE)
    legend = [
        "Pins: 1 Shenzhen · 2 New York · 3 Qeshm · 4 Myanmar · 5 Greenland · 6 Tallinn",
        "7 Junin · 8 Antalya · 9 Kerch · 10 San Francisco · 11 Melbourne",
    ]
    for i, ln in enumerate(legend):
        if text_w(d, ln, f_small_d) > map_w - 24:
            warn(f"map legend line {i + 1} too wide: {ln!r}")
        d.text((map_x0 + 12, mid_y + mid_h - 32 + i * 11), ln,
               font=f_small_d, fill=MUTED)

    # ---- list panel ----
    d.rounded_rectangle([list_x0, mid_y, list_x0 + list_w, mid_y + mid_h],
                        radius=8, fill=CARD, outline=CARD_EDGE, width=1)
    d.text((list_x0 + 12, mid_y + 8),
           "ALSO IN THE LEDGER — 27 MORE STORIES", font=f_sec, fill=INK)
    d.text((list_x0 + 12, mid_y + 26),
           "Numbered 12–38 · tags show the day each story broke.",
           font=f_small_d, fill=MUTED)
    ly = mid_y + 44
    lh = 11.8
    for num, text in LIST:
        ns = f"{num}."
        d.text((list_x0 + 12, ly), ns, font=f_list_n, fill=RED)
        nx = list_x0 + 12 + text_w(d, ns, f_list_n) + 6
        f_use = fit_one_line(d, text, f_list, list_x0 + list_w - 10 - nx,
                             f"list{num}")
        d.text((nx, ly), text, font=f_use, fill=INK_SOFT)
        ly += lh

    # ================= DATE CHECK =================
    dc_y, dc_h = 892, 56
    d.rounded_rectangle([M, dc_y, W - M, dc_y + dc_h], radius=8,
                        fill=RED_SOFT, outline=RED, width=1)
    d.text((M + 12, dc_y + 7), "DATE CHECK — ", font=f_datecheck_b, fill=RED)
    x = M + 12 + text_w(d, "DATE CHECK — ", f_datecheck_b)
    dc1 = ("SUN = Sunday 22 Nov · SAT = Saturday 21 Nov · FRI = Friday 20 Nov · "
           "WED = Wednesday 19 Nov")
    dc2 = ("WEEK = earlier in the week, first reported or confirmed this week.")
    dc3 = ("A story counts here only if it happened, or was first reported, "
           "on its tagged day.")
    if text_w(d, dc1, f_datecheck) > (W - M - 12) - x:
        warn(f"datecheck line 1 too wide: {dc1!r}")
    if text_w(d, dc2, f_datecheck) > W - 2 * M - 24:
        warn(f"datecheck line 2 too wide: {dc2!r}")
    if text_w(d, dc3, f_datecheck) > W - 2 * M - 24:
        warn(f"datecheck line 3 too wide: {dc3!r}")
    d.text((x, dc_y + 7), dc1, font=f_datecheck, fill=INK)
    d.text((M + 12, dc_y + 25), dc2, font=f_datecheck, fill=INK)
    d.text((M + 12, dc_y + 41), dc3, font=f_datecheck, fill=INK_SOFT)

    # ================= footer =================
    fy = 956
    f1 = ("Every story here happened, or was first reported, on its tagged day. "
          "Sources are named beside each story.")
    d.text(((W - text_w(d, f1, f_foot_b)) / 2, fy), f1, font=f_foot_b, fill=INK)
    f2 = "Sources: AP, Reuters, BBC, USGS, AAP, AFP — checked 22 Nov 2026."
    d.text(((W - text_w(d, f2, f_foot)) / 2, fy + 15), f2, font=f_foot, fill=MUTED)
    f3 = "THE SUNDAY LEDGER · 38 STORIES · 7 REGIONS · DRAWN 22 NOVEMBER 2026"
    d.text(((W - text_w(d, f3, f_foot)) / 2, fy + 30), f3, font=f_foot, fill=MUTED)

    return img


def draw_hero_pic(d, num, x0, y0, w, h):
    """Original pictograms inside the hero colour strip."""
    if num == 1:
        # Dove + olive branch + four stars (four-point peace declaration)
        # dove facing right: body, raised head, beak, wing, fanned tail
        cx, cy = x0 + 48, y0 + h // 2 + 2
        d.ellipse([cx - 20, cy - 8, cx + 14, cy + 8], outline=WHITE, width=2)
        d.ellipse([cx + 10, cy - 16, cx + 22, cy - 4], outline=WHITE, width=2)
        d.polygon([(cx + 21, cy - 12), (cx + 29, cy - 10), (cx + 21, cy - 8)],
                  fill=WHITE)
        d.point((cx + 16, cy - 12), fill=WHITE)
        d.arc([cx - 10, cy - 6, cx + 8, cy + 6], 200, 340, fill=WHITE, width=2)
        d.line([(cx - 20, cy - 2), (cx - 32, cy - 10)], fill=WHITE, width=2)
        d.line([(cx - 20, cy + 2), (cx - 33, cy + 2)], fill=WHITE, width=2)
        d.line([(cx - 20, cy + 5), (cx - 31, cy + 12)], fill=WHITE, width=2)
        # olive branch
        bx, by = x0 + w - 78, y0 + h - 12
        d.line([(bx, by), (bx + 58, by - 18)], fill=WHITE, width=2)
        for i in range(4):
            lx, ly = bx + 10 + i * 13, by - 4 - i * 4
            d.ellipse([lx - 4, ly - 3, lx + 4, ly + 3], outline=WHITE, width=1)
        # four stars
        for sx, sy in [(x0 + w - 34, y0 + 8), (x0 + w - 22, y0 + 14),
                       (x0 + w - 44, y0 + 18), (x0 + w - 28, y0 + 26)]:
            for dx, dy in [(0, -4), (3, -3), (4, 0), (3, 3), (0, 4),
                           (-3, 3), (-4, 0), (-3, -3)]:
                d.line([(sx, sy), (sx + dx, sy + dy)], fill=WHITE, width=1)
    elif num == 2:
        # Falling market chart: axes, descending line, down arrow, bars
        ox, oy = x0 + 22, y0 + h - 8
        d.line([(ox, y0 + 6), (ox, oy)], fill=WHITE, width=2)
        d.line([(ox, oy), (x0 + w - 14, oy)], fill=WHITE, width=2)
        # candlestick bars falling
        bars = [(30, 14, 26), (52, 20, 18), (74, 26, 12), (96, 30, 8)]
        for bx, top, hh in bars:
            d.rectangle([x0 + bx, y0 + top, x0 + bx + 10, y0 + top + hh],
                        outline=WHITE, width=1)
            d.line([(x0 + bx + 5, y0 + top - 4), (x0 + bx + 5, y0 + top + hh + 4)],
                   fill=WHITE, width=1)
        # descending trend line with arrowhead
        pts = [(x0 + 130, y0 + 8), (x0 + 165, y0 + 14), (x0 + 200, y0 + 12),
               (x0 + 235, y0 + 22), (x0 + 268, y0 + 20), (x0 + 292, y0 + 32)]
        d.line(pts, fill=WHITE, width=2)
        ax, ay = x0 + 292, y0 + 32
        d.polygon([(ax, ay + 8), (ax - 8, ay - 2), (ax + 2, ay - 2)],
                  fill=WHITE)
        d.text((x0 + 130, y0 + 22), "-10.4%", font=font(SANS_B, 13), fill=WHITE)
    else:
        # Gulf: explosion bursts over waves + a tanker silhouette
        base = y0 + h - 8
        for sx, sy in [(x0 + 60, y0 + 12), (x0 + 150, y0 + 8), (x0 + 240, y0 + 13)]:
            for dx, dy in [(0, -7), (5, -5), (7, 0), (5, 5), (0, 7),
                           (-5, 5), (-7, 0), (-5, -5)]:
                d.line([(sx, sy), (sx + dx, sy + dy)], fill=WHITE, width=2)
            d.ellipse([sx - 2, sy - 2, sx + 2, sy + 2], fill=WHITE)
        # tanker
        tx, ty = x0 + 110, base - 14
        d.rectangle([tx, ty, tx + 90, ty + 10], outline=WHITE, width=2)
        d.rectangle([tx + 66, ty - 8, tx + 84, ty], outline=WHITE, width=2)
        d.line([(tx + 70, ty - 8), (tx + 70, ty - 13)], fill=WHITE, width=2)
        # waves
        for wx in range(int(x0 + 16), int(x0 + w - 16), 26):
            d.arc([wx, base - 6, wx + 22, base + 6], 180, 360, fill=WHITE, width=2)


def draw_mini_pic(d, num, x, y, w, h):
    """Tiny 26x16 pictogram for small cards, drawn in muted ink.
    Fits above the headline (headline starts 2px below its bottom)."""
    c = (110, 112, 108)
    if num == 4:  # scales of justice
        d.line([(x + w // 2, y + 1), (x + w // 2, y + 13)], fill=c, width=1)
        d.line([(x + 3, y + 3), (x + w - 3, y + 3)], fill=c, width=1)
        d.line([(x + 3, y + 3), (x + 1, y + 9)], fill=c, width=1)
        d.line([(x + 3, y + 3), (x + 5, y + 9)], fill=c, width=1)
        d.line([(x + 1, y + 9), (x + 5, y + 9)], fill=c, width=1)
        d.line([(x + w - 3, y + 3), (x + w - 5, y + 9)], fill=c, width=1)
        d.line([(x + w - 3, y + 3), (x + w - 1, y + 9)], fill=c, width=1)
        d.line([(x + w - 5, y + 9), (x + w - 1, y + 9)], fill=c, width=1)
        d.line([(x + 8, y + 13), (x + w - 8, y + 13)], fill=c, width=1)
    elif num == 5:  # flag
        d.line([(x + 5, y + 1), (x + 5, y + 14)], fill=c, width=1)
        d.polygon([(x + 5, y + 1), (x + 22, y + 4), (x + 5, y + 8)],
                  outline=c, width=1)
    elif num == 6:  # border barrier
        d.line([(x + 4, y + 1), (x + 4, y + 14)], fill=c, width=1)
        d.line([(x + w - 4, y + 1), (x + w - 4, y + 14)], fill=c, width=1)
        d.line([(x + 4, y + 5), (x + w - 4, y + 5)], fill=c, width=1)
        d.line([(x + 4, y + 10), (x + w - 4, y + 10)], fill=c, width=1)
        d.line([(x + 4, y + 5), (x + w - 4, y + 10)], fill=c, width=1)
        d.line([(x + w - 4, y + 5), (x + 4, y + 10)], fill=c, width=1)
    elif num == 7:  # seismograph
        pts = [(x + 2, y + 8), (x + 6, y + 7), (x + 9, y + 9),
               (x + 12, y + 2), (x + 15, y + 14), (x + 18, y + 6),
               (x + 21, y + 9), (x + 24, y + 8)]
        d.line(pts, fill=c, width=1)
    elif num == 8:  # globe + leaf
        d.ellipse([x + 4, y + 1, x + 17, y + 13], outline=c, width=1)
        d.ellipse([x + 4, y + 6, x + 17, y + 9], outline=c, width=1)
        d.ellipse([x + 16, y + 9, x + 24, y + 15], outline=c, width=1)
    elif num == 9:  # bridge
        d.arc([x + 2, y + 2, x + 24, y + 15], 180, 360, fill=c, width=1)
        d.line([(x + 2, y + 9), (x + 24, y + 9)], fill=c, width=1)
        d.line([(x + 6, y + 9), (x + 6, y + 14)], fill=c, width=1)
        d.line([(x + 20, y + 9), (x + 20, y + 14)], fill=c, width=1)
    elif num == 10:  # AI chip
        d.rectangle([x + 6, y + 3, x + 20, y + 13], outline=c, width=1)
        for px in (10, 15, 20):
            d.line([(px, y + 1), (px, y + 3)], fill=c, width=1)
            d.line([(px, y + 13), (px, y + 15)], fill=c, width=1)
        d.text((x + 10, y + 4), "AI", font=font(SANS_B, 7), fill=c)
    else:  # cricket bat + ball
        d.line([(x + 6, y + 14), (x + 18, y + 2)], fill=c, width=2)
        d.ellipse([x + 18, y + 9, x + 23, y + 14], outline=c, width=1)


def main():
    img = draw()
    out = Path(__file__).resolve().parent / "entry.png"
    img.save(out, optimize=True)
    size = out.stat().st_size
    print(f"Wrote {out} ({size} bytes, {img.size[0]}x{img.size[1]})")
    if size >= 1024 * 1024:
        print("ERROR: entry.png is >= 1 MiB", file=sys.stderr)
        sys.exit(1)
    if WARNINGS:
        print(f"{len(WARNINGS)} fit warning(s) — see stderr", file=sys.stderr)
    else:
        print("FIT OK: no text overflow warnings")


if __name__ == "__main__":
    main()
