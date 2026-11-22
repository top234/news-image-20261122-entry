#!/usr/bin/env python3
"""The Dawn Ledger — news-image-20261122 v2.

Draws a 1024x1024 one-page newspaper front page summing up
Sunday 22 November 2026's world news: 3 hero stories, 8 small
cards, a world map with 11 numbered pins, and a numbered list of
27 more stories (38 total). Deterministic: fixed strings, fixed
geometry, no network, no clock, no randomness.

Run:  python3 generate.py   -> writes entry.png next to this file.
"""
import hashlib
import os
import sys

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "entry.png")

PAGE_W, PAGE_H = 1024, 1024
MARGIN = 24
CONTENT_W = PAGE_W - 2 * MARGIN

# ---- palette ------------------------------------------------------------
PAPER = (246, 239, 221)
INK = (28, 35, 51)
NAVY = (22, 35, 63)
RED = (163, 31, 31)
TEAL = (15, 91, 77)
DARKRED = (127, 29, 29)
STEEL = (29, 53, 87)
GOLD = (185, 138, 29)
MUTED = (107, 101, 88)
CARD = (255, 253, 246)
EDGE = (201, 191, 165)
SEA = (216, 230, 234)
LAND = (226, 228, 194)
LAND_EDGE = (170, 178, 140)
PIN = (176, 30, 30)
CHIP_BG = (255, 253, 246)

FONT_DIR = "/usr/share/fonts/truetype/dejavu"


