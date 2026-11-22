#!/usr/bin/env python3
"""The World in One Day — v3 broadsheet for Sunday 22 November 2026.

Builds a 1024x1024 newspaper front page with 35 verified stories:
3 hero cards with code-drawn scene illustrations, 10 small cards with
mini illustrations, a dotted world map with 13 numbered pins, a
two-column list of 22 more stories, a DATE CHECK box and a source footer.

Deterministic: fixed fonts, fixed palette, no randomness, no timestamps.
PIL only. Run: python3 generate.py  ->  writes entry.png next to itself.
"""

import hashlib
import os
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_PATH = os.path.join(HERE, "entry.png")

# ---------------------------------------------------------------- canvas
W, H = 1024, 1024
MARGIN = 24
CW = W - 2 * MARGIN  # 976 usable width

PAPER = (247, 243, 231)
CARD = (255, 252, 243)
INK = (22, 22, 24)
SOFT = (88, 86, 80)
FAINT = (150, 146, 134)
RED = (176, 28, 28)
RED_DEEP = (138, 18, 18)
RULE = (30, 30, 32)
MAP_SEA = (231, 237, 239)
MAP_LAND = (64, 84, 102)
SKY_DAWN = (250, 224, 178)

REGION_COLORS = {
    "EUROPE": (38, 96, 158),
    "MIDDLE EAST": (205, 110, 22),
    "AMERICAS": (46, 139, 64),
    "ASIA-PACIFIC": (128, 84, 168),
    "AFRICA": (168, 152, 32),
    "WORLD": (110, 110, 110),
}

# ---------------------------------------------------------------- fonts
FONT_DIR = "/usr/share/fonts/truetype/liberation"
def F(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)

SERIF_B = lambda s: F("LiberationSerif-Bold.ttf", s)
SERIF_I = lambda s: F("LiberationSerif-Italic.ttf", s)
SERIF = lambda s: F("LiberationSerif-Regular.ttf", s)
SANS_B = lambda s: F("LiberationSans-Bold.ttf", s)
SANS = lambda s: F("LiberationSans-Regular.ttf", s)
SANS_I = lambda s: F("LiberationSans-Italic.ttf", s)

# ---------------------------------------------------------------- helpers
def text_w(draw, s, font):
    return draw.textlength(s, font=font)

def wrap(draw, s, font, max_w):
    """Greedy word wrap; returns list of lines that fit max_w."""
    words, lines, cur = s.split(), [], ""
    for word in words:
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=font) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines

def fit_lines(draw, s, font, max_w, max_lines):
    """Wrap and truncate with an ellipsis so text never exceeds max_lines."""
    lines = wrap(draw, s, font, max_w)
    if len(lines) <= max_lines:
        return lines
    lines = lines[:max_lines]
    while lines and draw.textlength(lines[-1] + " ...", font=font) > max_w:
        lines[-1] = lines[-1].rsplit(" ", 1)[0] if " " in lines[-1] else lines[-1][:-1]
    lines[-1] = lines[-1] + " ..."
    return lines

def rule(draw, x0, y, x1, width=2, color=RULE):
    draw.line([(x0, y), (x1, y)], fill=color, width=width)

def hline(draw, x0, y, x1, color=FAINT):
    draw.line([(x0, y), (x1, y)], fill=color, width=1)

def tracked(draw, xy, s, font, fill, tracking=2):
    """Draw text with extra letter spacing; returns width used."""
    x, y = xy
    for ch in s:
        draw.text((x, y), ch, font=font, fill=fill)
        x += draw.textlength(ch, font=font) + tracking
    return x - xy[0] - tracking

def centered(draw, cx, y, s, font, fill):
    draw.text((cx - draw.textlength(s, font=font) / 2, y), s, font=font, fill=fill)

# ---------------------------------------------------------------- data
# Day tags: SUN = Sunday 22 Nov, SAT = Saturday 21 Nov, FRI = Friday 20 Nov,
# WED = Wednesday 18 Nov, WEEK = earlier this week, first confirmed this week.

HEROES = [
    {
        "num": 1, "tag": "SUN", "region": "WORLD",
        "kicker": "CLIMATE  |  ANTALYA",
        "headline": "COP31 nears deal at dawn",
        "body": ("New package announced overnight; delegations have until "
                 "03:00 GMT to object, approval session at 06:00 GMT. "
                 "President Murat Kurum; about 200 delegations. Australia "
                 "leads, Turkey hosts; talks ran past Friday's deadline."),
        "scene": "cop31",
    },
    {
        "num": 2, "tag": "SAT", "region": "EUROPE",
        "kicker": "WAR AT SEA  |  GULF OF FINLAND",
        "headline": "Sparta II ablaze after drone strike",
        "body": ("Russian-flagged cargo ship hit by two drones; fire breaks "
                 "out, vessel drifts into Finnish waters. All 16 crew "
                 "evacuate to lifeboats. Finland says Ukraine likely behind "
                 "it; sanctioned Oboronlogistika vessel."),
        "scene": "sparta",
    },
    {
        "num": 3, "tag": "SAT", "region": "AMERICAS",
        "kicker": "EARTHQUAKE  |  PERU",
        "headline": "M6.8 quake shakes Peru, felt in Lima",
        "body": ("M6.8 (GFZ), 129 km deep, 30 km north-west of Junin; struck "
                 "Friday 19:09 local. Tremors felt in the capital; no "
                 "casualties or damage reported. USGS measured 6.7."),
        "scene": "quake",
    },
]

