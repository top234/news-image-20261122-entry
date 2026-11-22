#!/usr/bin/env python3
"""The Sunday Ledger — one-page newspaper for Sunday 22 November 2026.

Draws entry.png (1024x1024) with Pillow. Fully deterministic: fixed
geometry, no network, no external assets, no randomness at all. Fonts
come from the system DejaVu set only.

Layout, top to bottom: nameplate strip, big serif dateline, standfirst,
six stat chips, region tally, three hero cards, eight small cards, a
world map with numbered pins beside a numbered list of 27 more stories,
a DATE CHECK explainer box, and a source footer.

Every story below was verified against AP / Reuters / BBC / USGS / AAP /
AFP before drawing; numbers and facts are used exactly as given.
Day tags: SUN = Sunday 22 Nov, SAT = Saturday 21 Nov, FRI = Friday
20 Nov, WED = Wednesday 19 Nov, WEEK = earlier in the week, first
reported or confirmed this week.
"""

import hashlib
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------- palette
PAPER = (248, 244, 233)   # warm newsprint
INK = (27, 42, 65)        # headline ink
SOFT = (58, 68, 84)       # softer ink for body copy
GREY = (110, 112, 108)    # captions, rules
RED = (178, 52, 40)       # accent red (numbers, warnings)
TEAL = (23, 107, 92)      # accent teal
GOLD = (169, 123, 31)     # accent gold
NAVY = (31, 58, 95)       # accent navy
CARD = (255, 255, 255)    # card faces
LINEC = (203, 196, 178)   # hairline rules on paper
MAPSEA = (214, 226, 232)  # map ocean
MAPLAND = (222, 226, 200) # map land
MAPGRID = (190, 205, 212) # map graticule

W, H = 1024, 1024
MARGIN = 26
CW = W - 2 * MARGIN  # 972 content width

FONTDIR = Path("/usr/share/fonts/truetype/dejavu")


def font(size, bold=False, serif=False, italic=False):
    """Pick a DejaVu face; sizes are rounded to whole points."""
    size = int(round(size))
    if serif:
        name = "DejaVuSerif-Bold.ttf" if bold else "DejaVuSerif.ttf"
    elif bold:
        name = "DejaVuSans-Bold.ttf"
    else:
        # No oblique face ships in this DejaVu set; italic falls back
        # to the regular face rather than failing the render.
        name = "DejaVuSans.ttf"
    return ImageFont.truetype(str(FONTDIR / name), size)


# ------------------------------------------------------------------- data
# Stat chips under the dateline: (big figure, small label).
CHIPS = [
    ("\u221210.4%", "Nasdaq week"),
    ("$81.3bn", "Anthropic IPO"),
    ("6.7", "Peru quake"),
    ("109\u20130", "Greenland deal"),
    ("188", "MCG record chase"),
    ("$3,518.50", "gold / oz"),
]

# Region tally: (label, count, dot colour).
REGIONS = [
    ("ASIA-PACIFIC", 12, TEAL),
    ("OCEANIA", 2, NAVY),
    ("EUROPE", 7, GOLD),
    ("AMERICAS", 10, RED),
    ("MIDDLE EAST", 2, INK),
    ("AFRICA", 1, SOFT),
    ("GLOBAL", 4, GREY),
]

# Hero stories. "art" picks the little white pictogram in the band.
HEROES = [
    dict(
        num=1, tag="WEEK", kicker="SHENZHEN \u00b7 PEACE DEAL",
        band=TEAL, art="branch",
        head="Trump, Xi and Putin sign a four-point peace declaration",
        body=("Signed in Shenzhen by Trump, Xi and Putin \u2014 a four-point "
              "declaration that says nothing about Ukraine."),
        src="SOURCE: AP \u00b7 REUTERS",
    ),
    dict(
        num=2, tag="FRI", kicker="MARKETS \u00b7 FRIDAY ROUT",
        band=NAVY, art="chart",
        head="Nasdaq suffers its worst week since 2020, down 10.4%",
        body=("S&P 500 falls into correction; Dow drops 1,101 to 49,097, "
              "first close below 50,000 since June. Nvidia \u221214% under "
              "SEC probe; gold \u22122.8% to $3,518.50/oz."),
        src="SOURCE: AP \u00b7 REUTERS",
    ),
    dict(
        num=3, tag="WED", kicker="GULF WAR \u00b7 WIDENS",
        band=RED, art="ship",
        head="Iran drones hit a US air base in Kuwait and sites in Bahrain",
        body=("US jets had struck an IRGC missile site on Qeshm Island the "
              "day before. An ADNOC-linked tanker was hit in Hormuz: "
              "1 crew missing, 11 hurt."),
        src="SOURCE: AP \u00b7 REUTERS",
    ),
]