def load(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


F_TITLE = load("DejaVuSerif-Bold.ttf", 48)
F_MAST = load("DejaVuSans-Bold.ttf", 15)
F_TOPRIGHT = load("DejaVuSans-Bold.ttf", 12)
F_SUB = load("DejaVuSerif.ttf", 14)
F_CHIP_V = load("DejaVuSans-Bold.ttf", 12)
F_CHIP_L = load("DejaVuSans.ttf", 10)
F_REGION = load("DejaVuSans-Bold.ttf", 11)
F_HERO_KICK = load("DejaVuSans-Bold.ttf", 11)
F_HERO_HEAD = load("DejaVuSerif-Bold.ttf", 16)
F_HERO_BODY = load("DejaVuSans.ttf", 9)
F_HERO_SRC = load("DejaVuSans-Bold.ttf", 8)
F_TAG = load("DejaVuSans-Bold.ttf", 8)
F_SM_KICK = load("DejaVuSans-Bold.ttf", 10)
F_SM_HEAD = load("DejaVuSerif-Bold.ttf", 13)
F_SM_BODY = load("DejaVuSans.ttf", 9)
F_SM_SRC = load("DejaVuSans-Bold.ttf", 7)
F_SEC = load("DejaVuSans-Bold.ttf", 13)
F_SEC_SUB = load("DejaVuSans.ttf", 10)
F_MAPCAP = load("DejaVuSans.ttf", 9)
F_DATE = load("DejaVuSans-Bold.ttf", 11)
F_DATE_BODY = load("DejaVuSans.ttf", 10)
F_FOOT = load("DejaVuSans.ttf", 10)
F_FOOT_B = load("DejaVuSans-Bold.ttf", 10)

warnings = []


def note(msg):
    warnings.append(msg)
    print("WARN:", msg)


# ---- text helpers -------------------------------------------------------
def wrap_text(draw, text, fnt, width):
    """Greedy word wrap; returns a list of lines that fit `width`."""
    lines, cur = [], ""
    for word in text.split(" "):
        trial = word if not cur else cur + " " + word
        if draw.textlength(trial, font=fnt) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_wrapped(draw, x, y, lines, fnt, fill, leading):
    for ln in lines:
        draw.text((x, y), ln, font=fnt, fill=fill)
        y += leading
    return y


def day_tag(draw, x, y, tag, col=RED):
    """Small outlined day tag; returns its width."""
    w = int(draw.textlength(tag, font=F_TAG)) + 10
    draw.rounded_rectangle([x, y, x + w, y + 13], radius=3,
                           outline=col, width=1)
    draw.text((x + 5, y + 2), tag, font=F_TAG, fill=col)
    return w


def num_badge(draw, x, y, num, d=17):
    draw.ellipse([x, y, x + d, y + d], fill=RED)
    txt = str(num)
    tw = draw.textlength(txt, font=F_TAG)
    draw.text((x + (d - tw) / 2, y + 3), txt, font=F_TAG, fill=(255, 255, 255))


# ---- data ---------------------------------------------------------------
HEROES = [
    {
        "num": 1, "color": TEAL, "kick": "COP31 NEARS DEAL", "tag": "SUN",
        "head": "UN climate talks in Antalya approach a final deal at dawn",
        "body": ("New package announced overnight; delegations have until "
                 "03:00 GMT to object, approval session 06:00 GMT Sunday. "
                 "Australia leads the talks, Turkey hosts, ~200 delegations; "
                 "ran past the Friday deadline through Saturday night."),
        "src": "SOURCE: REUTERS", "art": "sunrise",
    },
    {
        "num": 2, "color": STEEL, "kick": "SPARTA II ABLAZE", "tag": "SAT",
        "head": "Russian-flagged cargo ship Sparta II hit by two drones in the Gulf of Finland",
        "body": ("Fire breaks out, ship drifts into Finnish waters; all 16 "
                 "crew evacuate to lifeboats. Finland says Ukraine likely "
                 "behind it; Russian helicopter suspected of entering "
                 "Finnish airspace near Loviisa. Sanctioned Oboronlogistika "
                 "vessel, St Petersburg \u2192 Kaliningrad."),
        "src": "SOURCE: REUTERS / FINLAND DEFENCE FORCES", "art": "shipfire",
    },
    {
        "num": 3, "color": DARKRED, "kick": "TANKERS HIT OFF OMAN", "tag": "SUN",
        "head": "Two tankers struck by unknown projectiles off Oman, UK maritime agency says",
        "body": ("One hit in the engine room 17 nm east of Khasab, one in "
                 "the stern 11 nm north; no casualties at the warning; "
                 "fourth strike in 24 hours in the strait."),
        "src": "SOURCE: UKMTO / REUTERS", "art": "tanker",
    },
]

SMALLS = [
    {"num": 4, "kick": "FRANCE: MYANMAR TO UN", "tag": "SAT",
     "head": "France to seek a UN Security Council meeting",
     "body": ("After Myanmar rejects the ICJ genocide ruling; ICJ rulings "
              "are final and binding; The Gambia may seek enforcement under "
              "Article 94; China or Russia could veto."),
     "src": "REUTERS", "glyph": "scales"},
    {"num": 5, "kick": "900,000 AI CHIPS FOR CHINA", "tag": "FRI",
     "head": "US cleared nearly 900,000 AI chips for China",
     "body": ("Nvidia/AMD chips in six months (Dec\u2013May): 150,000 Tencent, "
              "75,000 Alibaba, 43,000 Baidu, 4,000 BYD \u2014 all on the "
              "Pentagon military-companies list; 3.4m requested; Nvidia has "
              "since stopped shipping H200s."),
     "src": "HOUSE FOREIGN AFFAIRS COMMITTEE / REUTERS", "glyph": "chip"},
    {"num": 6, "kick": "PERU QUAKE", "tag": "SAT",
     "head": "M6.8 quake in Jun\u00edn, 129 km deep, felt in Lima",
     "body": "No casualties or damage reported.",
     "src": "GFZ / REUTERS", "glyph": "quake"},
    {"num": 7, "kick": "SHENZHEN", "tag": "WEEK",
     "head": "Trump, Xi & Putin sign a four-point peace declaration",
     "body": "Signed in Shenzhen; it says nothing about Ukraine.",
     "src": "AP / REUTERS", "glyph": "dove"},
    {"num": 8, "kick": "MARKETS ROUT", "tag": "FRI",
     "head": "Nasdaq worst week since 2020, \u221210.4%",
     "body": ("S&P 500 falls into correction; Dow \u22121,101 to 49,097; "
              "Nvidia under SEC probe, \u221214%; gold \u22122.8% to "
              "$3,518.50/oz."),
     "src": "AP / REUTERS", "glyph": "chart"},
    {"num": 9, "kick": "GULF WAR WIDENS", "tag": "WED",
     "head": "Iran drones hit US base in Kuwait and sites in Bahrain",
     "body": ("US jets had struck an IRGC missile site on Qeshm Island; war "
              "began 28 Feb; ADNOC-linked tanker hit in Hormuz, 1 crew "
              "missing, 11 hurt."),
     "src": "AP / REUTERS", "glyph": "flame"},
    {"num": 10, "kick": "MYANMAR GENOCIDE", "tag": "WEEK",
     "head": "World Court: Myanmar committed genocide",
     "body": ("ICJ rules Myanmar committed genocide against the Rohingya \u2014 "
              "first time any international court has found a state guilty "
              "of genocide."),
     "src": "ICJ", "glyph": "gavel"},
    {"num": 11, "kick": "KERCH BRIDGE HIT", "tag": "SAT",
     "head": "Ukraine strikes the bridge to Crimea a third time",
     "body": ("Third strike in four days; Zelensky calls it a \u201cfair "
              "response\u201d; Berlin talks under way."),
     "src": "AP / REUTERS", "glyph": "bridge"},
]

# (number, lead-in-bold-or-None, text, day-tag)
MORE = [
    (12, None, "North Korea expanding Yongbyon uranium enrichment plant, IAEA says.", "WEEK"),
    (13, None, "Bangladesh violence flares ahead of Sheikh Hasina\u2019s planned return.", "WEEK"),
    (14, None, "US signs new military deal with Venezuela, 10 months after US forces removed Maduro.", "WEEK"),
    (15, None, "Poland: two Russian missiles and a drone land in rural Poland; PM Tusk responds.", "FRI"),
    (16, None, "Denmark accuses Russia of plotting to assassinate a US-Ukrainian rapper near Copenhagen.", "FRI"),
    (17, "SKYLIGHT HIT", "Palau-flagged tanker Skylight hit near Khasab; all 20 crew evacuated, 4 hurt \u2014 fourth strike in 24 hours.", "SUN"),
    (18, None, "FBI investigating apparent hack of its criminal database.", "FRI"),
    (19, None, "Mexican army captures cartel kingpin Fausto Isidro Meza Flores, \u201cEl Chapo Isidro\u201d.", "WEEK"),
    (20, None, "Pentagon memo tells US troops to curb informal gatherings with Canadian counterparts.", "WEEK"),
    (21, None, "Trump threatens a \u201ctremendous tax\u201d on US firms building AI data centres overseas.", "FRI"),
    (22, None, "Zscaler jumps 18% on report CrowdStrike is in talks to buy it.", "SAT"),
    (23, None, "India: Modi inaugurates Nitish Setu, linking Patna and Vaishali.", "SUN"),
    (24, "GREENLAND DEAL", "Denmark votes 109\u20130 to ratify a new US security deal; two new American bases.", "WEEK"),
    (25, None, "India face New Zealand in the 1st Test in windy Wellington.", "SUN"),
    (26, None, "Sensex ends a two-day rally on profit booking and US Fed rate worries.", "SUN"),
    (27, None, "Pat Cummins keeps Australia\u2019s Test captaincy with unanimous support.", "SUN"),
    (28, "ESTONIA SHUTS BORDER", "Estonia to close all 5 road crossings with Russia from 1 Dec for 6 months after a GRU-linked arson attempt on drone-maker Threod Systems; Moscow calls it a \u201cnew Iron Curtain\u201d.", "FRI"),
    (29, None, "Chess: Erigaisi and Praggnanandhaa win; Vaishali loses on classification day one.", "SUN"),
    (30, None, "South Africa local elections: ANC fights to keep control of the cities.", "SUN"),
    (31, None, "Mamdani reveals plan to close New York\u2019s Rikers Island jail.", "WEEK"),
    (32, None, "Nepal PM Balendra Shah to meet Modi on his first bilateral visit.", "SUN"),
    (33, "ANTHROPIC IPO", "$81.3bn IPO, the biggest in history; shares +39% on debut, then fall the next day.", "FRI"),
    (34, None, "US Forest Service releases its 1982 file on alleged Bigfoot footprints.", "WEEK"),
    (35, None, "Trafalgar Square\u2019s Christmas tree sets off from Oslo for London.", "SAT"),
    (36, None, "Man guilty of starting the Palisades fire, one of California\u2019s deadliest blazes.", "FRI"),
    (37, None, "Air India / AI Express extend Jeddah flight suspensions to 24 Nov.", "SUN"),
    (38, "AUSTRALIA WIN", "Record MCG T20 chase: Australia hunt down 188 to beat England by 3 wickets with a ball to spare; Nikhil Chaudhary 66 off 38 + 2-21; Harry Brook 65 off 28; England\u2019s 7-match T20 win streak ends; 39,289 crowd.", "SAT"),
]

CHIPS = [
    ("03:00 GMT", "COP31 deadline"),
    ("16 crew", "Sparta II saved"),
    ("900,000", "AI chips for China"),
    ("109\u20130", "Greenland deal"),
    ("188", "record MCG chase"),
    ("$81.3bn", "biggest IPO ever"),
]

REGIONS = [
    ("ASIA-PACIFIC", 11, (15, 91, 77)),
    ("OCEANIA", 2, (185, 138, 29)),
    ("EUROPE", 8, (29, 53, 87)),
    ("AMERICAS", 12, (163, 31, 31)),
    ("MIDDLE EAST", 3, (90, 60, 20)),
    ("AFRICA", 1, (60, 60, 60)),
    ("GLOBAL", 1, (120, 120, 120)),
]

# (pin number, name, lon, lat, label offset dx, dy in px from true point)
PINS = [
    (1, "Antalya", 30.7, 36.9, -26, 14),
    (2, "Gulf of Finland", 25.0, 59.8, 14, -8),
    (3, "Khasab", 56.2, 26.2, 16, 12),
    (4, "Paris", 2.35, 48.85, -14, -14),
    (5, "Washington", -77.0, 38.9, -16, 12),
    (6, "Jun\u00edn", -75.9, -11.2, 14, 2),
    (7, "Shenzhen", 114.0, 22.5, 14, -4),
    (8, "New York", -74.0, 40.7, 14, -12),
    (9, "Qeshm", 55.9, 26.8, -14, -16),
    (10, "Myanmar", 96.0, 21.9, 12, 10),
    (11, "Kerch", 36.5, 45.35, 14, -14),
]

# Rough continent outlines in (lon, lat); stylised, not surveyed.
LAND_POLYS = [
    [(-168, 66), (-165, 60), (-158, 58), (-152, 60), (-140, 60), (-135, 58),
     (-130, 54), (-125, 49), (-124, 42), (-120, 34), (-114, 29), (-110, 24),
     (-105, 20), (-97, 16), (-94, 17), (-90, 14), (-86, 12), (-83, 9),
     (-80, 8), (-79, 9), (-81, 13), (-83, 15), (-86, 16), (-88, 18),
     (-90, 21), (-91, 19), (-94, 18), (-97, 16), (-97, 26), (-93, 30),
     (-89, 30), (-84, 30), (-81, 26), (-80, 32), (-76, 35), (-74, 40),
     (-70, 42), (-68, 45), (-65, 44), (-60, 47), (-55, 52), (-60, 55),
     (-64, 58), (-68, 58), (-72, 62), (-78, 62), (-85, 66), (-92, 66),
     (-95, 69), (-110, 68), (-125, 70), (-140, 70), (-155, 71), (-165, 68)],
    [(-58, 64), (-52, 60), (-43, 60), (-40, 64), (-32, 68), (-22, 70),
     (-25, 74), (-30, 76), (-45, 76), (-58, 74), (-60, 70)],
    [(-79, 9), (-77, 4), (-80, -3), (-81, -6), (-77, -12), (-72, -18),
     (-70, -23), (-70, -30), (-72, -37), (-73, -44), (-74, -50), (-70, -54),
     (-66, -55), (-65, -45), (-62, -41), (-58, -35), (-52, -32), (-48, -28),
     (-41, -23), (-39, -17), (-35, -9), (-35, -6), (-40, -3), (-44, -2),
     (-50, 0), (-53, 4), (-58, 6), (-62, 9), (-68, 11), (-72, 12),
     (-76, 10)],
    [(-17, 15), (-16, 20), (-15, 27), (-10, 31), (-5, 35), (0, 36),
     (10, 37), (11, 34), (20, 32), (30, 31), (32, 31), (35, 28), (37, 22),
     (39, 18), (43, 12), (48, 11), (51, 10), (46, 5), (41, 0), (40, -5),
     (40, -10), (36, -18), (33, -26), (28, -33), (20, -35), (17, -32),
     (15, -27), (13, -18), (12, -10), (13, -5), (9, 0), (9, 4), (-8, 5),
     (-13, 8), (-17, 12)],
    [(-10, 36), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-1, 50), (2, 51),
     (5, 53), (8, 55), (8, 57), (10, 59), (5, 60), (5, 62), (12, 65),
     (18, 69), (25, 71), (30, 70), (35, 68), (40, 68), (45, 68), (55, 69),
     (68, 73), (75, 73), (85, 75), (100, 77), (110, 74), (120, 73),
     (130, 72), (140, 72), (150, 70), (160, 70), (170, 67), (178, 65),
     (178, 62), (170, 60), (162, 56), (158, 52), (156, 50), (150, 59),
     (142, 55), (141, 50), (140, 45), (138, 42), (135, 43), (130, 42),
     (127, 40), (126, 38), (122, 38), (120, 35), (122, 31), (120, 28),
     (118, 25), (115, 23), (110, 21), (108, 18), (105, 10), (103, 8),
     (100, 7), (98, 10), (95, 15), (92, 16), (91, 22), (89, 22), (86, 20),
     (83, 18), (80, 15), (77, 8), (75, 12), (72, 20), (68, 23), (66, 25),
     (62, 25), (58, 26), (57, 24), (55, 22), (52, 20), (48, 17), (45, 14),
     (43, 12), (40, 15), (39, 20), (37, 25), (35, 28), (34, 31), (36, 36),
     (33, 36), (30, 36), (27, 37), (26, 38), (23, 36), (22, 37), (19, 40),
     (15, 44), (12, 44), (8, 44), (3, 43), (0, 40), (-2, 37), (-6, 36),
     (-9, 37)],
    [(95, 5), (100, 0), (104, -3), (106, -6), (102, -5), (97, 2)],
    [(109, 1), (113, 4), (117, 6), (119, 1), (117, -3), (112, -3)],
    [(131, -1), (136, -2), (141, -3), (146, -6), (150, -8), (146, -8),
     (141, -7), (136, -4)],
    [(130, 31), (133, 34), (136, 35), (139, 37), (141, 40), (142, 44),
     (140, 40), (137, 37), (133, 34)],
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53)],
    [(113, -22), (114, -30), (115, -35), (120, -34), (124, -33), (129, -32),
     (132, -32), (135, -35), (138, -35), (140, -38), (145, -38), (150, -37),
     (153, -32), (153, -27), (150, -22), (146, -19), (142, -15), (142, -11),
     (137, -12), (135, -15), (132, -12), (130, -13), (126, -14), (122, -17),
     (118, -20)],
    [(167, -45), (170, -42), (174, -39), (178, -38), (176, -40), (173, -42),
     (169, -46)],
    [(44, -16), (47, -15), (50, -16), (49, -20), (46, -24), (44, -25),
     (43, -21)],
]