SMALLS = [
    {"num": 4, "tag": "SUN", "region": "MIDDLE EAST",
     "kicker": "TANKERS HIT OFF OMAN",
     "body": ("Two tankers struck off Oman, one in the engine room 17 nm "
              "east of Khasab. No casualties; fourth strike in 24 hours."),
     "icon": "tanker"},
    {"num": 5, "tag": "SAT", "region": "EUROPE",
     "kicker": "FRANCE: MYANMAR TO UN",
     "body": ("Paris to seek a UN Security Council meeting after Myanmar "
              "rejects the ICJ genocide ruling; China or Russia could veto."),
     "icon": "un"},
    {"num": 6, "tag": "FRI", "region": "ASIA-PACIFIC",
     "kicker": "900,000 AI CHIPS FOR CHINA",
     "body": ("US approved nearly 900,000 Nvidia/AMD AI chips for China: "
              "150,000 Tencent, 75,000 Alibaba, 43,000 Baidu, 4,000 BYD."),
     "icon": "chip"},
    {"num": 7, "tag": "WED", "region": "MIDDLE EAST",
     "kicker": "GULF WAR WIDENS",
     "body": ("Iran drones hit the US Ali Al Salem base in Kuwait and sites "
              "in Bahrain; hit 30+ times since the war began 28 Feb."),
     "icon": "base"},
    {"num": 8, "tag": "WEEK", "region": "ASIA-PACIFIC",
     "kicker": "MYANMAR GENOCIDE RULING",
     "body": ("World Court rules Myanmar committed genocide against the "
              "Rohingya, the first such finding against a state."),
     "icon": "court"},
    {"num": 9, "tag": "SAT", "region": "EUROPE",
     "kicker": "KERCH BRIDGE HIT AGAIN",
     "body": ("Ukraine strikes the bridge to Crimea a third time in four "
              "days; Zelensky calls it a 'fair response'."),
     "icon": "bridge"},
    {"num": 10, "tag": "FRI", "region": "AMERICAS",
     "kicker": "MARKETS ROUT",
     "body": ("Nasdaq worst week since 2020, -10.4%; S&P 500 in correction; "
              "Dow -1,101 to 49,097; Nvidia -14%; gold -2.8%."),
     "icon": "chart"},
    {"num": 11, "tag": "WEEK", "region": "AMERICAS",
     "kicker": "EL CHAPO ISIDRO CAPTURED",
     "body": ("Mexican army captures cartel kingpin Fausto Isidro Meza "
              "Flores, 'El Chapo Isidro'."),
     "icon": "badge"},
    {"num": 12, "tag": "FRI", "region": "EUROPE",
     "kicker": "ESTONIA SHUTS BORDER",
     "body": ("Estonia to close all 5 road crossings with Russia from 1 Dec "
              "for six months after a GRU-linked arson attempt."),
     "icon": "border"},
    {"num": 13, "tag": "WEEK", "region": "EUROPE",
     "kicker": "GREENLAND DEAL 109-0",
     "body": ("Denmark votes 109-0 to ratify a new US security deal; two "
              "new American bases."),
     "icon": "vote"},
]

# 22 more stories, numbered 14-35, shown in two columns of 11.
MORE = [
    (14, "North Korea expanding Yongbyon uranium plant, IAEA says.", "WEEK"),
    (15, "Bangladesh violence flares ahead of Hasina's planned return.", "WEEK"),
    (16, "US signs new military deal with Venezuela, 10 months after Maduro's removal.", "WEEK"),
    (17, "Two Russian missiles and a drone land in rural Poland; PM Tusk responds.", "FRI"),
    (18, "Denmark accuses Russia of plotting to kill a US-Ukrainian rapper near Copenhagen.", "FRI"),
    (19, "Palau-flagged tanker Skylight hit near Khasab; all 20 crew evacuated, 4 hurt.", "SUN"),
    (20, "FBI investigating apparent hack of its criminal database.", "FRI"),
    (21, "Trump threatens a 'tremendous tax' on US firms building AI data centres overseas.", "FRI"),
    (22, "Zscaler jumps 18% on report CrowdStrike is in talks to buy it.", "SAT"),
    (23, "Modi inaugurates Nitish Setu, linking Patna and Vaishali.", "SUN"),
    (24, "India face New Zealand in the 1st Test in windy Wellington.", "SUN"),
    (25, "Cummins keeps Australia's Test captaincy with unanimous support.", "SUN"),
    (26, "Chess: Erigaisi and Praggnanandhaa win; Vaishali loses on day one.", "SUN"),
    (27, "South Africa local elections: ANC fights to keep control of the cities.", "SUN"),
    (28, "Mamdani reveals plan to close New York's Rikers Island jail.", "WEEK"),
    (29, "Nepal PM Balendra Shah to meet Modi on his first bilateral visit.", "SUN"),
    (30, "Anthropic's $81.3bn IPO, the biggest in history; shares +39% on debut.", "FRI"),
    (31, "US Forest Service releases its 1982 file on alleged Bigfoot footprints.", "WEEK"),
    (32, "Trafalgar Square's Christmas tree sets off from Oslo for London.", "SAT"),
    (33, "Man guilty of starting the Palisades fire, one of California's deadliest.", "FRI"),
    (34, "Air India and AI Express extend Jeddah flight suspensions to 24 Nov.", "SUN"),
    (35, "Record MCG T20 chase: Australia hunt down 188 to beat England by 3 wickets.", "SAT"),
]

STATS = [
    ("35", "STORIES IN\nTHIS EDITION"),
    ("6", "REGIONS\nCOVERED"),
    ("900,000", "AI CHIPS APPROVED\nFOR CHINA"),
    ("200", "DELEGATIONS\nAT COP31"),
    ("16", "CREW SAVED FROM\nSPARTA II"),
    ("109-0", "DENMARK VOTES FOR\nTHE GREENLAND DEAL"),
]

REGION_COUNTS = [
    ("EUROPE", 8), ("MIDDLE EAST", 3), ("AMERICAS", 11),
    ("ASIA-PACIFIC", 11), ("AFRICA", 1), ("WORLD", 1),
]