# Small cards. Bodies are kept to two short lines each.
SMALLS = [
    dict(num=4, tag="WEEK", kicker="GENOCIDE RULING", accent=TEAL,
         icon="scales",
         head="World Court: Myanmar committed genocide",
         body=("First time any court has found a state guilty of genocide "
               "\u2014 against the Rohingya."),
         src="ICJ"),
    dict(num=5, tag="WEEK", kicker="GREENLAND", accent=NAVY, icon="flag",
         head="Denmark votes 109\u20130 for new US security deal",
         body="Ratified unanimously; two new American bases.",
         src="AP \u00b7 REUTERS"),
    dict(num=6, tag="FRI", kicker="ESTONIA", accent=RED, icon="fence",
         head="Estonia to shut all 5 Russia border crossings",
         body=("From 1 Dec for 6 months, after a GRU-linked arson at "
               "drone-maker Threod Systems."),
         src="REUTERS"),
    dict(num=7, tag="SAT", kicker="QUAKE \u00b7 PERU", accent=GOLD,
         icon="quake",
         head="M6.7 quake shakes Peru\u2019s Andes",
         body=("34 km north of Jun\u00edn, 108 km deep, 19:09 local; felt in "
               "Lima. No casualties or damage."),
         src="USGS \u00b7 AP"),
    dict(num=8, tag="SUN", kicker="COP31 \u00b7 ANTALYA", accent=TEAL,
         icon="globe",
         head="Climate talks go into overtime, deadlocked",
         body=("Nearly 200 nations stuck on fossil fuels; AI pledge fails "
               "to draw major US tech firms."),
         src="AP \u00b7 REUTERS"),
    dict(num=9, tag="SAT", kicker="KERCH BRIDGE", accent=NAVY, icon="bridge",
         head="Ukraine hits the Crimea bridge a third time",
         body=("Third strike in four days; Zelensky calls it a \u201cfair "
               "response\u201d. Berlin talks under way."),
         src="AP \u00b7 REUTERS"),
    dict(num=10, tag="FRI", kicker="ANTHROPIC IPO", accent=RED, icon="chip",
         head="Anthropic IPO: $81.3bn, the biggest ever",
         body="Shares +39% on debut, then fall the next day.",
         src="REUTERS"),
    dict(num=11, tag="SAT", kicker="CRICKET \u00b7 MCG", accent=GOLD,
         icon="bat",
         head="Record MCG chase: Australia hunt down 188",
         body=("Beat England by 3 wickets with a ball to spare; Chaudhary "
               "66 off 38; Brook 65 off 28."),
         src="AAP"),
]

# The numbered list, stories 12-38. Each line is one story; the tag in
# brackets is its day tag. Wording is trimmed only to fit one line.
LISTED = [
    (12, "North Korea expanding Yongbyon uranium enrichment plant, IAEA says.", "WEEK"),
    (13, "Bangladesh violence flares ahead of Sheikh Hasina\u2019s planned return.", "WEEK"),
    (14, "US signs new military deal with Venezuela, 10 months after Maduro\u2019s removal.", "WEEK"),
    (15, "Poland: two Russian missiles and a drone land in rural Poland; PM Tusk responds.", "FRI"),
    (16, "Denmark accuses Russia of plotting to kill a US-Ukrainian rapper near Copenhagen.", "FRI"),
    (17, "Russian merchant ship catches fire in the Gulf of Finland, likely hit by drones (Yle).", "SAT"),
    (18, "FBI investigating apparent hack of its criminal database.", "FRI"),
    (19, "Mexican army captures cartel kingpin Fausto Isidro Meza Flores, \u201cEl Chapo Isidro\u201d.", "WEEK"),
    (20, "Pentagon memo tells US troops to curb informal gatherings with Canadian counterparts.", "WEEK"),
    (21, "Trump threatens a \u201ctremendous tax\u201d on US firms building AI data centres overseas.", "FRI"),
    (22, "Zscaler jumps 18% on report CrowdStrike is in talks to buy it.", "SAT"),
    (23, "India: Modi inaugurates Nitish Setu, linking Patna and Vaishali.", "SUN"),
    (24, "Cyclone Akvan: 14 flights cancelled at Ranchi airport.", "SUN"),
    (25, "India face New Zealand in the 1st Test in windy Wellington.", "SUN"),
    (26, "Sensex ends a two-day rally on profit booking and US Fed rate worries.", "SUN"),
    (27, "Pat Cummins keeps Australia\u2019s Test captaincy with unanimous support.", "SUN"),
    (28, "Snooker: Advani and Ramachandran win opening group matches at the World Championship.", "SUN"),
    (29, "Chess: Erigaisi and Praggnanandhaa win; Vaishali loses on classification day one.", "SUN"),
    (30, "South Africa local elections: ANC fights to keep control of the cities.", "SUN"),
    (31, "Mamdani reveals plan to close New York\u2019s Rikers Island jail.", "WEEK"),
    (32, "Nepal PM Balendra Shah to meet Modi on his first bilateral visit.", "SUN"),
    (33, "Italian boy, 11, writes to NASA with an idea to save the Hubble telescope.", "WEEK"),
    (34, "US Forest Service releases its 1982 file on alleged Bigfoot footprints.", "WEEK"),
    (35, "Trafalgar Square\u2019s Christmas tree sets off from Oslo for London.", "SAT"),
    (36, "Man guilty of starting the Palisades fire, one of California\u2019s deadliest blazes.", "FRI"),
    (37, "Air India / AI Express extend Jeddah flight suspensions to 24 Nov.", "SUN"),
    (38, "ICMR completes 100 technology transfers at its health research summit.", "SUN"),
]

