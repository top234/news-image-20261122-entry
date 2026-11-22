#!/usr/bin/env python3
"""The World in One Day — v4 broadsheet for Sunday 22 November 2026.

One 1024x1024 newspaper front page summing up the day in 35 verified
stories: 3 hero cards with code-drawn scene illustrations, 10 small cards
with mini illustrations, a UTC timeline of the day, a dotted world map
with region-coloured pins, a two-column list of 22 more stories, a DATE
CHECK box and a source footer.

Every story carries its source and a status tag (CONFIRMED / OFFICIAL /
REPORTED / FORECAST). Day tags are honest: SUN = Sunday 22 Nov, SAT =
Saturday 21 Nov (still developing), FRI = Friday 20 Nov.

Deterministic: fixed fonts, fixed palette, no randomness, no clock, no
network. PIL only. Run: python3 generate.py  ->  writes entry.png here.
"""

import hashlib
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")

# ------------------------------------------------------------------ page
PAGE_W, PAGE_H = 1024, 1024
EDGE = 24                      # outer margin
INNER = PAGE_W - 2 * EDGE      # 976 usable width

# ---------------------------------------------------------------- palette
PAPER = (248, 244, 233)        # newsprint
CARD_BG = (255, 253, 246)
INK = (26, 25, 23)
GREY = (96, 94, 86)
PALE = (160, 156, 144)
RED = (178, 30, 30)
RED_DARK = (140, 20, 20)
RULE_C = (35, 35, 38)
SEA = (229, 236, 238)
LAND = (70, 90, 108)
SKY = (214, 230, 240)
NIGHT = (24, 34, 58)

REGION_HUES = {
    "EUROPE": (37, 99, 165),
    "MIDDLE EAST": (207, 112, 25),
    "ASIA-PACIFIC": (122, 80, 160),
    "AMERICAS": (43, 138, 62),
    "AFRICA": (176, 148, 28),
    "OCEANIA": (20, 150, 160),
    "GLOBAL": (115, 115, 115),
}

STATUS_HUES = {
    "CONFIRMED": (27, 120, 60),
    "OFFICIAL": (100, 60, 140),
    "REPORTED": (178, 108, 8),
    "FORECAST": (37, 99, 165),
    "CLAIM": (178, 30, 30),
}

# ------------------------------------------------------------------- fonts
FONT_DIR = "/usr/share/fonts/truetype/liberation"
_FONT_FILES = {
    "serif_b": "LiberationSerif-Bold.ttf",
    "serif": "LiberationSerif-Regular.ttf",
    "serif_i": "LiberationSerif-Italic.ttf",
    "sans_b": "LiberationSans-Bold.ttf",
    "sans": "LiberationSans-Regular.ttf",
    "sans_i": "LiberationSans-Italic.ttf",
}
_FONT_CACHE = {}


def font(kind, size):
    key = (kind, size)
    if key not in _FONT_CACHE:
        _FONT_CACHE[key] = ImageFont.truetype(
            os.path.join(FONT_DIR, _FONT_FILES[kind]), size
        )
    return _FONT_CACHE[key]


# ----------------------------------------------------------------- helpers
def tw(d, s, f):
    return d.textlength(s, font=f)


def wrap(d, s, f, max_w):
    """Greedy word wrap; returns lines that each fit max_w."""
    lines, cur = [], ""
    for word in s.split():
        trial = word if not cur else cur + " " + word
        if tw(d, trial, f) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(d, s, f, max_w, max_lines):
    """Wrap to at most max_lines, trimming the last with an ellipsis."""
    lines = wrap(d, s, f, max_w)
    if len(lines) <= max_lines:
        return lines
    lines = lines[:max_lines]
    while lines and tw(d, lines[-1] + "…", f) > max_w and len(lines[-1]) > 1:
        lines[-1] = lines[-1][:-1]
    lines[-1] = lines[-1] + "…"
    return lines


def centre(d, cx, y, s, f, fill):
    d.text((cx - tw(d, s, f) / 2, y), s, font=f, fill=fill)


def spaced(d, x, y, s, f, fill, gap=2):
    """Draw letter-spaced caps; returns the x just past the last letter."""
    cx = x
    for ch in s:
        d.text((cx, y), ch, font=f, fill=fill)
        cx += tw(d, ch, f) + gap
    return cx


def spaced_w(d, s, f, gap=2):
    return sum(tw(d, ch, f) + gap for ch in s) - (gap if s else 0)


def rule(d, x0, y, x1, width=2, color=RULE_C):
    d.line([(x0, y), (x1, y)], fill=color, width=width)


def status_chip(d, x_right, y, tag):
    """Small outlined status tag, right-aligned at x_right; returns left x."""
    f = font("sans_b", 7)
    hue = STATUS_HUES[tag]
    w = tw(d, tag, f) + 8
    x0 = x_right - w
    d.rectangle([x0, y, x_right, y + 10], outline=hue, width=1, fill=(255, 255, 255))
    d.text((x0 + 4, y + 1), tag, font=f, fill=hue)
    return x0

# -------------------------------------------------------------------- data
# All facts verified by the coordinator from Reuters / AP / AFP / GFZ /
# official releases. Do not add stories, do not change figures.

HEROES = [
    {
        "num": 1, "scene": "cop31", "kicker": "CLIMATE SUMMIT",
        "headline": "COP31 NEARS DEAL",
        "place": "ANTALYA, TURKEY", "topic": "CLIMATE",
        "status": "CONFIRMED", "day": "SUN",
        "stat": "~200 nations", "stat_sub": "power 21% → 35% by 2035",
        "body": "A new package was unveiled overnight. President Kurum: "
                "\u201cwe believe that we have put forward a text which all "
                "the parties can agree upon\u201d. Objections close 03:00 "
                "GMT; approval plenary 06:00 GMT. (Reuters)",
    },
    {
        "num": 2, "scene": "bahrain", "kicker": "GULF WAR",
        "headline": "IRAN STRIKES US BASES IN BAHRAIN",
        "place": "BAHRAIN", "topic": "GULF WAR",
        "status": "REPORTED", "day": "SAT",
        "stat": "2 bases", "stat_sub": "al-Riffa & Awali",
        "body": "The IRGC says a missile-and-drone operation hit US "
                "positions at al-Riffa and Awali, claiming two Patriot "
                "radars destroyed. Bahrain: a civilian site hit, fire, no "
                "casualties. Reply to US MQ-1/MQ-9 drones in Iranian "
                "airspace. (Reuters / IANS)",
    },
    {
        "num": 3, "scene": "sparta", "kicker": "BALTIC SEA",
        "headline": "SPARTA II ABLAZE, STILL BURNING",
        "place": "GULF OF FINLAND", "topic": "SHIPPING",
        "status": "CONFIRMED", "day": "SAT",
        "stat": "16 crew saved", "stat_sub": "Helsinki: Ukraine possibly behind it",
        "body": "The 121 m Russian cargo ship was hit by two drones in the "
                "Gulf of Finland; the fire still burned on Saturday night. "
                "All 16 crew took to lifeboats and were picked up by a "
                "Russian vessel. Finland set temporary air and sea limits. "
                "(Reuters / Yle)",
    },
]