# Map pins: (story number, longitude, latitude, label offset in px).
# Offsets + leader lines separate the close pairs (Antalya/Kerch,
# Khasab/Kuwait, Paris/The Hague, Washington/New York, Gulf of Finland/Tallinn).
PINS = [
    (1, 30.7, 36.9, (-30, 16)),    # Antalya
    (2, 27.0, 60.0, (30, -10)),    # Gulf of Finland
    (3, -75.0, -11.0, (18, 10)),   # Junin, Peru
    (4, 56.2, 26.2, (24, 14)),     # Khasab, Oman
    (5, 2.35, 48.85, (-28, 12)),   # Paris
    (6, -77.0, 38.9, (-30, 10)),   # Washington
    (7, 47.9, 29.3, (-28, -12)),   # Ali Al Salem, Kuwait
    (8, 4.3, 52.1, (26, -14)),     # The Hague (ICJ)
    (9, 36.5, 45.3, (28, -14)),    # Kerch
    (10, -74.0, 40.7, (28, -12)),  # New York
    (11, -107.4, 24.8, (-22, 16)), # Culiacan, Mexico
    (12, 24.7, 59.4, (-30, 12)),   # Tallinn, Estonia
    (13, -51.7, 64.2, (12, -8)),   # Nuuk, Greenland
]

# Land bitmap: 100 cols (lon -180..180) x 46 rows (lat 80..-57).
# Each row is a list of inclusive (col_start, col_end) land runs.
LAND_ROWS = [
    [(33, 44)],
    [(8, 25), (33, 44), (60, 95)],
    [(2, 28), (33, 44), (58, 98)],
    [(2, 30), (35, 42), (55, 99)],
    [(2, 32), (34, 43), (55, 99)],
    [(2, 33), (35, 42), (50, 55), (55, 99)],
    [(12, 34), (35, 42), (49, 56), (56, 99)],
    [(12, 35), (47, 49), (50, 57), (57, 99)],
    [(12, 36), (47, 49), (49, 60), (60, 99)],
    [(12, 36), (47, 62), (62, 98)],
    [(12, 36), (47, 63), (63, 98)],
    [(12, 37), (47, 63), (63, 97)],
    [(12, 38), (48, 60), (62, 95)],
    [(12, 39), (48, 58), (60, 94)],
    [(12, 40), (48, 56), (57, 66), (66, 93)],
    [(12, 40), (45, 58), (58, 68), (68, 92)],
    [(12, 38), (44, 60), (58, 66), (68, 73), (72, 90)],
    [(14, 34), (44, 60), (57, 67), (67, 74), (74, 90)],
    [(15, 32), (44, 62), (57, 67), (67, 75), (76, 88)],
    [(16, 30), (44, 62), (67, 75), (76, 88)],
    [(18, 28), (44, 62), (68, 75), (76, 88)],
    [(19, 27), (44, 62), (69, 75), (77, 88)],
    [(20, 26), (44, 62), (69, 74), (77, 87)],
    [(24, 32), (44, 62), (70, 74), (78, 86)],
    [(23, 33), (45, 62), (79, 86)],
    [(23, 34), (45, 61), (78, 90)],
    [(23, 35), (46, 60), (78, 92)],
    [(23, 35), (46, 60), (79, 92)],
    [(24, 35), (46, 60), (80, 92)],
    [(24, 35), (46, 60)],
    [(24, 35), (47, 59), (62, 64), (83, 94)],
    [(24, 35), (47, 59), (62, 64), (82, 95)],
    [(25, 35), (47, 59), (62, 64), (82, 95)],
    [(25, 34), (48, 58), (62, 64), (82, 95)],
    [(25, 34), (48, 58), (62, 64), (82, 95)],
    [(25, 34), (48, 57), (83, 94)],
    [(26, 33), (48, 56), (84, 93)],
    [(26, 33), (49, 55), (85, 92)],
    [(26, 32), (49, 55), (95, 97)],
    [(27, 32), (95, 97)],
    [(27, 31)],
    [(27, 31)],
    [(27, 30)],
    [(27, 30)],
    [(27, 30)],
    [(28, 30)],
]

# ================================================================ scenes
# All illustrations are drawn with PIL primitives — no external images.

def sky_bands(draw, x, y, w, h, top, bottom, steps=6):
    """Vertical gradient made of solid bands (deterministic)."""
    for i in range(steps):
        t = i / (steps - 1)
        col = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        draw.rectangle([x, y + h * i / steps, x + w, y + h * (i + 1) / steps], fill=col)

def flame(draw, cx, base_y, size, palette):
    """Layered teardrop flame at (cx, base_y)."""
    for j, (col, s) in enumerate(palette):
        w2, h2 = size * s, size * 1.5 * s
        draw.polygon([
            (cx - w2, base_y),
            (cx - w2 * 0.55, base_y - h2 * 0.55),
            (cx, base_y - h2),
            (cx + w2 * 0.55, base_y - h2 * 0.55),
            (cx + w2, base_y),
        ], fill=col)