# Map pins: (number, label, lon, lat, optional offset lon/lat for the
# drawn pin when the true spot crowds a neighbour; the leader line
# points back to the true spot).
PINS = [
    (1, "Shenzhen", 114.1, 22.5, None),
    (2, "New York", -74.0, 40.7, None),
    (3, "Qeshm", 56.3, 26.9, None),
    (4, "Myanmar", 96.2, 21.9, (86.0, 8.0)),
    (5, "Greenland", -42.0, 72.0, None),
    (6, "Tallinn", 24.7, 59.4, None),
    (7, "Jun\u00edn", -75.2, -11.2, None),
    (8, "Antalya", 30.7, 36.9, None),
    (9, "Kerch", 36.4, 45.3, (45.0, 54.0)),
    (10, "San Francisco", -122.4, 37.8, None),
    (11, "Melbourne", 145.0, -37.8, None),
]

# Rough continent outlines (lon, lat) — deliberately coarse, drawn only
# to read as a world map behind the pins.
CONTINENTS = [
    # North America
    [(-168, 66), (-150, 70), (-135, 69), (-125, 71), (-110, 68), (-95, 69),
     (-85, 66), (-80, 73), (-68, 66), (-60, 60), (-55, 52), (-60, 47),
     (-65, 44), (-70, 42), (-75, 36), (-80, 32), (-81, 26), (-84, 30),
     (-90, 21), (-94, 18), (-97, 16), (-92, 15), (-86, 13), (-83, 9),
     (-80, 8), (-77, 7), (-80, 10), (-85, 12), (-90, 14), (-95, 16),
     (-100, 18), (-105, 20), (-110, 23), (-114, 28), (-117, 33),
     (-122, 37), (-124, 42), (-124, 48), (-130, 55), (-140, 60),
     (-152, 58), (-162, 58), (-168, 66)],
    # Greenland
    [(-58, 64), (-52, 60), (-43, 60), (-32, 68), (-22, 70), (-25, 76),
     (-40, 80), (-58, 76), (-62, 74), (-58, 64)],
    # South America
    [(-79, 9), (-77, 7), (-72, 11), (-64, 10), (-60, 8), (-52, 5),
     (-50, 0), (-44, -3), (-35, -8), (-38, -15), (-40, -22), (-48, -28),
     (-53, -33), (-58, -38), (-62, -41), (-65, -45), (-68, -50),
     (-70, -54), (-73, -50), (-73, -40), (-72, -30), (-70, -20),
     (-75, -15), (-80, -6), (-81, -1), (-80, 4), (-79, 9)],
    # Europe
    [(-9, 37), (-9, 43), (-2, 44), (-1, 46), (-4, 48), (-1, 50),
     (2, 51), (4, 53), (7, 54), (8, 57), (10, 59), (12, 56),
     (18, 56), (21, 55), (24, 58), (28, 60), (30, 62), (30, 66),
     (28, 70), (20, 70), (14, 67), (12, 64), (10, 62), (6, 58),
     (5, 60), (0, 59), (-3, 58), (-6, 56), (-10, 54), (-10, 50),
     (-9, 43), (-9, 37)],
    # Africa
    [(-6, 35), (0, 36), (10, 37), (12, 34), (20, 32), (25, 32),
     (32, 31), (34, 28), (37, 22), (39, 18), (43, 12), (48, 11),
     (51, 10), (51, 2), (46, -2), (40, -8), (39, -15), (36, -18),
     (33, -26), (29, -30), (26, -34), (20, -35), (16, -28), (12, -18),
     (13, -10), (9, -1), (9, 4), (4, 6), (-4, 5), (-8, 4), (-13, 8),
     (-17, 12), (-17, 15), (-16, 20), (-15, 27), (-10, 31), (-6, 35)],
    # Asia
    [(30, 36), (33, 36), (36, 36), (39, 39), (42, 41), (44, 39),
     (48, 38), (50, 37), (54, 37), (57, 27), (60, 25), (62, 25),
     (66, 25), (70, 22), (73, 20), (76, 15), (77, 8), (80, 7),
     (80, 10), (84, 18), (88, 22), (91, 22), (93, 17), (95, 16),
     (98, 16), (100, 13), (100, 8), (103, 2), (104, 2), (103, 7),
     (105, 9), (107, 11), (109, 13), (109, 17), (107, 20), (105, 20),
     (102, 23), (100, 24), (98, 28), (95, 29), (92, 21), (89, 22),
     (86, 20), (82, 17), (79, 15), (76, 10), (74, 14), (72, 20),
     (68, 23), (64, 25), (60, 25), (57, 26), (54, 27), (52, 28),
     (50, 30), (48, 30), (46, 30), (44, 29), (42, 30), (40, 31),
     (38, 32), (36, 33), (34, 31), (33, 35), (30, 36)],
    # South-East Asian islands (rough blob)
    [(95, 5), (98, 6), (100, 5), (102, 2), (104, 1), (106, -2),
     (110, -4), (114, -4), (116, -6), (119, -8), (122, -8), (124, -10),
     (128, -6), (130, -2), (132, 0), (130, 2), (126, 2), (122, 4),
     (118, 2), (114, 4), (110, 2), (106, 2), (102, 5), (98, 6), (95, 5)],
    # Australia
    [(114, -22), (114, -30), (115, -34), (118, -35), (124, -33),
     (129, -32), (132, -32), (136, -35), (138, -35), (140, -38),
     (145, -38), (150, -37), (153, -32), (153, -27), (152, -24),
     (150, -22), (146, -19), (142, -11), (141, -13), (137, -12),
     (135, -12), (132, -11), (130, -13), (126, -14), (122, -17),
     (118, -20), (114, -22)],
    # Japan
    [(130, 31), (132, 33), (134, 34), (137, 35), (139, 35), (140, 38),
     (141, 41), (142, 44), (140, 44), (138, 39), (136, 37), (133, 35),
     (131, 33), (130, 31)],
    # Britain
    [(-5, 50), (-3, 53), (-5, 56), (-3, 58), (-1, 57), (0, 53),
     (1, 51), (-2, 50), (-5, 50)],
]