# ---- small glyphs (line art, drawn inside a 26x14 box) -----------------
def glyph(draw, kind, x, y, col):
    if kind == "sunrise":
        draw.arc([x + 3, y + 1, x + 23, y + 15], 180, 360, fill=col, width=2)
        draw.line([x + 1, y + 12, x + 25, y + 12], fill=col, width=2)
        for dx in (5, 13, 21):
            draw.line([x + dx, y + 1, x + dx, y + 5], fill=col, width=1)
    elif kind == "shipfire":
        draw.polygon([(x + 2, y + 8), (x + 24, y + 8), (x + 21, y + 13),
                      (x + 5, y + 13)], outline=col)
        draw.rectangle([x + 9, y + 3, x + 15, y + 8], outline=col)
        draw.polygon([(x + 12, y - 1), (x + 15, y + 3), (x + 11, y + 3)],
                     fill=col)
    elif kind == "tanker":
        draw.polygon([(x + 1, y + 7), (x + 25, y + 7), (x + 23, y + 12),
                      (x + 3, y + 12)], outline=col)
        draw.rectangle([x + 4, y + 3, x + 10, y + 7], outline=col)
        draw.rectangle([x + 12, y + 3, x + 18, y + 7], outline=col)
        draw.line([x + 21, y + 1, x + 24, y + 5], fill=col, width=2)
        draw.line([x + 24, y + 1, x + 21, y + 5], fill=col, width=2)
    elif kind == "scales":
        draw.line([x + 13, y + 1, x + 13, y + 11], fill=col, width=1)
        draw.line([x + 5, y + 3, x + 21, y + 3], fill=col, width=1)
        draw.arc([x + 2, y + 3, x + 8, y + 10], 0, 180, fill=col, width=1)
        draw.arc([x + 18, y + 3, x + 24, y + 10], 0, 180, fill=col, width=1)
        draw.line([x + 9, y + 12, x + 17, y + 12], fill=col, width=1)
    elif kind == "chip":
        draw.rectangle([x + 6, y + 2, x + 20, y + 12], outline=col)
        for px in (9, 13, 17):
            draw.line([x + px, y + 2, x + px, y + 12], fill=col, width=1)
        draw.line([x + 6, y + 7, x + 20, y + 7], fill=col, width=1)
    elif kind == "quake":
        pts = [(x + 1, y + 7), (x + 5, y + 7), (x + 7, y + 2), (x + 10, y + 12),
               (x + 13, y + 4), (x + 16, y + 10), (x + 19, y + 7), (x + 25, y + 7)]
        draw.line(pts, fill=col, width=1, joint="curve")
    elif kind == "dove":
        draw.arc([x + 4, y + 3, x + 18, y + 13], 200, 340, fill=col, width=2)
        draw.line([x + 18, y + 6, x + 25, y + 3], fill=col, width=1)
        draw.line([x + 6, y + 5, x + 11, y + 2], fill=col, width=1)
    elif kind == "chart":
        draw.line([(x + 2, y + 3), (x + 9, y + 6), (x + 14, y + 5),
                   (x + 24, y + 12)], fill=col, width=2, joint="curve")
        draw.line([x + 24, y + 12, x + 24, y + 8], fill=col, width=1)
        draw.line([x + 24, y + 12, x + 20, y + 12], fill=col, width=1)
    elif kind == "flame":
        draw.polygon([(x + 13, y + 1), (x + 18, y + 7), (x + 16, y + 12),
                      (x + 9, y + 12), (x + 8, y + 7)], outline=col)
    elif kind == "gavel":
        draw.line([x + 5, y + 11, x + 21, y + 2], fill=col, width=2)
        draw.rectangle([x + 14, y + 1, x + 22, y + 6], outline=col)
        draw.line([x + 4, y + 12, x + 12, y + 12], fill=col, width=1)
    elif kind == "bridge":
        draw.arc([x + 2, y + 4, x + 24, y + 16], 180, 360, fill=col, width=2)
        draw.line([x + 2, y + 11, x + 24, y + 11], fill=col, width=1)
        draw.line([x + 6, y + 6, x + 6, y + 11], fill=col, width=1)
        draw.line([x + 20, y + 6, x + 20, y + 11], fill=col, width=1)