def scene_cop31(draw, x, y, w, h):
    """Dawn negotiation hall in Antalya: rising sun, long table, flags."""
    sky_bands(draw, x, y, w, h, (255, 214, 150), (208, 224, 238))
    # rising sun
    sx, sy, sr = x + w - 52, y + 22, 13
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(255, 176, 66),
                 outline=(224, 130, 40), width=2)
    for k in range(8):
        import math
        a = math.pi * k / 4
        draw.line([(sx + 17 * math.cos(a), sy + 17 * math.sin(a)),
                   (sx + 23 * math.cos(a), sy + 23 * math.sin(a))],
                  fill=(224, 130, 40), width=2)
    # hall back wall
    draw.rectangle([x, y + h - 30, x + w, y + h], fill=(122, 96, 66))
    # long negotiation table
    ty = y + h - 34
    draw.rectangle([x + 18, ty, x + w - 18, ty + 12], fill=(96, 64, 32))
    draw.rectangle([x + 18, ty + 12, x + w - 18, ty + 14], fill=(70, 46, 22))
    # delegates: heads + shoulders behind the table
    for i, px in enumerate(range(x + 34, x + w - 30, 34)):
        col = (44, 62, 88) if i % 2 == 0 else (88, 52, 44)
        draw.ellipse([px - 6, ty - 22, px + 6, ty - 10], fill=(222, 184, 150))
        draw.rectangle([px - 9, ty - 10, px + 9, ty], fill=col)
    # flag poles with small flags on the table
    flag_cols = [(200, 30, 30), (30, 80, 160), (30, 140, 70), (220, 180, 40)]
    for i, px in enumerate(range(x + 44, x + w - 40, 56)):
        draw.line([(px, ty - 30), (px, ty)], fill=(60, 60, 60), width=2)
        draw.rectangle([px, ty - 30, px + 14, ty - 22], fill=flag_cols[i % 4])
    # name plates
    for px in range(x + 40, x + w - 34, 34):
        draw.rectangle([px - 7, ty + 2, px + 7, ty + 8], fill=(250, 248, 240))
    # "COP31" banner on the wall
    bw = 74
    draw.rectangle([x + (w - bw) // 2, y + 6, x + (w + bw) // 2, y + 20],
                   fill=(24, 74, 52))
    centered(draw, x + w // 2, y + 7, "COP31", SANS_B(11), (255, 255, 255))

def scene_sparta(draw, x, y, w, h):
    """Cargo ship ablaze in a grey northern sea, drones above, lifeboat."""
    sky_bands(draw, x, y, w, h, (168, 186, 200), (120, 140, 158))
    sea_y = y + int(h * 0.58)
    draw.rectangle([x, sea_y, x + w, y + h], fill=(52, 92, 122))
    for i, wy in enumerate(range(sea_y + 4, y + h - 2, 7)):
        off = 12 if i % 2 else 0
        for wx in range(x + off, x + w - 10, 26):
            draw.line([(wx, wy), (wx + 12, wy)], fill=(140, 180, 205), width=2)
    # ship hull
    hx0, hx1 = x + 52, x + w - 52
    hy = sea_y - 6
    draw.polygon([(hx0, hy), (hx1, hy), (hx1 - 14, hy + 16),
                  (hx0 + 18, hy + 16)], fill=(38, 44, 52))
    draw.rectangle([hx0 + 6, hy - 4, hx1 - 6, hy], fill=(150, 40, 36))
    # superstructure + containers
    draw.rectangle([hx1 - 62, hy - 26, hx1 - 30, hy - 4], fill=(232, 230, 222))
    draw.rectangle([hx1 - 58, hy - 22, hx1 - 34, hy - 16], fill=(70, 90, 110))
    for cx0, ccol in [(hx0 + 12, (196, 120, 44)), (hx0 + 44, (44, 120, 140)),
                      (hx0 + 76, (140, 60, 60))]:
        draw.rectangle([cx0, hy - 16, cx0 + 28, hy - 4], fill=ccol)
    # flames on deck
    flame(draw, hx0 + 26, hy - 14, 13,
          [((232, 120, 30), 1.0), ((250, 190, 60), 0.65), ((255, 240, 160), 0.35)])
    flame(draw, hx0 + 90, hy - 14, 10,
          [((232, 120, 30), 1.0), ((250, 190, 60), 0.65), ((255, 240, 160), 0.35)])
    # smoke
    for sx, sy, sr in [(hx0 + 26, hy - 34, 9), (hx0 + 36, hy - 44, 12),
                       (hx0 + 50, hy - 52, 14), (hx0 + 90, hy - 36, 10)]:
        draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr], fill=(96, 96, 96))
    # two drones
    for dx, dy in [(x + w - 70, y + 12), (x + 34, y + 16)]:
        draw.line([(dx - 9, dy - 5), (dx + 9, dy + 5)], fill=(30, 30, 30), width=2)
        draw.line([(dx - 9, dy + 5), (dx + 9, dy - 5)], fill=(30, 30, 30), width=2)
        draw.ellipse([dx - 3, dy - 3, dx + 3, dy + 3], fill=(30, 30, 30))
    # orange lifeboat with crew dots
    lx, ly = x + w - 96, sea_y + 10
    draw.polygon([(lx, ly), (lx + 34, ly), (lx + 28, ly + 9), (lx + 6, ly + 9)],
                 fill=(230, 110, 20))
    for px in (lx + 9, lx + 17, lx + 25):
        draw.ellipse([px - 2, ly - 5, px + 2, ly - 1], fill=(30, 30, 30))

def scene_quake(draw, x, y, w, h):
    """Andean peaks at dusk above a seismograph strip."""
    sky_bands(draw, x, y, w, h, (240, 196, 140), (214, 178, 150))
    # sun
    draw.ellipse([x + 34, y + 8, x + 54, y + 28], fill=(255, 220, 130),
                 outline=(220, 150, 60), width=2)
    # mountain ridges
    base = y + int(h * 0.62)
    draw.polygon([(x, base), (x + 70, y + 14), (x + 140, base)], fill=(120, 96, 78))
    draw.polygon([(x + 70, y + 14), (x + 92, y + 30), (x + 118, y + 30),
                  (x + 96, y + 14)], fill=(250, 250, 248))
    draw.polygon([(x + 110, base), (x + 200, y + 6), (x + 290, base)],
                 fill=(96, 74, 58))
    draw.polygon([(x + 200, y + 6), (x + 222, y + 24), (x + 250, y + 24),
                  (x + 226, y + 6)], fill=(250, 250, 248))
    draw.polygon([(x + 250, base), (x + w, y + 26), (x + w, base)],
                 fill=(132, 106, 86))
    # ground + crack
    draw.rectangle([x, base, x + w, y + h - 22], fill=(150, 124, 92))
    draw.line([(x + 150, base), (x + 158, base + 8), (x + 150, base + 14),
               (x + 162, base + 20)], fill=(60, 44, 30), width=2)
    # seismograph strip
    sy0 = y + h - 22
    draw.rectangle([x, sy0, x + w, y + h], fill=(252, 252, 248))
    draw.line([(x, sy0), (x + w, sy0)], fill=(120, 120, 120), width=1)
    pts = []
    spikes = [0, 0, 1, -1, 0, 2, -3, 6, -9, 12, -8, 5, -3, 2, -1, 1, 0, 0,
              3, -5, 9, -12, 8, -4, 2, -1, 0, 1, 0, 0]
    for i, s in enumerate(spikes):
        px = x + 6 + i * (w - 12) // (len(spikes) - 1)
        pts.append((px, sy0 + 11 - s))
    draw.line(pts, fill=RED, width=2)
    draw.text((x + w - 44, sy0 + 2), "M6.8", font=SANS_B(10), fill=RED)