SMALLS = [
    {"num": 4, "icon": "tanker", "kicker": "MIDDLE EAST",
     "headline": "TANKERS HIT OFF OMAN", "status": "CONFIRMED", "day": "SUN",
     "body": "Two tankers hit by unknown projectiles off Khasab — engine "
             "room and stern. No casualties. (UKMTO / Reuters)"},
    {"num": 5, "icon": "power", "kicker": "ENERGY",
     "headline": "IRAN BEGINS POWER RATIONING", "status": "CONFIRMED", "day": "SUN",
     "body": "Power distribution limits begin Sunday; outages of up to 2 "
             "hours a day by region. (RFE/RL / Straits Times)"},
    {"num": 6, "icon": "ballot", "kicker": "ASIA",
     "headline": "HONG KONG VOTES", "status": "CONFIRMED", "day": "SUN",
     "body": "856 candidates contest 723 seats; polls 09:00–18:00 HKT. "
             "Turnout 44.74% at 10:00. (China Daily Asia)"},
    {"num": 7, "icon": "plane", "kicker": "DIPLOMACY",
     "headline": "NEPAL PM FLIES TO DELHI", "status": "OFFICIAL", "day": "SUN",
     "body": "Balendra Shah arrives Sunday for a 2-day state visit, his "
             "first since taking office on 27 March. (MEA / IANS)"},
    {"num": 8, "icon": "nato", "kicker": "NATO",
     "headline": "RUTTE IN WARSAW", "status": "CONFIRMED", "day": "SAT",
     "body": "\u201cNATO will defend every inch of Polish territory,\u201d "
             "the secretary general said on Saturday. (PAP / AP)"},
    {"num": 9, "icon": "van", "kicker": "GAZA",
     "headline": "GAZA FOOD-AID VAN HIT", "status": "REPORTED", "day": "SAT",
     "body": "An Israeli strike in Tel al-Hawa killed 3 in a van carrying "
             "food and WCK-logo paper. WCK: not ours. (Reuters)"},
    {"num": 10, "icon": "f1", "kicker": "FORMULA 1",
     "headline": "LAS VEGAS GP", "status": "FORECAST", "day": "SUN",
     "body": "Lights out 04:00 UTC. Verstappen on pole (1:34.151); "
             "Antonelli fastest, penalised 5 places. (F1)"},
    {"num": 11, "icon": "football", "kicker": "FOOTBALL",
     "headline": "LIVERPOOL HOST MAN UTD", "status": "FORECAST", "day": "SUN",
     "body": "Kick-off 16:30 GMT at Anfield. Pochettino\u2019s first game "
             "as United coach; United 18th after 10. (Premier League)"},
    {"num": 12, "icon": "tennis", "kicker": "TENNIS",
     "headline": "ATP FINALS: ZVEREV v ALCARAZ", "status": "FORECAST", "day": "SUN",
     "body": "Final 18:00 CET in Turin. Zverev beat Medvedev 7-6(7-0) 6-4; "
             "Alcaraz beat Shelton in three. (ATP)"},
    {"num": 13, "icon": "cricket", "kicker": "CRICKET",
     "headline": "INDIA FACE NZ IN WELLINGTON", "status": "CONFIRMED", "day": "SUN",
     "body": "First Test, day three in windy Wellington as India face "
             "New Zealand. (Set v2)"},
]

# (number, text with source, day tag) — list items 14–35
MORE = [
    (14, "Skylight tanker hit near Khasab; 20 crew evacuated, 4 hurt — 4th strike in 24 hours. (Oman Maritime Security Centre)", "SUN"),
    (15, "France to seek a UN Security Council meeting on Myanmar rejecting the ICJ ruling. (Reuters)", "SAT"),
    (16, "US approves ~900,000 Nvidia/AMD chips for China over 6 months: Tencent 150k, Alibaba 75k, Baidu 43k, BYD 4k. (Reuters)", "FRI"),
    (17, "Nasdaq\u2019s worst week since 2020, \u221210.4%; S&P 500 enters correction; Dow \u22121,101 to 49,097. (AP)", "FRI"),
    (18, "FBI investigates suspected hack of its criminal database. (Set v2)", "FRI"),
    (19, "Trump threatens a \u201cbig tax\u201d on US firms building AI data centres abroad. (Set v2)", "FRI"),
    (20, "Denmark accuses Russia of plotting to kill a US-Ukrainian rapper near Copenhagen. (Set v2)", "FRI"),
    (21, "Estonia to close 5 land crossings with Russia from 1 Dec for 6 months after GRU-linked arson attempts. (Reuters)", "FRI"),
    (22, "Mexican army captures cartel boss Fausto Isidro Meza Flores, \u201cEl Chapo Isidro\u201d. (Set v2)", "SAT"),
    (23, "Zscaler jumps 18% on reports CrowdStrike is in talks to buy it. (Set v2)", "SAT"),
    (24, "Record T20 chase at the MCG: Australia chase 188, beat England by 3 wickets; Chaudhary 66 off 38. (AAP)", "SAT"),
    (25, "Zelensky proposes a local ceasefire to evacuate civilians from 15 settlements along the Dnipro. (ISW)", "SAT"),
    (26, "Modi opens Nitish Setu, the bridge linking Patna and Vaishali. (PTI)", "SUN"),
    (27, "Cummins keeps the Australian Test captaincy with unanimous support. (Set v2)", "SUN"),
    (28, "Chess: Erigaisi and Praggnanandhaa win; Vaishali loses on the first classification day. (Set v2)", "SUN"),
    (29, "South Africa local elections: ANC fights to hold cities. (Set v2)", "SUN"),
    (30, "Air India / AI Express extend Jeddah flight suspensions to 24 Nov. (Set v2)", "SUN"),
    (31, "Trafalgar Square Christmas tree leaves Oslo for London. (Set v2)", "SAT"),
    (32, "Man found guilty of starting the Palisades fire, one of California\u2019s deadliest. (Set v2)", "FRI"),
    (33, "Anthropic\u2019s $81.3bn IPO, the largest ever; shares +39% on debut, then fell the next day. (Reuters)", "FRI"),
    (34, "Sensex ends a two-day rally on profit-taking and US Fed rate worries. (Set v2)", "SUN"),
    (35, "80 drones shot down over Leningrad region overnight. (Gov. Drozdenko)", "SAT"),
]

STATS = [
    ("200", "DELEGATIONS AT COP31", "Reuters"),
    ("2", "US BASES HIT IN BAHRAIN", "Reuters / IANS"),
    ("16", "CREW SAVED FROM SPARTA II", "Reuters / Yle"),
    ("723", "SEATS IN HONG KONG VOTE", "China Daily Asia"),
    ("5,709", "VOTERS, HONG KONG POLLS", "info.gov.hk"),
    ("50", "LAPS, LAS VEGAS GP", "F1"),
]

# Region counts across the 35 stories; GLOBAL = the UN Security Council item.
REGIONS = [
    ("EUROPE", 10), ("AMERICAS", 9), ("ASIA-PACIFIC", 6),
    ("MIDDLE EAST", 5), ("OCEANIA", 3), ("AFRICA", 1), ("GLOBAL", 1),
]