# ---- sections -----------------------------------------------------------
def build():
    img = Image.new("RGB", (PAGE_W, PAGE_H), PAPER)
    d = ImageDraw.Draw(img)
    y = 12

    # masthead row
    d.text((MARGIN, y), "THE DAWN LEDGER", font=F_MAST, fill=INK)
    tr = "ONE DAY  \u00b7  ONE PAGE  \u00b7  38 STORIES"
    d.text((PAGE_W - MARGIN - d.textlength(tr, font=F_TOPRIGHT), y),
           tr, font=F_TOPRIGHT, fill=RED)
    y += 20

    # dateline headline
    d.text((MARGIN, y), "Sunday 22 November 2026", font=F_TITLE, fill=NAVY)
    y += 58

    # standfirst
    sub = ("COP31 nears a dawn deal  \u00b7  Sparta II ablaze in the Gulf of Finland  "
           "\u00b7  Two tankers hit off Oman")
    d.text((MARGIN, y), sub, font=F_SUB, fill=(60, 58, 50))
    y += 20
    d.line([MARGIN, y, PAGE_W - MARGIN, y], fill=INK, width=2)
    y += 6

    # stat chips
    chip_w = (CONTENT_W - 5 * 8) // 6
    for i, (val, lab) in enumerate(CHIPS):
        x0 = MARGIN + i * (chip_w + 8)
        d.rounded_rectangle([x0, y, x0 + chip_w, y + 28], radius=5,
                            fill=CHIP_BG, outline=EDGE, width=1)
        vw = d.textlength(val, font=F_CHIP_V)
        lw = d.textlength(lab, font=F_CHIP_L)
        total = vw + 5 + lw
        tx = x0 + max(4, (chip_w - total) // 2)
        d.text((tx, y + 7), val, font=F_CHIP_V, fill=RED)
        d.text((tx + vw + 5, y + 8), lab, font=F_CHIP_L, fill=INK)
    y += 34

    # region bar
    rx = MARGIN
    for name, count, col in REGIONS:
        d.ellipse([rx, y + 2, rx + 9, y + 11], fill=col)
        label = "%s %d" % (name, count)
        d.text((rx + 13, y), label, font=F_REGION, fill=INK)
        rx += 13 + d.textlength(label, font=F_REGION) + 18
    y += 20

    # ---- hero cards ----
    hero_w = (CONTENT_W - 2 * 10) // 3
    hero_h = 184
    hy = y
    for i, h in enumerate(HEROES):
        x0 = MARGIN + i * (hero_w + 10)
        d.rounded_rectangle([x0, hy, x0 + hero_w, hy + hero_h], radius=6,
                            fill=CARD, outline=EDGE, width=1)
        # coloured header band
        d.rounded_rectangle([x0, hy, x0 + hero_w, hy + 30], radius=6,
                            fill=h["color"])
        d.rectangle([x0, hy + 20, x0 + hero_w, hy + 30], fill=h["color"])
        d.rectangle([x0, hy, x0 + 8, hy + 30], fill=h["color"])
        d.rectangle([x0 + hero_w - 8, hy, x0 + hero_w, hy + 30], fill=h["color"])
        num_badge(d, x0 + 8, hy + 6, h["num"], 18)
        d.text((x0 + 32, hy + 8), h["kick"], font=F_HERO_KICK,
               fill=(255, 255, 255))
        glyph(d, h["art"], x0 + hero_w - 78, hy + 8, (255, 255, 255))
        day_tag(d, x0 + hero_w - 46, hy + 8, h["tag"], (255, 255, 255))
        # headline
        hx, hw = x0 + 12, hero_w - 24
        head_lines = wrap_text(d, h["head"], F_HERO_HEAD, hw)
        if len(head_lines) > 3:
            note("hero %d headline %d lines" % (h["num"], len(head_lines)))
        cy = draw_wrapped(d, hx, hy + 40, head_lines[:3], F_HERO_HEAD, INK, 20)
        # body
        body_lines = wrap_text(d, h["body"], F_HERO_BODY, hw)
        max_body = int((hy + hero_h - 18 - cy) // 10.5)
        if len(body_lines) > max_body:
            note("hero %d body %d lines > %d" % (h["num"], len(body_lines), max_body))
        draw_wrapped(d, hx, cy + 4, body_lines[:max_body], F_HERO_BODY,
                     (52, 50, 44), 10.5)
        d.text((hx, hy + hero_h - 16), h["src"], font=F_HERO_SRC, fill=MUTED)
    y = hy + hero_h + 8

    # ---- small cards: 4 x 2 (no glyphs: long kickers leave no room) ----
    sm_w = (CONTENT_W - 3 * 8) // 4
    sm_h = 120
    for row in range(2):
        for col in range(4):
            s = SMALLS[row * 4 + col]
            x0 = MARGIN + col * (sm_w + 8)
            y0 = y + row * (sm_h + 8)
            d.rounded_rectangle([x0, y0, x0 + sm_w, y0 + sm_h], radius=5,
                                fill=CARD, outline=EDGE, width=1)
            d.rectangle([x0, y0 + 4, x0 + 4, y0 + sm_h - 4], fill=TEAL)
            num_badge(d, x0 + 9, y0 + 7, s["num"], 16)
            d.text((x0 + 29, y0 + 9), s["kick"], font=F_SM_KICK, fill=TEAL)
            day_tag(d, x0 + sm_w - 40, y0 + 8, s["tag"])
            hx, hw = x0 + 10, sm_w - 20
            hl = wrap_text(d, s["head"], F_SM_HEAD, hw)
            if len(hl) > 2:
                note("small %d headline %d lines" % (s["num"], len(hl)))
            cy = draw_wrapped(d, hx, y0 + 26, hl[:2], F_SM_HEAD, INK, 14)
            # adaptive body type: shrink until it fits above the source line
            picked = None
            for fsize, lead in ((9, 11), (8.5, 10), (8, 9.5)):
                fnt = load("DejaVuSans.ttf", fsize)
                bl = wrap_text(d, s["body"], fnt, hw)
                room = int((y0 + sm_h - 14 - cy) // lead)
                if len(bl) <= room:
                    picked = (fnt, bl, lead, room)
                    break
            if picked is None:
                note("small %d body %d lines > %d even at 8pt"
                     % (s["num"], len(bl), room))
                picked = (fnt, bl, lead, room)
            fnt, bl, lead, room = picked
            draw_wrapped(d, hx, cy + 2, bl[:room], fnt, (52, 50, 44), lead)
            d.text((hx, y0 + sm_h - 13), s["src"], font=F_SM_SRC, fill=MUTED)
    y = y + 2 * sm_h + 8 + 8

    # ---- map + list row ----
    row_y = y
    row_h = 320
    map_x, map_w = MARGIN, 360
    list_x, list_w = MARGIN + map_w + 8, CONTENT_W - map_w - 8

    # map panel
    d.rounded_rectangle([map_x, row_y, map_x + map_w, row_y + row_h], radius=6,
                        fill=CARD, outline=EDGE, width=1)
    d.text((map_x + 12, row_y + 8), "WHERE IT HAPPENED", font=F_SEC, fill=NAVY)
    d.text((map_x + 12, row_y + 26),
           "Numbered pins mark the dateline of each story.",
           font=F_SEC_SUB, fill=MUTED)
    mx0, my0 = map_x + 10, row_y + 46
    mx1, my1 = map_x + map_w - 10, row_y + 236
    d.rectangle([mx0, my0, mx1, my1], fill=SEA, outline=EDGE)
    lon0, lon1, lat0, lat1 = -170.0, 190.0, -58.0, 84.0

    def proj(lon, lat):
        px = mx0 + (lon - lon0) / (lon1 - lon0) * (mx1 - mx0)
        py = my0 + (lat1 - lat) / (lat1 - lat0) * (my1 - my0)
        return px, py

    # graticule
    for lon in range(-150, 181, 30):
        gx, _ = proj(lon, 0)
        d.line([gx, my0, gx, my1], fill=(200, 214, 219), width=1)
    for lat in (-40, -20, 0, 20, 40, 60):
        _, gy = proj(0, lat)
        d.line([mx0, gy, mx1, gy], fill=(200, 214, 219), width=1)
    for poly in LAND_POLYS:
        pts = [proj(lon, lat) for lon, lat in poly]
        d.polygon(pts, fill=LAND, outline=LAND_EDGE)
    # pins
    for num, name, lon, lat, dx, dy in PINS:
        px, py = proj(lon, lat)
        d.ellipse([px - 2, py - 2, px + 2, py + 2], fill=PIN)
        bx, by = px + dx, py + dy
        if dx or dy:
            d.line([px, py, bx, by], fill=PIN, width=1)
        d.ellipse([bx - 8, by - 8, bx + 8, by + 8], fill=PIN,
                  outline=(255, 255, 255), width=1)
        t = str(num)
        tw = d.textlength(t, font=F_TAG)
        d.text((bx - tw / 2, by - 4), t, font=F_TAG, fill=(255, 255, 255))
    cap = ("Pins: 1 Antalya \u00b7 2 Gulf of Finland \u00b7 3 Khasab \u00b7 4 Paris \u00b7 "
           "5 Washington \u00b7 6 Jun\u00edn \u00b7 7 Shenzhen \u00b7 8 New York \u00b7 "
           "9 Qeshm \u00b7 10 Myanmar \u00b7 11 Kerch")
    cap_lines = wrap_text(d, cap, F_MAPCAP, map_w - 24)
    draw_wrapped(d, map_x + 12, row_y + 242, cap_lines, F_MAPCAP, MUTED, 12)

    # list panel
    d.rounded_rectangle([list_x, row_y, list_x + list_w, row_y + row_h],
                        radius=6, fill=CARD, outline=EDGE, width=1)
    d.text((list_x + 12, row_y + 8), "ALSO IN THE LEDGER \u2014 27 MORE STORIES",
           font=F_SEC, fill=NAVY)
    d.text((list_x + 12, row_y + 26),
           "Numbered 12\u201338 \u00b7 tags show the day each story broke.",
           font=F_SEC_SUB, fill=MUTED)
    # adaptive list type size: shrink until it fits
    avail_h = row_y + row_h - (row_y + 46)
    lx = list_x + 12
    lw = list_w - 24
    chosen = None
    for fsize, lead in ((9.5, 11.0), (9.0, 10.4), (8.5, 9.3)):
        f_body = load("DejaVuSans.ttf", fsize)
        f_bold = load("DejaVuSans-Bold.ttf", fsize)
        f_num = load("DejaVuSans-Bold.ttf", fsize)
        total = 0
        rendered = []
        for num, lead_txt, text, tag in MORE:
            prefix = "%d. " % num
            if lead_txt:
                full = prefix + lead_txt + " \u2014 " + text + " (" + tag + ")"
            else:
                full = prefix + text + " (" + tag + ")"
            lines = wrap_text(d, full, f_body, lw)
            rendered.append((num, lead_txt, text, tag, lines))
            total += len(lines) * lead
        if total <= avail_h:
            chosen = (fsize, lead, f_body, f_bold, f_num, rendered)
            break
    if chosen is None:
        note("list does not fit even at 8.5pt (%d px needed)" % total)
        chosen = (8.5, 9.3, f_body, f_bold, f_num, rendered)
    fsize, lead, f_body, f_bold, f_num, rendered = chosen
    print("list type: %.1fpt leading %.1f" % (fsize, lead))
    cy = row_y + 46
    for num, lead_txt, text, tag, lines in rendered:
        for li, ln in enumerate(lines):
            if li == 0 and lead_txt:
                prefix = "%d. %s \u2014 " % (num, lead_txt)
                pw = d.textlength(prefix, font=f_bold)
                d.text((lx, cy), prefix, font=f_bold, fill=RED)
                d.text((lx + pw, cy), ln[len(prefix):], font=f_body, fill=INK)
            elif li == 0:
                prefix = "%d. " % num
                pw = d.textlength(prefix, font=f_num)
                d.text((lx, cy), prefix, font=f_num, fill=RED)
                d.text((lx + pw, cy), ln[len(prefix):], font=f_body, fill=INK)
            else:
                d.text((lx, cy), ln, font=f_body, fill=INK)
            cy += lead
    if cy > row_y + row_h - 4:
        note("list overflow by %d px" % (cy - (row_y + row_h - 4)))
    y = row_y + row_h + 8

    # ---- date check box ----
    d.rounded_rectangle([MARGIN, y, PAGE_W - MARGIN, y + 42], radius=6,
                        outline=RED, width=1, fill=(255, 247, 240))
    d.text((MARGIN + 10, y + 5),
           "DATE CHECK \u2014 SUN = Sunday 22 Nov \u00b7 SAT = Saturday 21 Nov \u00b7 "
           "FRI = Friday 20 Nov \u00b7 WED = Wednesday 19 Nov",
           font=F_DATE, fill=RED)
    d.text((MARGIN + 10, y + 22),
           "WEEK = earlier in the week, first reported or confirmed this week. "
           "A story counts here only if it happened, or was first reported, on its tagged day.",
           font=F_DATE_BODY, fill=INK)
    y += 48

    # ---- footer (two lines) ----
    d.text((MARGIN, y),
           "Every story here happened, or was first reported, on its tagged day. "
           "Sources are named beside each story.",
           font=F_FOOT_B, fill=INK)
    y += 13
    d.text((MARGIN, y),
           "Sources: AP, Reuters, BBC, USGS, AAP, AFP, ICJ, UKMTO, GFZ \u2014 checked 22 Nov 2026.   "
           "THE DAWN LEDGER \u00b7 38 STORIES \u00b7 7 REGIONS \u00b7 DRAWN 22 NOVEMBER 2026",
           font=F_FOOT, fill=MUTED)
    print("bottom y=%d (page %d)" % (y, PAGE_H))
    if y > PAGE_H - 8:
        note("footer overflows page bottom")

    img.save(OUT, format="PNG")
    data = open(OUT, "rb").read()
    print("entry.png: %d bytes sha256=%s" %
          (len(data), hashlib.sha256(data).hexdigest()))
    print("warnings: %d" % len(warnings))
    return len(warnings) == 0


if __name__ == "__main__":
    ok = build()
    sys.exit(0 if ok else 1)