# ---------------------------------------------------------------- helpers
FIT_NOTES = []  # overflow warnings collected while drawing


def text_w(draw, s, fnt):
    return draw.textlength(s, font=fnt)


def wrap(draw, text, fnt, width, max_lines=None):
    """Greedy word wrap; returns (lines, clipped?) where clipped is True
    when max_lines forced words off."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if text_w(draw, trial, fnt) <= width or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    clipped = False
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        clipped = True
    return lines, clipped


def draw_lines(draw, x, y, lines, fnt, fill, leading):
    for i, line in enumerate(lines):
        draw.text((x, y + i * leading), line, font=fnt, fill=fill)
    return y + len(lines) * leading


def hairline(draw, x0, y, x1, colour=LINEC, width=1):
    draw.line([(x0, y), (x1, y)], fill=colour, width=width)


def num_disc(draw, cx, cy, n, r=11, fill=RED):
    """Red numbered disc used for hero / small cards and map pins."""
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill,
                 outline=(255, 255, 255), width=1)
    label = str(n)
    fnt = font(10 if n < 10 else 9, bold=True)
    tw = text_w(draw, label, fnt)
    th = fnt.getbbox(label)[3]
    draw.text((cx - tw / 2, cy - th / 2 - 1), label, font=fnt,
              fill=(255, 255, 255))


# ------------------------------------------------------------- pictograms
def hero_art(draw, kind, x, y, w, h, colour=(255, 255, 255)):
    """Small white line drawing in the hero band, top-right corner."""
    if kind == "branch":  # olive branch: diagonal stem, pointed leaves
        draw.line([(x, y + h - 4), (x + w, y + 2)], fill=colour, width=2)
        for i in range(3):
            lx = x + 12 + i * (w - 24) / 2
            ly = y + h - 8 - i * (h - 14) / 2
            # one filled leaf above the stem, one below, sharing the point
            draw.polygon([(lx - 8, ly - 3), (lx, ly - 8), (lx + 8, ly - 3),
                          (lx, ly + 1)], fill=colour)
            draw.polygon([(lx - 8, ly + 3), (lx, ly + 8), (lx + 8, ly + 3),
                          (lx, ly - 1)], fill=colour)
    elif kind == "chart":  # candlesticks + falling trend line
        step = w / 6
        tops = [6, 10, 4, 12, 16, 20]
        for i, t in enumerate(tops):
            bx = x + i * step + 3
            draw.line([(bx + 3, y + t - 4), (bx + 3, y + t + 12)],
                      fill=colour, width=1)
            draw.rectangle([bx, y + t, bx + 6, y + t + 8],
                           outline=colour, width=1)
        draw.line([(x, y + 4), (x + w, y + h - 4)], fill=colour, width=2)
    elif kind == "ship":  # tanker: hull, containers, mast, waves
        draw.polygon([(x, y + 14), (x + w, y + 14), (x + w - 8, y + 24),
                      (x + 8, y + 24)], outline=colour, width=2)
        for i in range(3):
            bx = x + 8 + i * 18
            draw.rectangle([bx, y + 4, bx + 14, y + 14],
                           outline=colour, width=1)
        draw.line([(x + w - 20, y + 14), (x + w - 20, y + 2)],
                  fill=colour, width=1)
        draw.line([(x, y + h - 2), (x + w, y + h - 2)], fill=colour,
                  width=1)


def small_icon(draw, kind, x, y, colour):
    """Tiny line icon at the top-right of a small card (20x14 box)."""
    if kind == "scales":
        draw.line([(x + 10, y), (x + 10, y + 12)], fill=colour, width=1)
        draw.line([(x + 2, y + 2), (x + 18, y + 2)], fill=colour, width=1)
        draw.arc([x, y + 4, x + 6, y + 10], 0, 180, fill=colour, width=1)
        draw.arc([x + 14, y + 4, x + 20, y + 10], 0, 180, fill=colour,
                 width=1)
    elif kind == "flag":
        draw.line([(x + 3, y), (x + 3, y + 13)], fill=colour, width=1)
        draw.polygon([(x + 3, y), (x + 17, y + 3), (x + 3, y + 6)],
                     outline=colour, width=1)
    elif kind == "fence":
        for i in range(4):
            bx = x + i * 5
            draw.line([(bx, y + 12), (bx + 3, y + 2), (bx + 5, y + 12)],
                      fill=colour, width=1)
    elif kind == "quake":
        draw.line([(x, y + 7), (x + 4, y + 7), (x + 6, y + 2), (x + 8, y + 12),
                   (x + 11, y + 4), (x + 13, y + 7), (x + 20, y + 7)],
                  fill=colour, width=1)
    elif kind == "globe":
        draw.ellipse([x + 3, y, x + 17, y + 13], outline=colour, width=1)
        draw.ellipse([x + 8, y, x + 12, y + 13], outline=colour, width=1)
        draw.line([(x + 3, y + 6), (x + 17, y + 6)], fill=colour, width=1)
    elif kind == "bridge":
        draw.arc([x, y + 2, x + 20, y + 16], 180, 360, fill=colour, width=1)
        draw.line([(x, y + 12), (x + 20, y + 12)], fill=colour, width=1)
        for bx in (x + 4, x + 10, x + 16):
            draw.line([(bx, y + 6), (bx, y + 12)], fill=colour, width=1)
    elif kind == "chip":
        draw.rectangle([x + 2, y + 1, x + 18, y + 12], outline=colour,
                       width=1)
        draw.text((x + 5, y + 2), "AI", font=font(8, bold=True), fill=colour)
    elif kind == "bat":
        draw.line([(x + 4, y + 12), (x + 16, y + 1)], fill=colour, width=2)
        draw.ellipse([x + 15, y + 8, x + 20, y + 13], outline=colour,
                     width=1)


# ------------------------------------------------------------------ cards
def hero_card(draw, box, story):
    x, y, w, h = box
    draw.rounded_rectangle([x, y, x + w, y + h], radius=6, fill=CARD,
                           outline=LINEC, width=1)
    # coloured band with pictogram
    draw.rounded_rectangle([x, y, x + w, y + 36], radius=6, fill=story["band"])
    draw.rectangle([x, y + 24, x + w, y + 36], fill=story["band"])
    hero_art(draw, story["art"], x + w - 78, y + 5, 64, 26)
    num_disc(draw, x + 20, y + 36, story["num"], r=11)
    # kicker: number tag + section label
    kx = x + 36
    draw.text((kx, y + 44), story["kicker"], font=font(10.5, bold=True),
              fill=story["band"])
    tag = story["tag"]
    tf = font(9, bold=True)
    tw = text_w(draw, tag, tf)
    draw.rounded_rectangle([x + w - tw - 16, y + 42, x + w - 8, y + 58],
                           radius=4, outline=story["band"], width=1)
    draw.text((x + w - tw - 12, y + 44), tag, font=tf, fill=story["band"])
    # headline (serif bold, up to 3 lines)
    lines, clipped = wrap(draw, story["head"], font(16, bold=True, serif=True),
                          w - 24, max_lines=3)
    if clipped:
        FIT_NOTES.append(f"hero {story['num']} headline clipped")
    hy = draw_lines(draw, x + 12, y + 62, lines, font(16, bold=True, serif=True),
                    INK, 18)
    # body (up to 3 lines)
    blines, bclip = wrap(draw, story["body"], font(10.5), w - 24, max_lines=3)
    if bclip:
        FIT_NOTES.append(f"hero {story['num']} body clipped")
    by = draw_lines(draw, x + 12, hy + 4, blines, font(10.5), SOFT, 13)
    if by > y + h - 18:
        FIT_NOTES.append(f"hero {story['num']} body runs into source line")
    draw.text((x + 12, y + h - 13), story["src"], font=font(8.5, bold=True),
              fill=GREY)
    return by


def small_card(draw, box, story):
    x, y, w, h = box
    draw.rounded_rectangle([x, y, x + w, y + h], radius=5, fill=CARD,
                           outline=LINEC, width=1)
    draw.rectangle([x, y + 4, x + 4, y + h - 4], fill=story["accent"])
    num_disc(draw, x + 16, y + 14, story["num"], r=9)
    draw.text((x + 28, y + 7), story["kicker"], font=font(9.5, bold=True),
              fill=story["accent"])
    small_icon(draw, story["icon"], x + w - 26, y + 6, story["accent"])
    lines, clipped = wrap(draw, story["head"],
                          font(12, bold=True, serif=True), w - 20,
                          max_lines=2)
    if clipped:
        FIT_NOTES.append(f"small {story['num']} headline clipped")
    hy = draw_lines(draw, x + 10, y + 23, lines,
                    font(12, bold=True, serif=True), INK, 13)
    blines, bclip = wrap(draw, story["body"], font(9), w - 20, max_lines=2)
    if bclip:
        FIT_NOTES.append(f"small {story['num']} body clipped")
    by = draw_lines(draw, x + 10, hy + 3, blines, font(9), SOFT, 11)
    draw.text((x + 10, y + h - 12), story["src"], font=font(8, bold=True),
              fill=GREY)
    if by > y + h - 14:
        FIT_NOTES.append(f"small {story['num']} body runs into source line")


# -------------------------------------------------------------------- map
def project(lon, lat, box):
    """Equirectangular projection into the map box; lat clipped to
    -58..84 so Antarctica stays off the page."""
    x0, y0, w, h = box
    px = x0 + (lon + 180.0) / 360.0 * w
    lat_c = max(-58.0, min(84.0, lat))
    py = y0 + (84.0 - lat_c) / 142.0 * h
    return px, py


def draw_map(draw, box):
    x0, y0, w, h = box
    draw.rectangle([x0, y0, x0 + w, y0 + h], fill=MAPSEA,
                   outline=LINEC, width=1)
    # graticule every 30 degrees
    for lon in range(-180, 181, 30):
        gx, _ = project(lon, 0, box)
        draw.line([(gx, y0), (gx, y0 + h)], fill=MAPGRID, width=1)
    for lat in (-30, 0, 30, 60):
        _, gy = project(0, lat, box)
        draw.line([(x0, gy), (x0 + w, gy)], fill=MAPGRID, width=1)
    # continents
    for poly in CONTINENTS:
        pts = [project(lon, lat, box) for lon, lat in poly]
        draw.polygon(pts, fill=MAPLAND, outline=(180, 186, 158))
    # pins; leader-line pins are drawn at their offset spot
    for num, label, lon, lat, offset in PINS:
        tx, ty = project(lon, lat, box)
        px, py = (project(*offset, box) if offset else (tx, ty))
        if offset:
            draw.line([(tx, ty), (px, py)], fill=RED, width=1)
            draw.ellipse([tx - 2, ty - 2, tx + 2, ty + 2], fill=RED)
        num_disc(draw, px, py, num, r=9)


# ------------------------------------------------------------------ page
def build():
    img = Image.new("RGB", (W, H), PAPER)
    draw = ImageDraw.Draw(img)

    # --- nameplate strip
    draw.text((MARGIN, 12), "THE SUNDAY LEDGER", font=font(13, bold=True),
              fill=INK)
    right = "ONE DAY  \u00b7  ONE PAGE  \u00b7  38 STORIES"
    rf = font(12, bold=True)
    draw.text((W - MARGIN - text_w(draw, right, rf), 13), right, font=rf,
              fill=RED)

    # --- dateline masthead + standfirst
    mast = "Sunday 22 November 2026"
    mf = font(54, bold=True, serif=True)
    draw.text(((W - text_w(draw, mast, mf)) / 2, 30), mast, font=mf, fill=INK)
    stand = ("Shenzhen peace pact says nothing of Ukraine \u00b7 "
             "Nasdaq\u2019s worst week since 2020 \u00b7 "
             "Gulf war widens to Kuwait and Bahrain")
    sf = font(13, italic=True)
    draw.text(((W - text_w(draw, stand, sf)) / 2, 100), stand, font=sf,
              fill=SOFT)
    hairline(draw, MARGIN, 122, W - MARGIN, colour=INK, width=2)
    hairline(draw, MARGIN, 126, W - MARGIN, colour=LINEC, width=1)

    # --- stat chips
    chip_w, chip_h, gap = 157, 34, 6
    cy = 136
    for i, (value, label) in enumerate(CHIPS):
        cx = MARGIN + i * (chip_w + gap)
        draw.rounded_rectangle([cx, cy, cx + chip_w, cy + chip_h], radius=6,
                               fill=CARD, outline=LINEC, width=1)
        vf = font(15, bold=True)
        lf = font(10.5)
        vw, lw = text_w(draw, value, vf), text_w(draw, label, lf)
        total = vw + 6 + lw
        vx = cx + (chip_w - total) / 2
        draw.text((vx, cy + 9), value, font=vf, fill=RED)
        draw.text((vx + vw + 6, cy + 11), label, font=lf, fill=SOFT)

    # --- region tally, centred
    ry = 180
    parts, total_w = [], 0
    for label, count, colour in REGIONS:
        seg = f"{label} {count}"
        seg_w = 9 + 4 + text_w(draw, seg, font(11, bold=True))
        parts.append((seg, colour, seg_w))
        total_w += seg_w
    total_w += 14 * (len(parts) - 1)
    rx = (W - total_w) / 2
    for seg, colour, seg_w in parts:
        draw.ellipse([rx, ry + 3, rx + 9, ry + 12], fill=colour)
        draw.text((rx + 13, ry), seg, font=font(11, bold=True), fill=INK)
        rx += seg_w + 14

    # --- three hero cards
    hero_y, hero_h = 200, 160
    hero_w = (CW - 2 * 8) / 3
    for i, story in enumerate(HEROES):
        hx = MARGIN + i * (hero_w + 8)
        hero_card(draw, (hx, hero_y, hero_w, hero_h), story)

    # --- eight small cards, 4 per row
    small_w = (CW - 3 * 8) / 4
    small_h = 88
    for row in range(2):
        for col in range(4):
            story = SMALLS[row * 4 + col]
            sx = MARGIN + col * (small_w + 8)
            sy = 368 + row * (small_h + 8)
            small_card(draw, (sx, sy, small_w, small_h), story)

    # --- map + numbered list
    panel_y, panel_h = 560, 324
    map_w, list_w = 400, CW - 400 - 8
    draw.rounded_rectangle([MARGIN, panel_y, MARGIN + map_w, panel_y + panel_h],
                           radius=6, fill=CARD, outline=LINEC, width=1)
    draw.rounded_rectangle([MARGIN + map_w + 8, panel_y, W - MARGIN,
                            panel_y + panel_h], radius=6, fill=CARD,
                           outline=LINEC, width=1)

    # map side
    mx = MARGIN + 14
    draw.text((mx, panel_y + 10), "WHERE IT HAPPENED",
              font=font(13, bold=True), fill=INK)
    draw.text((mx, panel_y + 28), "Numbered pins mark the dateline of each story.",
              font=font(10), fill=GREY)
    draw_map(draw, (mx, panel_y + 42, map_w - 28, 220))
    legend = ("Pins: 1 Shenzhen \u00b7 2 New York \u00b7 3 Qeshm \u00b7 "
              "4 Myanmar \u00b7 5 Greenland \u00b7 6 Tallinn")
    legend2 = ("7 Jun\u00edn \u00b7 8 Antalya \u00b7 9 Kerch \u00b7 "
               "10 San Francisco \u00b7 11 Melbourne")
    draw.text((mx, panel_y + 270), legend, font=font(9.5), fill=SOFT)
    draw.text((mx, panel_y + 284), legend2, font=font(9.5), fill=SOFT)

    # list side — pick the largest size (10 down to 9) that fits every line
    lx = MARGIN + map_w + 8 + 14
    lw = list_w - 28
    draw.text((lx, panel_y + 10), "ALSO IN THE LEDGER \u2014 27 MORE STORIES",
              font=font(13, bold=True), fill=INK)
    draw.text((lx, panel_y + 28),
              "Numbered 12\u201338 \u00b7 tags show the day each story broke.",
              font=font(10), fill=GREY)
    list_size = 10.0
    while list_size > 8.5:
        lf = font(list_size)
        widest = 0
        for num, text, tag in LISTED:
            line = f"{num}. {text} ({tag})"
            widest = max(widest, text_w(draw, line, lf))
        if widest <= lw:
            break
        list_size -= 0.5
    lf = font(list_size)
    ly = panel_y + 42
    leading = 10.0
    for num, text, tag in LISTED:
        line = f"{num}. {text} ({tag})"
        draw.text((lx, ly), line, font=lf, fill=SOFT)
        ly += leading
    if ly > panel_y + panel_h - 6:
        FIT_NOTES.append("numbered list runs past panel bottom")

    # --- DATE CHECK box
    dy = 892
    draw.rounded_rectangle([MARGIN, dy, W - MARGIN, dy + 52], radius=6,
                           fill=(253, 240, 234), outline=RED, width=1)
    draw.text((MARGIN + 14, dy + 7),
              "DATE CHECK \u2014 SUN = Sunday 22 Nov \u00b7 SAT = Saturday 21 Nov "
              "\u00b7 FRI = Friday 20 Nov \u00b7 WED = Wednesday 19 Nov",
              font=font(11, bold=True), fill=RED)
    draw.text((MARGIN + 14, dy + 26),
              "WEEK = earlier in the week, first reported or confirmed this week.",
              font=font(10.5), fill=SOFT)
    draw.text((MARGIN + 14, dy + 40),
              "A story counts here only if it happened, or was first reported, "
              "on its tagged day.",
              font=font(10.5), fill=SOFT)

    # --- footer
    fy = 954
    foot = ("Every story here happened, or was first reported, on its tagged "
            "day. Sources are named beside each story.")
    ff = font(11, bold=True)
    draw.text(((W - text_w(draw, foot, ff)) / 2, fy), foot, font=ff, fill=INK)
    srcs = "Sources: AP, Reuters, BBC, USGS, AAP, AFP \u2014 checked 22 Nov 2026."
    sf2 = font(10)
    draw.text(((W - text_w(draw, srcs, sf2)) / 2, fy + 18), srcs, font=sf2,
              fill=GREY)
    tail = "THE SUNDAY LEDGER \u00b7 38 STORIES \u00b7 7 REGIONS \u00b7 DRAWN 22 NOVEMBER 2026"
    tf2 = font(10)
    draw.text(((W - text_w(draw, tail, tf2)) / 2, fy + 34), tail, font=tf2,
              fill=GREY)

    # sanity: every story accounted for
    total = len(HEROES) + len(SMALLS) + len(LISTED)
    assert total == 38, f"expected 38 stories, got {total}"
    return img


def main():
    out = Path(__file__).resolve().parent / "entry.png"
    img = build()
    img.save(out, "PNG")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    size = out.stat().st_size
    print(f"stories: {len(HEROES) + len(SMALLS) + len(LISTED)} "
          f"(heroes {len(HEROES)}, small {len(SMALLS)}, listed {len(LISTED)})")
    print(f"pins: {len(PINS)}")
    print(f"entry.png: {size} bytes, sha256 {digest}")
    if FIT_NOTES:
        print("FIT WARNINGS:")
        for note in FIT_NOTES:
            print(f"  - {note}")
        sys.exit(2)
    print("FIT OK")


if __name__ == "__main__":
    main()