TIMELINE = [
    ("01:00", "HK polls open"),
    ("03:00", "COP31 objections close"),
    ("04:00", "Las Vegas GP lights out"),
    ("06:00", "COP31 approval plenary"),
    ("08:00", "Nepal PM departs Kathmandu"),
    ("10:00", "HK polls close"),
    ("16:30", "Liverpool v Man Utd kick-off"),
    ("17:00", "ATP Finals final"),
]

# Map pins: (story number, lon, lat, region, label offset dx, dy)
PINS = [
    (1, 30.7, 36.9, "EUROPE", -20, -16),
    (2, 50.6, 26.2, "MIDDLE EAST", -24, 4),
    (3, 25.0, 59.8, "EUROPE", 16, -14),
    (4, 56.2, 26.2, "MIDDLE EAST", 18, 12),
    (5, 51.4, 35.7, "MIDDLE EAST", 18, -12),
    (6, 114.2, 22.3, "ASIA-PACIFIC", 12, 10),
    (7, 77.2, 28.6, "ASIA-PACIFIC", 10, -14),
    (8, 21.0, 52.2, "EUROPE", -22, 8),
    (9, 34.5, 31.5, "MIDDLE EAST", 16, 10),
    (10, -115.1, 36.2, "AMERICAS", -14, -14),
    (11, -3.0, 53.4, "EUROPE", -18, -14),
    (12, 7.7, 45.1, "EUROPE", -16, 10),
    (13, 174.8, -41.3, "OCEANIA", -12, 10),
    (14, 145.0, -37.8, "OCEANIA", -22, -12),
    (29, 28.0, -26.2, "AFRICA", 12, 8),
]

# Land as latitude bands: (lat_lo, lat_hi, lon_lo, lon_hi). A coarse but
# recognisable world, built from geography rather than copied from a bitmap.
LAND_BANDS = [
    # North America
    (60, 72, -168, -58), (50, 60, -140, -55), (40, 50, -125, -66),
    (30, 40, -120, -75), (25, 31, -112, -80), (15, 25, -106, -87),
    (8, 15, -93, -79), (25, 30, -82, -80),
    # Greenland
    (76, 84, -60, -18), (70, 76, -55, -20), (60, 70, -53, -40),
    # South America
    (5, 11, -77, -60), (0, 5, -79, -50), (-10, 0, -80, -35),
    (-20, -10, -70, -35), (-30, -20, -70, -48), (-40, -30, -73, -57),
    (-52, -40, -73, -65),
    # Africa
    (27, 32, -10, 33), (20, 27, -17, 32), (10, 20, -17, 43),
    (5, 10, -13, 51), (0, 5, -8, 42), (-10, 0, 8, 41),
    (-20, -10, 12, 36), (-30, -20, 15, 33), (-35, -30, 18, 29),
    (-26, -12, 44, 50),
    # Eurasia
    (68, 75, 15, 180), (60, 68, 5, 180), (55, 60, -5, 170),
    (50, 55, -5, 140), (45, 50, -5, 135), (40, 45, -10, 130),
    (36, 40, -10, 130), (30, 36, 35, 122), (25, 30, 35, 122),
    (20, 25, 39, 59), (20, 25, 68, 89), (20, 25, 98, 110),
    (15, 20, 42, 59), (15, 20, 74, 80), (15, 20, 98, 109),
    (10, 15, 43, 55), (10, 15, 76, 80), (10, 15, 98, 106),
    (5, 10, 98, 104),
    # UK, Japan, Indonesia
    (50, 59, -6, 2),
    (43, 46, 140, 146), (38, 43, 139, 142), (34, 38, 133, 141),
    (31, 34, 130, 134),
    (-6, 6, 95, 106), (-4, 4, 109, 119), (-8, -6, 105, 114),
    (-9, -1, 131, 141), (-6, 1, 119, 123),
    # Australia, New Zealand
    (-15, -11, 130, 150), (-25, -15, 113, 150), (-35, -25, 113, 150),
    (-39, -35, 140, 150), (-43, -41, 145, 148),
    (-38, -35, 173, 178), (-42, -38, 174, 178), (-47, -42, 167, 174),
]

# Seas carved out of the bands above.
SEA_HOLES = [
    (52, 63, -93, -77),    # Hudson Bay
    (32, 36, -6, 36),      # Mediterranean
    (15, 27, 35, 38),      # Red Sea
    (37, 47, 47, 54),      # Caspian Sea
    (41, 47, 28, 41),      # Black Sea
    (26, 30, 48, 56),      # Persian Gulf
]


def is_land(lon, lat):
    for lo, hi, w, e in SEA_HOLES:
        if lo <= lat < hi and w <= lon < e:
            return False
    for lo, hi, w, e in LAND_BANDS:
        if lo <= lat < hi and w <= lon < e:
            return True
    return False

def _clip_paint(img, x, y, w, h, fn):
    """Paint fn into a temp image and paste it: anything the painter draws
    outside its box is cut off instead of bleeding into neighbouring
    sections."""
    tmp = Image.new("RGB", (w, h), PAPER)
    td = ImageDraw.Draw(tmp)
    fn(td, 0, 0, w, h)
    img.paste(tmp, (x, y))


# ------------------------------------------------------- hero illustrations
def _sky_bands(d, x, y, w, h, top, bottom, steps=7):
    for i in range(steps):
        t = i / (steps - 1)
        col = tuple(int(top[k] + (bottom[k] - top[k]) * t) for k in range(3))
        y0 = y + int(h * i / steps)
        y1 = y + int(h * (i + 1) / steps)
        d.rectangle([x, y0, x + w, y1], fill=col)


def _flame(d, cx, base, size):
    """Layered teardrop flame: red outer, orange mid, yellow core."""
    for scale, col in ((1.0, (200, 40, 20)), (0.68, (240, 120, 20)),
                       (0.38, (250, 210, 60))):
        s = size * scale
        d.polygon([(cx - s * 0.55, base), (cx - s * 0.28, base - s * 0.9),
                   (cx, base - s * 1.5), (cx + s * 0.28, base - s * 0.9),
                   (cx + s * 0.55, base)], fill=col)


def _smoke(d, cx, y, puffs=((0, 0, 9), (10, -6, 12), (-9, -8, 10), (3, -14, 8))):
    for dx, dy, r in puffs:
        d.ellipse([cx + dx - r, y + dy - r, cx + dx + r, y + dy + r],
                  fill=(120, 118, 112))