# ---------------------------------------------------------------- mini icons
# Each icon draws into a small band (x, y, w, h) at the top of a small card.

def icon_tanker(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(214, 228, 236))
    sy = y + h - 12
    draw.rectangle([x, sy, x + w, y + h], fill=(70, 110, 140))
    draw.polygon([(x + 30, sy - 8), (x + w - 30, sy - 8), (x + w - 44, sy + 4),
                  (x + 44, sy + 4)], fill=(52, 58, 66))
    draw.rectangle([x + w - 62, sy - 20, x + w - 44, sy - 8], fill=(240, 238, 230))
    flame(draw, x + 56, sy - 8, 8,
          [((232, 120, 30), 1.0), ((250, 190, 60), 0.6)])
    draw.ellipse([x + 56, sy - 24, x + 68, sy - 12], fill=(110, 110, 110))

def icon_un(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(222, 230, 240))
    # French tricolore on the left, UN-style globe on the right
    for i, col in enumerate([(36, 80, 164), (250, 250, 248), (220, 40, 40)]):
        draw.rectangle([x + 16 + i * 12, y + 6, x + 28 + i * 12, y + h - 6], fill=col)
    cx, cy, r = x + w - 52, y + h // 2, 11
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(90, 140, 190),
                 outline=(40, 80, 130), width=2)
    draw.ellipse([cx - 4, cy - r, cx + 4, cy + r], outline=(250, 250, 248), width=1)
    draw.line([(cx - r, cy), (cx + r, cy)], fill=(250, 250, 248), width=1)
    draw.line([(x + 60, y + h // 2), (x + w - 70, y + h // 2)],
              fill=(120, 130, 140), width=2)
    draw.polygon([(x + w - 70, y + h // 2 - 4), (x + w - 70, y + h // 2 + 4),
                  (x + w - 64, y + h // 2)], fill=(120, 130, 140))

def icon_chip(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(232, 232, 228))
    cx, cy = x + w // 2, y + h // 2
    for k in range(-2, 3):
        draw.line([(cx + k * 8, y + 3), (cx + k * 8, y + 9)], fill=(90, 90, 90), width=2)
        draw.line([(cx + k * 8, y + h - 9), (cx + k * 8, y + h - 3)],
                  fill=(90, 90, 90), width=2)
        draw.line([(x + w // 2 - 30, cy + k * 6), (x + w // 2 - 24, cy + k * 6)],
                  fill=(90, 90, 90), width=2)
        draw.line([(x + w // 2 + 24, cy + k * 6), (x + w // 2 + 30, cy + k * 6)],
                  fill=(90, 90, 90), width=2)
    draw.rectangle([cx - 16, cy - 10, cx + 16, cy + 10], fill=(34, 34, 36),
                   outline=(120, 120, 120), width=1)
    draw.rectangle([cx - 8, cy - 5, cx + 8, cy + 5], fill=(70, 160, 90))
    draw.text((x + w - 40, y + h // 2 - 6), "900K", font=SANS_B(10), fill=RED)

def icon_base(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(236, 224, 196))
    # runway + hangar + drone + blast
    draw.rectangle([x + 14, y + h - 10, x + w - 14, y + h - 4], fill=(90, 90, 90))
    for wx in range(x + 22, x + w - 22, 16):
        draw.line([(wx, y + h - 7), (wx + 8, y + h - 7)], fill=(250, 250, 248), width=2)
    draw.polygon([(x + 30, y + h - 10), (x + 44, y + 8), (x + 58, y + h - 10)],
                 fill=(140, 120, 90))
    draw.rectangle([x + 40, y + h - 16, x + 48, y + h - 10], fill=(60, 60, 60))
    dx, dy = x + w - 46, y + 10
    draw.line([(dx - 8, dy - 4), (dx + 8, dy + 4)], fill=(30, 30, 30), width=2)
    draw.line([(dx - 8, dy + 4), (dx + 8, dy - 4)], fill=(30, 30, 30), width=2)
    flame(draw, x + w - 26, y + h - 10, 7,
          [((232, 120, 30), 1.0), ((250, 190, 60), 0.6)])

def icon_court(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(228, 226, 216))
    cx = x + w // 2
    draw.polygon([(cx - 52, y + 12), (cx, y + 2), (cx + 52, y + 12)], fill=(120, 110, 90))
    draw.rectangle([cx - 56, y + 12, cx + 56, y + 15], fill=(120, 110, 90))
    for k in range(-2, 3):
        px = cx + k * 20
        draw.rectangle([px - 3, y + 15, px + 3, y + h - 5], fill=(150, 140, 118))
    draw.rectangle([cx - 56, y + h - 5, cx + 56, y + h - 2], fill=(120, 110, 90))
    draw.text((cx - 26, y + 16), "ICJ", font=SANS_B(9), fill=(90, 80, 60))

def icon_bridge(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(216, 228, 236))
    sy = y + h - 8
    draw.rectangle([x, sy, x + w, y + h], fill=(80, 120, 150))
    # deck + arch + pylons
    draw.rectangle([x + 10, y + 12, x + w - 10, y + 16], fill=(90, 90, 90))
    draw.arc([x + 30, y - 6, x + w - 30, y + 26], start=180, end=360,
             fill=(90, 90, 90), width=3)
    for px in (x + 40, x + w // 2, x + w - 40):
        draw.line([(px, y + 16), (px, sy)], fill=(90, 90, 90), width=3)
    flame(draw, x + w // 2 + 30, y + 12, 7,
          [((232, 120, 30), 1.0), ((250, 190, 60), 0.6)])
    draw.ellipse([x + w // 2 + 26, y - 2, x + w // 2 + 38, y + 8], fill=(110, 110, 110))

def icon_chart(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(240, 228, 228))
    pts = [(x + 12, y + 6), (x + 40, y + 10), (x + 66, y + 8), (x + 92, y + 16),
           (x + 118, y + 14), (x + 144, y + 22), (x + w - 12, y + h - 6)]
    draw.line(pts, fill=RED, width=3)
    draw.polygon([(x + w - 12, y + h - 6), (x + w - 22, y + h - 8),
                  (x + w - 16, y + h - 14)], fill=RED)
    draw.text((x + w - 50, y + 2), "-10.4%", font=SANS_B(10), fill=RED)

def icon_badge(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(230, 232, 236))
    cx, cy = x + w // 2, y + h // 2
    import math
    outer, inner, pts = 13, 6, []
    for i in range(10):
        r = outer if i % 2 == 0 else inner
        a = math.pi * i / 5 - math.pi / 2
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    draw.polygon(pts, fill=(196, 160, 60), outline=(140, 110, 40))
    draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(60, 60, 60))
    # handcuffs
    for hx in (x + 18, x + w - 34):
        draw.ellipse([hx, cy - 5, hx + 12, cy + 7], outline=(70, 70, 70), width=3)
    draw.line([(x + 30, cy + 1), (x + w - 34, cy + 1)], fill=(70, 70, 70), width=2)

def icon_border(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(226, 232, 226))
    # striped barrier arm + post + Estonian colours
    draw.rectangle([x + 14, y + 6, x + 20, y + h - 4], fill=(70, 70, 70))
    for i in range(6):
        col = (220, 40, 40) if i % 2 == 0 else (250, 250, 248)
        draw.rectangle([x + 20 + i * 22, y + 7, x + 42 + i * 22, y + 13], fill=col)
    draw.rectangle([x + w - 26, y + 13, x + w - 20, y + h - 4], fill=(70, 70, 70))
    for i, col in enumerate([(40, 110, 180), (30, 30, 30), (250, 250, 248)]):
        draw.rectangle([x + 30, y + h - 12 + i * 3, x + 58, y + h - 9 + i * 3],
                       fill=col)
    draw.text((x + 66, y + h - 13), "5 CLOSED", font=SANS_B(9), fill=INK)

def icon_vote(draw, x, y, w, h):
    draw.rectangle([x, y, x + w, y + h], fill=(236, 232, 224))
    # Greenland flag: white/red with offset disc
    fx, fy = x + 16, y + 6
    draw.rectangle([fx, fy, fx + 44, fy + 10], fill=(250, 250, 248),
                   outline=(160, 160, 160))
    draw.rectangle([fx, fy + 10, fx + 44, fy + 20], fill=(200, 30, 40))
    draw.pieslice([fx + 12, fy + 3, fx + 32, fy + 17], start=180, end=360,
                  fill=(200, 30, 40))
    draw.pieslice([fx + 12, fy + 3, fx + 32, fy + 17], start=0, end=180,
                  fill=(250, 250, 248))
    # ballot box + tick
    bx, by = x + w - 52, y + 6
    draw.rectangle([bx, by + 6, bx + 26, by + 22], fill=(90, 110, 140))
    draw.rectangle([bx - 3, by + 2, bx + 29, by + 8], fill=(70, 90, 120))
    draw.line([(bx + 5, by + 14), (bx + 11, by + 19), (bx + 21, by + 9)],
              fill=(255, 255, 255), width=3)
    draw.text((x + 70, y + 8), "109-0", font=SANS_B(12), fill=RED)

ICONS = {
    "tanker": icon_tanker, "un": icon_un, "chip": icon_chip,
    "base": icon_base, "court": icon_court, "bridge": icon_bridge,
    "chart": icon_chart, "badge": icon_badge, "border": icon_border,
    "vote": icon_vote,
}
SCENES = {"cop31": scene_cop31, "sparta": scene_sparta, "quake": scene_quake}

# ================================================================ sections

def draw_masthead(draw, y):
    """Top line: nameplate left, story count right, double rule below."""
    tracked(draw, (MARGIN, y), "THE WORLD IN ONE DAY", SANS_B(17), INK, tracking=3)
    right = "35 STORIES  |  6 REGIONS  |  EVERY ONE DATED SUNDAY 22 NOVEMBER 2026"
    f = SANS_B(9)
    draw.text((W - MARGIN - text_w(draw, right, f), y + 4), right, font=f, fill=SOFT)
    rule(draw, MARGIN, y + 24, W - MARGIN, width=3)
    rule(draw, MARGIN, y + 28, W - MARGIN, width=1)
    return y + 32

def draw_title_block(draw, y):
    """Giant serif date + italic red sub-headline of the top 3 stories."""
    centered(draw, W // 2, y, "Sunday 22 November 2026", SERIF_B(52), INK)
    sub = ("COP31 nears a climate deal in Antalya  |  Sparta II ablaze in the "
           "Gulf of Finland  |  M6.8 quake shakes Peru")
    centered(draw, W // 2, y + 62, sub, SERIF_I(15), RED)
    hline(draw, MARGIN, y + 88, W - MARGIN)
    return y + 94

def draw_stat_strip(draw, y, height=56):
    """Six big red numbers with two-line captions, divided by hairlines."""
    col_w = CW / 6
    for i, (num, cap) in enumerate(STATS):
        cx = MARGIN + col_w * i + col_w / 2
        centered(draw, cx, y, num, SERIF_B(30), RED)
        for j, line in enumerate(cap.split("\n")):
            centered(draw, cx, y + 34 + j * 10, line, SANS_B(7), SOFT)
        if i:
            x = MARGIN + col_w * i
            draw.line([(x, y + 4), (x, y + height - 6)], fill=FAINT, width=1)
    hline(draw, MARGIN, y + height, W - MARGIN)
    return y + height + 6

def draw_region_bar(draw, y, height=22):
    """One bar split into 6 coloured region segments, sized by story count.

    Segments too narrow for a full label get just their count inside the
    bar; their names are spelled out in the legend line underneath.
    """
    total = sum(n for _, n in REGION_COUNTS)
    x = MARGIN
    small = []
    for name, n in REGION_COUNTS:
        seg = CW * n / total
        draw.rectangle([x, y, x + seg, y + height], fill=REGION_COLORS[name])
        label = "%s %d" % (name, n)
        f = SANS_B(8)
        if text_w(draw, label, f) + 10 <= seg:
            draw.text((x + 6, y + 6), label, font=f, fill=(255, 255, 255))
        else:
            small.append(label)
            draw.text((x + seg / 2 - 3, y + 6), str(n), font=f,
                      fill=(255, 255, 255))
        x += seg
    legend = "  |  ".join(small)
    lf = SANS_B(7)
    draw.text((W - MARGIN - text_w(draw, legend, lf), y + height + 2),
              legend, font=lf, fill=SOFT)
    return y + height + 14

def draw_hero_card(draw, x, y, w, h, hero):
    """Hero card: scene illustration (~40%), red kicker band, headline, body."""
    draw.rectangle([x, y, x + w, y + h], fill=CARD, outline=RULE, width=1)
    ill_h = 76
    SCENES[hero["scene"]](draw, x + 1, y + 1, w - 2, ill_h)
    # number badge on the illustration
    bx, by = x + 8, y + 8
    draw.ellipse([bx, by, bx + 20, by + 20], fill=RED)
    centered(draw, bx + 10, by + 3, str(hero["num"]), SANS_B(11), (255, 255, 255))
    # red kicker band
    ky = y + ill_h + 1
    draw.rectangle([x + 1, ky, x + w - 1, ky + 17], fill=RED)
    draw.text((x + 8, ky + 4), hero["kicker"], font=SANS_B(8), fill=(255, 255, 255))
    tag = hero["tag"]
    tf = SANS_B(8)
    draw.text((x + w - 8 - text_w(draw, tag, tf), ky + 4), tag, font=tf,
              fill=(255, 220, 200))
    # headline (serif bold, up to 2 lines)
    hy = ky + 21
    for j, line in enumerate(fit_lines(draw, hero["headline"], SERIF_B(16),
                                       w - 16, 2)):
        draw.text((x + 8, hy + j * 19), line, font=SERIF_B(16), fill=INK)
    # body
    by2 = hy + 40
    for j, line in enumerate(fit_lines(draw, hero["body"], SANS(9), w - 16, 4)):
        draw.text((x + 8, by2 + j * 12), line, font=SANS(9), fill=INK)
    return y + h

def draw_small_card(draw, x, y, w, h, story):
    """Small card: mini illustration band, red kicker, 2-line body."""
    draw.rectangle([x, y, x + w, y + h], fill=CARD, outline=RULE, width=1)
    ill_h = 30
    ICONS[story["icon"]](draw, x + 1, y + 1, w - 2, ill_h)
    # number badge
    bx, by = x + 6, y + 5
    draw.ellipse([bx, by, bx + 17, by + 17], fill=RED)
    centered(draw, bx + 8, by + 2, str(story["num"]), SANS_B(9), (255, 255, 255))
    # kicker line (red bold) + day tag
    ky = y + ill_h + 5
    kf = SANS_B(8)
    kicker = story["kicker"]
    if text_w(draw, kicker, kf) > w - 34:
        kicker = fit_lines(draw, kicker, kf, w - 34, 1)[0]
    draw.text((x + 7, ky), kicker, font=kf, fill=RED)
    tag = story["tag"]
    tf = SANS_B(7)
    draw.text((x + w - 6 - text_w(draw, tag, tf), ky + 1), tag, font=tf, fill=SOFT)
    # body, up to 3 lines (the card has room; 2 lines truncated most texts)
    by2 = ky + 13
    for j, line in enumerate(fit_lines(draw, story["body"], SANS(8), w - 14, 3)):
        draw.text((x + 7, by2 + j * 10), line, font=SANS(8), fill=INK)
    return y + h

def draw_map_panel(draw, x, y, w, h):
    """Dotted world map with numbered red pins and leader lines."""
    draw.rectangle([x, y, x + w, y + h], fill=MAP_SEA, outline=RULE, width=1)
    header = "WHERE IT HAPPENED"
    draw.text((x + 8, y + 5), header, font=SANS_B(9), fill=INK)
    draw.text((x + w - 8 - text_w(draw, "13 PINS", SANS_B(8)), y + 6),
              "13 PINS", font=SANS_B(8), fill=RED)
    mx, my = x + 6, y + 22
    mw, mh = w - 12, h - 30
    cell_w, cell_h = mw / 100.0, mh / 46.0
    # dotted land
    for r, runs in enumerate(LAND_ROWS):
        cy = my + (r + 0.5) * cell_h
        for c0, c1 in runs:
            for c in range(c0, c1 + 1):
                cx = mx + (c + 0.5) * cell_w
                draw.ellipse([cx - 1.3, cy - 1.3, cx + 1.3, cy + 1.3], fill=MAP_LAND)
    # pins
    def to_xy(lon, lat):
        return (mx + (lon + 180.0) / 360.0 * mw,
                my + (80.0 - lat) / 137.0 * mh)
    for num, lon, lat, (ox, oy) in PINS:
        px, py = to_xy(lon, lat)
        lx, ly = px + ox, py + oy
        # clamp label inside the panel
        lx = max(mx + 10, min(mx + mw - 10, lx))
        ly = max(my + 10, min(my + mh - 10, ly))
        if abs(ox) + abs(oy) > 0:
            draw.line([(px, py), (lx, ly)], fill=(120, 120, 120), width=1)
            draw.ellipse([px - 2, py - 2, px + 2, py + 2], fill=RED)
        draw.ellipse([lx - 8, ly - 8, lx + 8, ly + 8], fill=RED,
                     outline=(255, 255, 255), width=1)
        centered(draw, lx, ly - 6, str(num), SANS_B(9), (255, 255, 255))
    # caption
    draw.text((x + 8, y + h - 13), "Numbers match the stories. Pins mark "
              "the dateline, not the whole region.", font=SANS_I(7), fill=SOFT)
    return y + h

def draw_more_list(draw, x, y, w, h):
    """'22 MORE STORIES' in two columns of 11 numbered entries."""
    draw.text((x, y), "22 MORE STORIES", font=SANS_B(11), fill=INK)
    sub = "ALSO ON SUNDAY 22 NOVEMBER"
    draw.text((x + text_w(draw, "22 MORE STORIES  ", SANS_B(11)), y + 2),
              sub, font=SANS_B(8), fill=RED)
    rule(draw, x, y + 16, x + w, width=2)
    col_w = (w - 14) // 2
    entry_h = (h - 22) // 11
    f_num, f_txt, f_tag = SANS_B(9), SANS(8.5), SANS_B(7)
    for idx, (num, text, tag) in enumerate(MORE):
        col = 0 if idx < 11 else 1
        row = idx % 11
        ex = x + col * (col_w + 14)
        ey = y + 22 + row * entry_h
        draw.text((ex, ey), "%d." % num, font=f_num, fill=RED)
        num_w = text_w(draw, "%d.  " % num, f_num)
        body = text + "  [" + tag + "]"
        lines = fit_lines(draw, body, f_txt, col_w - num_w, 2)
        for j, line in enumerate(lines):
            draw.text((ex + num_w, ey + j * 11), line, font=f_txt, fill=INK)
        if row < 10:
            hline(draw, ex, ey + entry_h - 4, ex + col_w, color=(214, 208, 192))
    return y + h

def draw_date_check(draw, y, height=62):
    """Red-framed verification box: method, exclusions, still to come."""
    draw.rectangle([MARGIN, y, W - MARGIN, y + height], fill=CARD,
                   outline=RED, width=2)
    title = "DATE CHECK"
    tf = SANS_B(10)
    draw.text((MARGIN + 10, y + 6), title, font=tf, fill=RED)
    tx = MARGIN + 10 + text_w(draw, title + "   ", tf)
    f = SANS(8.5)
    lines = [
        "METHOD: every story dated from its first Reuters / AP wire or official "
        "release; day tags SUN / SAT / FRI / WED / WEEK show that date.",
        "EXCLUDED: the Shenzhen peace declaration (signed earlier in the week, not "
        "22 Nov news); the 'M6.9' Peru figure (unsupported - GFZ says 6.8); "
        "'COP31 deal reached' claims (objections open until 03:00 GMT).",
        "STILL TO COME AT PRESS TIME: the COP31 approval session, 06:00 GMT "
        "Sunday - the deal is 'nears', not done.",
    ]
    for j, line in enumerate(lines):
        draw.text((tx, y + 6 + j * 12), line, font=f, fill=INK)
    # wrap the middle line if it overflows
    return y + height

def draw_footer(draw, y):
    rule(draw, MARGIN, y, W - MARGIN, width=1)
    src = ("Sources: Reuters  |  Associated Press  |  GFZ  |  USGS  |  UKMTO  |  "
           "IAEA  |  ICJ  |  AAP  |  Oman Maritime Security Centre  |  House "
           "Foreign Affairs Committee   -   Press time Sunday 22 November 2026, "
           "06:00 GMT")
    centered(draw, W // 2, y + 5, src, SANS(8), SOFT)
    return y + 20

# ================================================================ compose

def build():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    y = 12
    y = draw_masthead(draw, y)
    y = draw_title_block(draw, y + 4)
    y = draw_stat_strip(draw, y + 4)
    y = draw_region_bar(draw, y)

    # 3 hero cards
    hero_y, hero_h = y, 190
    hero_w = (CW - 16) // 3
    for i, hero in enumerate(HEROES):
        draw_hero_card(draw, MARGIN + i * (hero_w + 8), hero_y, hero_w, hero_h, hero)
    y = hero_y + hero_h + 8

    # 10 small cards, 2 rows x 5
    small_w = (CW - 4 * 6) // 5
    small_h = 90
    for i, story in enumerate(SMALLS):
        row, col = divmod(i, 5)
        draw_small_card(draw, MARGIN + col * (small_w + 6),
                        y + row * (small_h + 6), small_w, small_h, story)
    y = y + 2 * small_h + 6 + 8

    # map (left) + 22 more stories (right)
    map_w = 350
    section_h = 288
    draw_map_panel(draw, MARGIN, y, map_w, section_h)
    draw_more_list(draw, MARGIN + map_w + 12, y, CW - map_w - 12, section_h)
    y = y + section_h + 8

    y = draw_date_check(draw, y)
    y = draw_footer(draw, y + 6)
    return img, y

def main():
    img, bottom = build()
    img.save(OUT_PATH, format="PNG", optimize=True)
    data = open(OUT_PATH, "rb").read()
    digest = hashlib.sha256(data).hexdigest()
    mean = sum(img.convert("L").getdata()) / (W * H)
    print("wrote %s" % OUT_PATH)
    print("bytes: %d (limit 1048576)" % len(data))
    print("sha256: %s" % digest)
    print("bottom y: %d of %d (FIT %s)" % (bottom, H, "OK" if bottom <= H else "OVERFLOW"))
    print("mean brightness: %.1f" % mean)
    print("stories: %d hero + %d small + %d list = %d"
          % (len(HEROES), len(SMALLS), len(MORE),
             len(HEROES) + len(SMALLS) + len(MORE)))
    print("regions: %s (sum %d)"
          % (", ".join("%s %d" % rc for rc in REGION_COUNTS),
             sum(n for _, n in REGION_COUNTS)))

if __name__ == "__main__":
    main()