def paint_cop31(d, x, y, w, h):
    """Dawn over the summit table: rising sun, flags, delegates, COP31 banner."""
    _sky_bands(d, x, y, w, h, (252, 226, 170), (214, 232, 240))
    sun_cx, sun_cy, sun_r = x + int(w * 0.72), y + int(h * 0.42), 16
    d.ellipse([sun_cx - sun_r - 8, sun_cy - sun_r - 8,
               sun_cx + sun_r + 8, sun_cy + sun_r + 8], fill=(250, 214, 130))
    d.ellipse([sun_cx - sun_r, sun_cy - sun_r,
               sun_cx + sun_r, sun_cy + sun_r], fill=(245, 180, 60))
    # distant hills + sea
    d.polygon([(x, y + h * 0.62), (x + w * 0.3, y + h * 0.48),
               (x + w * 0.55, y + h * 0.62), (x + w, y + h * 0.52),
               (x + w, y + h * 0.62)], fill=(150, 178, 150))
    d.rectangle([x, y + int(h * 0.62), x + w, y + h], fill=(168, 196, 208))
    # long negotiation table
    ty = y + int(h * 0.66)
    d.rectangle([x + 14, ty, x + w - 14, ty + 12], fill=(122, 84, 52))
    d.rectangle([x + 14, ty + 12, x + w - 14, ty + 15], fill=(96, 64, 38))
    # delegates behind the table
    for i in range(7):
        px = x + 26 + i * int((w - 52) / 6)
        d.ellipse([px - 6, ty - 22, px + 6, ty - 10], fill=(52, 48, 44))
        d.pieslice([px - 11, ty - 12, px + 11, ty + 8], 180, 360,
                   fill=(64, 60, 56))
    # flag poles on the table
    flag_cols = [(178, 30, 30), (37, 99, 165), (43, 138, 62), (207, 112, 25),
                 (122, 80, 160), (20, 150, 160)]
    for i, fc in enumerate(flag_cols):
        fx = x + 34 + i * int((w - 68) / 5)
        d.line([(fx, ty - 34), (fx, ty)], fill=(60, 60, 60), width=1)
        d.rectangle([fx, ty - 34, fx + 11, ty - 27], fill=fc)
    # banner on the table front — shifted right so the stat chip (which
    # sits bottom-left over the illustration) never covers it
    d.rectangle([x + int(w * 0.48), ty + 2, x + int(w * 0.84), ty + 11],
                fill=(255, 253, 246))
    centre(d, x + int(w * 0.66), ty + 1, "COP31", font("sans_b", 8), RED_DARK)


def paint_bahrain(d, x, y, w, h):
    """Night strike: two bases, Patriot radar, missile trails, blasts."""
    d.rectangle([x, y, x + w, y + h], fill=NIGHT)
    for sx, sy in ((18, 12), (52, 22), (96, 9), (150, 18), (205, 10),
                   (250, 24), (288, 12), (120, 28), (228, 30), (70, 32)):
        d.ellipse([x + sx, y + sy, x + sx + 2, y + sy + 2], fill=(220, 225, 240))
    moon_cx, moon_cy = x + int(w * 0.85), y + 14
    d.ellipse([moon_cx - 9, moon_cy - 9, moon_cx + 9, moon_cy + 9],
              fill=(235, 232, 210))
    d.ellipse([moon_cx - 5, moon_cy - 9, moon_cx + 11, moon_cy + 9], fill=NIGHT)
    gy = y + int(h * 0.78)
    d.rectangle([x, gy, x + w, y + h], fill=(38, 44, 58))
    # base buildings + radar dishes
    d.rectangle([x + 16, gy - 26, x + 80, gy], fill=(58, 64, 82))
    d.rectangle([x + 200, gy - 22, x + 268, gy], fill=(58, 64, 82))
    for rx in (x + 48, x + 234):
        d.line([(rx, gy - 26), (rx, gy - 44)], fill=(150, 155, 170), width=2)
        d.pieslice([rx - 12, gy - 56, rx + 12, gy - 32], 180, 360,
                   fill=(170, 175, 190))
        d.line([(rx, gy - 44), (rx + 14, gy - 52)], fill=(150, 155, 170),
               width=1)
    # lit windows
    for wx in (24, 38, 52, 66, 208, 222, 236, 250):
        d.rectangle([x + wx, gy - 16, x + wx + 7, gy - 9], fill=(250, 210, 110))
    # missile trails arcing in
    for x0, y0, x1, y1 in ((x + 40, y + 8, x + 52, gy - 30),
                           (x + 150, y + 4, x + 238, gy - 26),
                           (x + 280, y + 10, x + 262, gy - 24)):
        d.line([(x0, y0), (x1, y1)], fill=(255, 190, 90), width=2)
        d.ellipse([x1 - 3, y1 - 3, x1 + 3, y1 + 3], fill=(255, 230, 150))
    # explosion bursts
    for ex, ey, r in ((x + 52, gy - 30, 13), (x + 238, gy - 26, 11),
                      (x + 262, gy - 24, 8)):
        for rr, col in ((r, (240, 120, 20)), (r * 0.6, (250, 200, 60)),
                        (r * 0.3, (255, 245, 200))):
            d.ellipse([ex - rr, ey - rr, ex + rr, ey + rr], fill=col)
    _smoke(d, x + 52, gy - 40)
    _smoke(d, x + 238, gy - 36)
    # small drone silhouettes
    for dx_, dy_ in ((120, 26), (180, 16)):
        d.ellipse([x + dx_ - 6, y + dy_ - 2, x + dx_ + 6, y + dy_ + 2],
                  fill=(10, 12, 20))
        d.line([(x + dx_ - 9, y + dy_ - 3), (x + dx_ + 9, y + dy_ - 3)],
               fill=(10, 12, 20), width=1)


def paint_sparta(d, x, y, w, h):
    """Cargo ship ablaze at sea: hull, containers, flames, lifeboat, drones."""
    _sky_bands(d, x, y, w, h, (240, 200, 150), (200, 205, 210))
    wy = y + int(h * 0.66)
    d.rectangle([x, wy, x + w, y + h], fill=(74, 110, 138))
    for i in range(9):  # wave lines
        wx = x + 8 + i * int((w - 16) / 8)
        d.arc([wx, wy + 8, wx + 26, wy + 18], 200, 340, fill=(190, 215, 225),
              width=1)
    # hull
    d.polygon([(x + 22, wy - 8), (x + w - 22, wy - 8), (x + w - 40, wy + 14),
               (x + 40, wy + 14)], fill=(40, 44, 50))
    d.rectangle([x + 22, wy - 12, x + w - 22, wy - 8], fill=(60, 64, 70))
    # containers
    cont_cols = [(178, 60, 40), (37, 99, 165), (43, 138, 62), (207, 140, 25),
                 (122, 80, 160)]
    for i, cc in enumerate(cont_cols):
        cx0 = x + 34 + i * 50
        d.rectangle([cx0, wy - 34, cx0 + 44, wy - 12], fill=cc)
        d.rectangle([cx0, wy - 34, cx0 + 44, wy - 12], outline=(30, 30, 30))
    # bridge tower
    d.rectangle([x + w - 66, wy - 52, x + w - 30, wy - 12], fill=(210, 208, 200))
    d.rectangle([x + w - 62, wy - 48, x + w - 34, wy - 40], fill=(90, 130, 160))
    # flames over the mid containers — sized to stay inside the frame
    for fx, fs in ((x + 84, 12), (x + 132, 15), (x + 186, 12), (x + 108, 10)):
        _flame(d, fx, wy - 32, fs)
    _smoke(d, x + 132, wy - 40, ((0, 0, 7), (8, -4, 9), (-7, -6, 8), (2, -11, 6)))
    _smoke(d, x + 190, wy - 36, ((0, 0, 7), (8, -4, 9), (-7, -6, 8), (2, -11, 6)))
    # two drones above
    for dx_, dy_ in ((70, 18), (250, 24)):
        d.ellipse([x + dx_ - 7, y + dy_ - 2, x + dx_ + 7, y + dy_ + 2],
                  fill=(25, 25, 28))
        d.line([(x + dx_ - 11, y + dy_ - 4), (x + dx_ + 11, y + dy_ - 4)],
               fill=(25, 25, 28), width=1)
    # orange lifeboat with crew, lower right
    bx, by = x + w - 88, wy + 8
    d.polygon([(bx, by), (bx + 44, by), (bx + 38, by + 10), (bx + 6, by + 10)],
              fill=(235, 110, 20))
    for px in (bx + 10, bx + 22, bx + 34):
        d.ellipse([px - 3, by - 8, px + 3, by - 2], fill=(40, 36, 32))


SCENES = {"cop31": paint_cop31, "bahrain": paint_bahrain, "sparta": paint_sparta}


# ---------------------------------------------------------- mini illustrations
def _mini_base(d, x, y, w, h, tint):
    d.rectangle([x, y, x + w, y + h], fill=tint)


def mini_tanker(d, x, y, w, h):
    _mini_base(d, x, y, w, h, (222, 232, 238))
    wy = y + int(h * 0.68)
    d.rectangle([x, wy, x + w, y + h], fill=(120, 160, 185))
    d.polygon([(x + 30, wy - 6), (x + w - 30, wy - 6), (x + w - 44, wy + 5),
               (x + 44, wy + 5)], fill=(50, 54, 60))
    d.rectangle([x + w - 56, wy - 12, x + w - 40, wy - 6], fill=(210, 208, 200))
    _flame(d, x + 62, wy - 2, 7)


def mini_power(d, x, y, w, h):
    _mini_base(d, x, y, w, h, (250, 240, 205))
    px = x + int(w * 0.3)
    d.line([(px, y + h - 4), (px, y + 5)], fill=(70, 66, 60), width=3)
    d.line([(px - 16, y + 10), (px + 16, y + 10)], fill=(70, 66, 60), width=2)
    d.line([(px - 11, y + 17), (px + 11, y + 17)], fill=(70, 66, 60), width=2)
    # lightning bolt
    bx = x + int(w * 0.68)
    d.polygon([(bx, y + 4), (bx - 8, y + 14), (bx - 2, y + 14),
               (bx - 6, y + h - 5), (bx + 6, y + 12), (bx, y + 12)],
              fill=(230, 170, 20))
    d.rectangle([x + int(w * 0.82), y + 6, x + w - 6, y + h - 6],
                fill=(60, 60, 60))
    d.text((x + int(w * 0.82) + 3, y + 7), "2h", font=font("sans_b", 9),
           fill=(250, 240, 200))


def mini_ballot(d, x, y, w, h):
    _mini_base(d, x, y, w, h, (232, 228, 245))
    bx, by = x + int(w * 0.32), y + 8
    d.rectangle([bx, by, bx + 30, by + 10], fill=(122, 80, 160))
    d.rectangle([bx + 7, by - 2, bx + 23, by], fill=(60, 50, 70))
    d.rectangle([bx + 11, y + 1, bx + 19, y + 6], fill=(255, 255, 255),
                outline=(120, 120, 120))
    d.line([(bx + 13, y + 4), (bx + 15, y + 5), (bx + 17, y + 2)],
           fill=(27, 120, 60), width=1)
    d.text((x + int(w * 0.58), y + 1), "723", font=font("sans_b", 13),
           fill=(122, 80, 160))
    d.text((x + int(w * 0.58), y + 12), "SEATS", font=font("sans_b", 7),
           fill=GREY)


def mini_plane(d, x, y, w, h):
    _mini_base(d, x, y, w, h, (214, 232, 240))
    cx, cy = x + int(w * 0.42), y + 10
    d.ellipse([cx - 24, cy - 3, cx + 24, cy + 3], fill=(70, 90, 108))
    d.polygon([(cx - 6, cy - 2), (cx + 6, cy - 10), (cx + 12, cy - 10),
               (cx + 9, cy - 2)], fill=(70, 90, 108))
    d.polygon([(cx - 2, cy + 2), (cx - 14, cy + 8), (cx - 7, cy + 8),
               (cx + 3, cy + 2)], fill=(90, 110, 128))
    d.polygon([(cx + 20, cy - 2), (cx + 26, cy - 8), (cx + 28, cy - 2)],
              fill=(70, 90, 108))
    for i in range(5):  # dotted flight path
        d.ellipse([x + w - 52 + i * 9, y + 8 + i, x + w - 50 + i * 9, y + 10 + i],
                  fill=(150, 150, 150))
    d.text((x + w - 46, y + 7), "DELHI", font=font("sans_b", 8),
           fill=(37, 99, 165))


def mini_nato(d, x, y, w, h):
    _mini_base(d, x, y, w, h, (220, 230, 245))
    cx, cy = x + int(w * 0.3), y + 10
    d.ellipse([cx - 9, cy - 9, cx + 9, cy + 9], outline=(37, 99, 165),
              width=2)
    d.polygon([(cx, cy - 9), (cx + 3, cy - 3), (cx, cy), (cx - 3, cy - 3)],
              fill=(37, 99, 165))
    d.polygon([(cx, cy + 9), (cx + 3, cy + 3), (cx, cy), (cx - 3, cy + 3)],
              fill=(37, 99, 165))
    d.polygon([(cx - 9, cy), (cx - 3, cy + 3), (cx, cy), (cx - 3, cy - 3)],
              fill=(37, 99, 165))
    d.polygon([(cx + 9, cy), (cx + 3, cy + 3), (cx, cy), (cx + 3, cy - 3)],
              fill=(37, 99, 165))
    # Polish flag, centred vertically; no text (headline names Warsaw)
    d.rectangle([x + int(w * 0.55), y + 5, x + w - 8, y + 10],
                fill=(255, 255, 255), outline=(180, 180, 180))
    d.rectangle([x + int(w * 0.55), y + 10, x + w - 8, y + 15],
                fill=(220, 20, 60))


def mini_van(d, x, y, w, h):
    _mini_base(d, x, y, w, h, (240, 232, 220))
    vx, vy = x + 16, y + 2
    d.rectangle([vx, vy, vx + 66, vy + 11], fill=(235, 235, 230),
                outline=(120, 120, 120))
    d.polygon([(vx + 66, vy + 3), (vx + 82, vy + 8), (vx + 82, vy + 11),
               (vx + 66, vy + 11)], fill=(200, 200, 195), outline=(120, 120, 120))
    for wx in (vx + 14, vx + 70):
        d.ellipse([wx - 4, vy + 9, wx + 4, vy + 17], fill=(40, 40, 40))
        d.ellipse([wx - 1, vy + 12, wx + 1, vy + 14], fill=(180, 180, 180))
    d.text((vx + 5, vy + 2), "WCK", font=font("sans_b", 7), fill=(27, 120, 60))
    d.line([(vx + 34, vy + 2), (vx + 46, vy + 10)], fill=RED, width=2)
    d.line([(vx + 46, vy + 2), (vx + 34, vy + 10)], fill=RED, width=2)
    d.text((x + w - 42, y + 3), "GAZA", font=font("sans_b", 8), fill=RED_DARK)


def mini_f1(d, x, y, w, h):
    _mini_base(d, x, y, w, h, (235, 235, 235))
    cy = y + 10
    d.rectangle([x + 18, cy - 4, x + w - 40, cy + 2], fill=(178, 30, 30))
    d.polygon([(x + 30, cy - 4), (x + 42, cy - 9), (x + 56, cy - 9),
               (x + 62, cy - 4)], fill=(178, 30, 30))
    d.rectangle([x + w - 40, cy - 9, x + w - 33, cy + 2], fill=(40, 40, 40))
    for wx in (x + 34, x + w - 56):
        d.ellipse([wx - 6, cy + 1, wx + 6, cy + 9], fill=(25, 25, 25))
        d.ellipse([wx - 2, cy + 3, wx + 2, cy + 7], fill=(160, 160, 160))
    # chequered flag
    fx, fy = x + w - 24, y + 2
    for r in range(3):
        for c in range(3):
            if (r + c) % 2 == 0:
                d.rectangle([fx + c * 4, fy + r * 4, fx + c * 4 + 4, fy + r * 4 + 4],
                            fill=(30, 30, 30))
    d.line([(fx, fy), (fx, fy + 16)], fill=(80, 80, 80), width=1)


def mini_football(d, x, y, w, h):
    _mini_base(d, x, y, w, h, (222, 240, 222))
    gy = y + 14
    d.rectangle([x, gy, x + w, y + h], fill=(120, 180, 110))
    d.line([(x + 14, y + 4), (x + 14, gy)], fill=(255, 255, 255), width=3)
    d.line([(x + 14, y + 4), (x + 62, y + 4)], fill=(255, 255, 255), width=3)
    d.line([(x + 62, y + 4), (x + 62, gy)], fill=(255, 255, 255), width=3)
    cx, cy = x + int(w * 0.72), y + 9
    d.ellipse([cx - 8, cy - 8, cx + 8, cy + 8], fill=(255, 255, 255),
              outline=(60, 60, 60))
    d.polygon([(cx, cy - 5), (cx + 5, cy - 1), (cx + 3, cy + 4),
               (cx - 3, cy + 4), (cx - 5, cy - 1)], fill=(40, 40, 40))
    d.text((x + 70, y + 6), "16:30 GMT", font=font("sans_b", 8), fill=GREY)


def mini_tennis(d, x, y, w, h):
    _mini_base(d, x, y, w, h, (240, 235, 205))
    cx, cy = x + int(w * 0.32), y + 9
    d.ellipse([cx - 10, cy - 9, cx + 10, cy + 7], outline=(90, 70, 40),
              width=3)
    d.line([(cx - 6, cy - 5), (cx + 6, cy - 5)], fill=(150, 150, 150), width=1)
    d.line([(cx - 9, cy + 1), (cx + 9, cy + 1)], fill=(150, 150, 150), width=1)
    d.line([(cx - 6, cy + 5), (cx + 6, cy + 5)], fill=(150, 150, 150), width=1)
    d.line([(cx, cy - 7), (cx, cy + 5)], fill=(150, 150, 150), width=1)
    d.line([(cx - 1, cy + 7), (cx + 4, y + 19)], fill=(90, 70, 40), width=3)
    bx, by = x + int(w * 0.78), y + 8
    d.ellipse([bx - 7, by - 7, bx + 7, by + 7], fill=(210, 225, 60),
              outline=(150, 160, 40))
    d.arc([bx - 7, by - 7, bx + 7, by + 7], 300, 60, fill=(255, 255, 255),
          width=2)
    d.text((x + int(w * 0.52), y + 12), "TURIN", font=font("sans_b", 8),
           fill=GREY)


def mini_cricket(d, x, y, w, h):
    _mini_base(d, x, y, w, h, (228, 238, 222))
    gy = y + 15
    d.rectangle([x, gy, x + w, y + h], fill=(140, 190, 120))
    # stumps
    for sx in (x + 26, x + 34, x + 42):
        d.rectangle([sx, gy - 13, sx + 4, gy], fill=(220, 190, 90))
    d.rectangle([x + 26, gy - 15, x + 46, gy - 13], fill=(220, 190, 90))
    # bat
    d.polygon([(x + 78, y + 6), (x + 88, y + 6), (x + 96, gy - 6),
               (x + 86, gy - 2)], fill=(210, 180, 120),
              outline=(140, 110, 60))
    d.line([(x + 83, y + 6), (x + 76, y + 2)], fill=(120, 90, 50), width=3)
    # red ball
    d.ellipse([x + w - 33, y + 7, x + w - 21, y + 19], fill=(178, 30, 30))
    d.text((x + 100, y + 3), "WINDY", font=font("sans_b", 8), fill=GREY)


ICONS = {
    "tanker": mini_tanker, "power": mini_power, "ballot": mini_ballot,
    "plane": mini_plane, "nato": mini_nato, "van": mini_van,
    "f1": mini_f1, "football": mini_football, "tennis": mini_tennis,
    "cricket": mini_cricket,
}

# ----------------------------------------------------------------- sections
def paint_masthead(d, y):
    title = "THE WORLD IN ONE DAY"
    f = font("serif_b", 38)
    centre(d, PAGE_W // 2, y, title, f, INK)
    sub = "35 STORIES  ·  7 REGIONS  ·  EVERY ONE DATED SUNDAY 22 NOVEMBER 2026"
    sf = font("sans_b", 10)
    centre(d, PAGE_W // 2, y + 40, sub, sf, RED_DARK)
    rule(d, EDGE, y + 54, PAGE_W - EDGE, width=2)
    rule(d, EDGE, y + 57, PAGE_W - EDGE, width=1)
    return y + 60


def paint_title_block(d, y):
    centre(d, PAGE_W // 2, y, "Sunday 22 November 2026", font("serif_b", 33), INK)
    sub = ("COP31 nears a deal in Antalya  ·  Iran strikes US bases in "
           "Bahrain  ·  Sparta II still burning in the Gulf of Finland")
    centre(d, PAGE_W // 2, y + 34, sub, font("serif_i", 13), RED)
    return y + 50


def paint_stat_strip(d, y):
    h = 46
    d.rectangle([EDGE, y, PAGE_W - EDGE, y + h], fill=(238, 232, 216))
    rule(d, EDGE, y, PAGE_W - EDGE, width=1)
    rule(d, EDGE, y + h, PAGE_W - EDGE, width=1)
    cell = INNER // 6
    for i, (num, label, src) in enumerate(STATS):
        cx = EDGE + cell * i + cell // 2
        if i:
            d.line([(EDGE + cell * i, y + 6), (EDGE + cell * i, y + h - 6)],
                   fill=PALE, width=1)
        centre(d, cx, y + 1, num, font("serif_b", 23), RED_DARK)
        centre(d, cx, y + 26, label, font("sans_b", 8), INK)
        centre(d, cx, y + 35, src, font("sans_i", 8), GREY)
    return y + h + 2


def paint_region_bar(d, y):
    total = sum(n for _, n in REGIONS)
    bx = EDGE
    for name, n in REGIONS:
        seg = int(INNER * n / total)
        hue = REGION_HUES[name]
        d.rectangle([bx, y, bx + seg, y + 18], fill=hue)
        lab = f"{name} {n}" if seg >= 60 else str(n)
        centre(d, bx + seg // 2, y + 4, lab, font("sans_b", 9),
               (255, 255, 255))
        bx += seg
    note = "AFRICA 1  ·  GLOBAL 1 — one story each (UN Security Council item)"
    d.text((EDGE, y + 20), note, font=font("sans", 8), fill=GREY)
    d.text((PAGE_W - EDGE - tw(d, "SHARE OF 35 STORIES", font("sans_b", 8)),
            y + 20), "SHARE OF 35 STORIES", font=font("sans_b", 8), fill=GREY)
    return y + 30


def paint_timeline(d, y):
    d.text((EDGE, y), "SUNDAY IN UTC", font=font("sans_b", 10), fill=INK)
    right = "ALL TIMES UTC  ·  PRESS TIME 04:00 UTC"
    d.text((PAGE_W - EDGE - tw(d, right, font("sans", 8)), y + 1), right,
           font=font("sans", 8), fill=GREY)
    line_y = y + 23
    rule(d, EDGE, line_y, PAGE_W - EDGE, width=1, color=PALE)
    slot = INNER / len(TIMELINE)
    for i, (t, label) in enumerate(TIMELINE):
        cx = EDGE + slot * (i + 0.5)
        centre(d, cx, y + 11, t, font("sans_b", 10), RED_DARK)
        d.ellipse([cx - 4, line_y - 4, cx + 4, line_y + 4], fill=RED,
                  outline=(255, 255, 255), width=1)
        # one line each: every label fits its 122 px slot at 8px
        centre(d, cx, line_y + 5, label, font("sans", 8), INK)
    return y + 38


def paint_hero(img, d, x, y, w, h, hero):
    d.rectangle([x, y, x + w, y + h], fill=CARD_BG, outline=(130, 128, 118))
    ill_h = 86
    _clip_paint(img, x + 1, y + 1, w - 2, ill_h, SCENES[hero["scene"]])
    # number badge
    d.rectangle([x + 1, y + 1, x + 19, y + 19], fill=RED)
    centre(d, x + 10, y + 3, str(hero["num"]), font("sans_b", 11),
           (255, 255, 255))
    # stat chip over the illustration
    sf, ssf = font("sans_b", 12), font("sans", 8)
    chip_w = max(tw(d, hero["stat"], sf), tw(d, hero["stat_sub"], ssf)) + 14
    chip_y = y + ill_h - 30
    d.rectangle([x + 6, chip_y, x + 6 + chip_w, chip_y + 26],
                fill=(255, 253, 246), outline=RED)
    d.text((x + 13, chip_y + 2), hero["stat"], font=sf, fill=RED_DARK)
    d.text((x + 13, chip_y + 15), hero["stat_sub"], font=ssf, fill=GREY)
    # kicker + day + status
    ky = y + ill_h + 4
    d.text((x + 8, ky), f"{hero['kicker']}  ·  {hero['day']}",
           font=font("sans_b", 9), fill=RED)
    status_chip(d, x + w - 8, ky, hero["status"])
    # headline (one line at 16px; fit() guards the overflow)
    hy = ky + 13
    head_lines = fit(d, hero["headline"], font("serif_b", 16), w - 16, 2)
    for j, ln in enumerate(head_lines):
        d.text((x + 8, hy + j * 18), ln, font=font("serif_b", 16), fill=INK)
    # body, 4 lines
    by = hy + len(head_lines) * 18 + 2
    for j, ln in enumerate(fit(d, hero["body"], font("sans", 9), w - 16, 4)):
        d.text((x + 8, by + j * 11), ln, font=font("sans", 9), fill=INK)
    # location line
    loc = f"{hero['num']}  ·  {hero['place']}  ·  {hero['topic']}"
    d.text((x + 8, y + h - 12), loc, font=font("sans_b", 8), fill=GREY)


def paint_small(img, d, x, y, w, h, story):
    d.rectangle([x, y, x + w, y + h], fill=CARD_BG, outline=(150, 148, 138))
    _clip_paint(img, x + 1, y + 1, w - 2, 20, ICONS[story["icon"]])
    d.rectangle([x + 1, y + 1, x + 15, y + 15], fill=RED)
    centre(d, x + 8, y + 2, str(story["num"]), font("sans_b", 9),
           (255, 255, 255))
    ky = y + 23
    d.text((x + 6, ky), f"{story['kicker']}  ·  {story['day']}",
           font=font("sans_b", 8), fill=RED)
    status_chip(d, x + w - 6, ky, story["status"])
    head_lines = fit(d, story["headline"], font("serif_b", 12), w - 12, 2)
    hy = ky + 12
    for j, ln in enumerate(head_lines):
        d.text((x + 6, hy + j * 13), ln, font=font("serif_b", 12), fill=INK)
    by = hy + len(head_lines) * 13 + 1
    for j, ln in enumerate(fit(d, story["body"], font("sans", 9), w - 12, 3)):
        d.text((x + 6, by + j * 10), ln, font=font("sans", 9), fill=INK)


def paint_map_panel(d, x, y, w, h):
    d.rectangle([x, y, x + w, y + h], fill=CARD_BG, outline=(130, 128, 118))
    d.text((x + 8, y + 5), "WHERE IT HAPPENED", font=font("sans_b", 10), fill=INK)
    note = "PIN = STORY NUMBER"
    d.text((x + w - 8 - tw(d, note, font("sans", 8)), y + 6), note,
           font=font("sans", 8), fill=GREY)
    mx, my = x + 8, y + 20
    mw, mh = w - 16, 220
    d.rectangle([mx, my, mx + mw, my + mh], fill=SEA)
    lat_top, lat_bot = 84.0, -58.0

    def to_xy(lon, lat):
        px = mx + (lon + 180.0) / 360.0 * mw
        py = my + (lat_top - lat) / (lat_top - lat_bot) * mh
        return px, py

    step = 4
    for gy in range(my, my + mh, step):
        lat = lat_top - (gy + step / 2 - my) / mh * (lat_top - lat_bot)
        for gx in range(mx, mx + mw, step):
            lon = -180.0 + (gx + step / 2 - mx) / mw * 360.0
            if is_land(lon, lat):
                d.rectangle([gx, gy, gx + 1, gy + 1], fill=LAND)
    # pins with leader lines
    for num, lon, lat, region, dx, dy in PINS:
        px, py = to_xy(lon, lat)
        bx, by = px + dx, py + dy
        hue = REGION_HUES[region]
        d.line([(px, py), (bx, by)], fill=hue, width=1)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=hue)
        d.ellipse([bx - 7, by - 7, bx + 7, by + 7], fill=hue,
                  outline=(255, 255, 255), width=1)
        centre(d, bx, by - 6, str(num), font("sans_b", 8), (255, 255, 255))
    # legend: two rows of region colours
    ly = my + mh + 8
    cols = [("EUROPE", "MIDDLE EAST", "ASIA-PACIFIC", "AMERICAS"),
            ("AFRICA", "OCEANIA", "GLOBAL", "PIN COLOUR = REGION")]
    for r, row in enumerate(cols):
        cx = x + 8
        for name in row:
            if name in REGION_HUES:
                d.rectangle([cx, ly + r * 13, cx + 8, ly + r * 13 + 8],
                            fill=REGION_HUES[name])
                d.text((cx + 11, ly + r * 13 - 1), name, font=font("sans_b", 8),
                       fill=INK)
                cx += 13 + tw(d, name, font("sans_b", 8)) + 10
            else:
                d.text((cx, ly + r * 13 - 1), name, font=font("sans_i", 8),
                       fill=GREY)


def paint_more_list(d, x, y, w, h):
    d.text((x, y), "22 MORE STORIES", font=font("sans_b", 11), fill=INK)
    note = "EVERY ITEM SOURCED  ·  DAY-TAGGED"
    d.text((x + w - tw(d, note, font("sans", 8)), y + 2), note,
           font=font("sans", 8), fill=GREY)
    rule(d, x, y + 15, x + w, width=1)
    col_w = (w - 12) // 2
    f_num, f_txt = font("sans_b", 9), font("sans", 9)
    for idx, (num, text, day) in enumerate(MORE):
        col = 0 if idx < 11 else 1
        row = idx % 11
        ix = x + col * (col_w + 12)
        iy = y + 20 + row * 24
        d.text((ix, iy), f"{num}.", font=f_num, fill=RED)
        tx = ix + 20
        full = f"{text} · {day}"
        lines = fit(d, full, f_txt, col_w - 20, 2)
        for j, ln in enumerate(lines):
            d.text((tx, iy + j * 11), ln, font=f_txt, fill=INK)
        # repaint the day tag in red, same font so it lands exactly over
        # the black original (a bold repaint would be wider and smear)
        last = lines[-1]
        if last.endswith(day):
            cut = last.rfind("·")
            if cut >= 0:
                pre, tag_txt = last[:cut], last[cut:]
            else:  # "·" wrapped onto the previous line; colour the day only
                pre, tag_txt = last[:len(last) - len(day)], day
            d.text((tx + tw(d, pre, f_txt), iy + (len(lines) - 1) * 11),
                   tag_txt, font=f_txt, fill=RED)


def paint_date_check(d, y):
    lines = [
        ("METHOD — ", "first Reuters/AP wire or official release; every "
         "story carries its day tag: SUN Sunday 22 Nov · SAT Saturday "
         "21 Nov · FRI Friday 20 Nov."),
        ("LEFT OUT — ", "Peru M6.8 quake (Friday 20 Nov local) · Russia\u2019s "
         "400-drone wave (Thu night–Fri) · Kerch bridge strikes (earlier "
         "this week) · Shenzhen summit (19 Nov) · ICJ Myanmar ruling + "
         "Greenland vote (earlier this week) · \u201cCOP31 deal reached\u201d "
         "claims — approval is 06:00 GMT, so \u201cnears\u201d, not done."),
        ("", "Some list items were first reported Fri/Sat and are still "
         "developing — weekend news, shown as it is. STILL TO COME: COP31 "
         "approval 06:00 GMT · Las Vegas GP · ATP final · Liverpool v "
         "Man Utd."),
    ]
    h = 64
    d.rectangle([EDGE, y, PAGE_W - EDGE, y + h], fill=(253, 246, 240),
                outline=RED, width=2)
    d.text((EDGE + 8, y + 4), "DATE CHECK", font=font("sans_b", 10), fill=RED)
    ly = y + 17
    f_lab, f_txt = font("sans_b", 9), font("sans", 9)
    for label, text in lines:
        wrapped = wrap(d, label + text, f_txt, INNER - 16)
        for j, ln in enumerate(wrapped):
            yy = ly + j * 11
            if j == 0 and label:
                d.text((EDGE + 8, yy), label, font=f_lab, fill=RED_DARK)
                d.text((EDGE + 8 + tw(d, label, f_lab), yy),
                       ln[len(label):], font=f_txt, fill=INK)
            else:
                d.text((EDGE + 8, yy), ln, font=f_txt, fill=INK)
        ly += len(wrapped) * 11
    return y + h + 2


def paint_how_checked(d, y):
    parts = [("HOW WE CHECKED — ", INK, "sans_b"),
             ("CONFIRMED", STATUS_HUES["CONFIRMED"], "sans_b"),
             (" = 2+ outlets  ·  ", GREY, "sans"),
             ("OFFICIAL", STATUS_HUES["OFFICIAL"], "sans_b"),
             (" = on the record  ·  ", GREY, "sans"),
             ("REPORTED", STATUS_HUES["REPORTED"], "sans_b"),
             (" = one outlet  ·  ", GREY, "sans"),
             ("CLAIM", STATUS_HUES["CLAIM"], "sans_b"),
             (" = one side\u2019s claim  ·  ", GREY, "sans"),
             ("FORECAST", STATUS_HUES["FORECAST"], "sans_b"),
             (" = scheduled today", GREY, "sans")]
    total = sum(tw(d, t, font(k, 9)) for t, _, k in parts)
    cx = (PAGE_W - total) / 2
    for t, col, kind in parts:
        f = font(kind, 9)
        d.text((cx, y), t, font=f, fill=col)
        cx += tw(d, t, f)
    return y + 12


def paint_footer(d, y):
    main = ("Every story here happened, was first reported, or is scheduled "
            "for Sunday 22 November 2026. Sources named beside each story. "
            "Pictures and map: original, drawn in code.")
    centre(d, PAGE_W // 2, y, main, font("sans", 9), GREY)
    centre(d, PAGE_W // 2, y + 10,
           "Press time: Sunday 22 November 2026, 04:00 UTC.",
           font("sans_b", 9), INK)
    return y + 22


# -------------------------------------------------------------------- build
def build():
    img = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    d = ImageDraw.Draw(img)
    y = 12
    y = paint_masthead(d, y)            # -> 72
    y = paint_title_block(d, y + 2)     # -> 124
    y = paint_stat_strip(d, y + 2)      # -> 174
    y = paint_region_bar(d, y + 2)      # -> 206
    y = paint_timeline(d, y + 2)        # -> 246
    hero_y, hero_h = y + 2, 176
    hero_w = (INNER - 16) // 3
    for i, hero in enumerate(HEROES):
        paint_hero(img, d, EDGE + i * (hero_w + 8), hero_y, hero_w, hero_h, hero)
    y = hero_y + hero_h + 6             # -> 430
    small_w = (INNER - 4 * 6) // 5
    small_h = 90
    for i, story in enumerate(SMALLS):
        r, c = divmod(i, 5)
        paint_small(img, d, EDGE + c * (small_w + 6), y + r * (small_h + 6),
                    small_w, small_h, story)
    y = y + 2 * small_h + 6 + 6         # -> 622
    map_w = 344
    section_h = 282
    paint_map_panel(d, EDGE, y, map_w, section_h)
    paint_more_list(d, EDGE + map_w + 12, y, INNER - map_w - 12, section_h)
    y = y + section_h + 6               # -> ~908
    y = paint_date_check(d, y)          # -> ~974
    y = paint_how_checked(d, y + 1)     # -> ~987
    y = paint_footer(d, y + 1)          # -> ~1010, must stay <= 1024
    return img, y


def main():
    img, bottom = build()
    img.save(OUT, format="PNG")
    data = open(OUT, "rb").read()
    print(f"wrote {OUT}")
    print(f"size: {img.size[0]}x{img.size[1]} mode={img.mode}")
    print(f"bytes: {len(data)}")
    print(f"sha256: {hashlib.sha256(data).hexdigest()}")
    print(f"content bottom y: {bottom} (page height {PAGE_H})")
    print(f"stories: {len(HEROES)} hero + {len(SMALLS)} small + "
          f"{len(MORE)} list = {len(HEROES) + len(SMALLS) + len(MORE)}")


if __name__ == "__main__":
    main()
