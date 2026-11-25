#!/usr/bin/env python3
"""Winner-style renderer for the make.fun daily news-image bounty.

Reads a stories JSON file and renders a 1024x1024 PNG in the layout the
top-ranked entries use (see LEARNINGS.md in the 20261122 winners folder):

  masthead with story + region counts, UTC timeline strip, 3 feature
  stories with small drawn illustrations, 10 medium stories, a numbered
  "also on" list (18) reaching 30+ stories total, a "day in numbers"
  panel, a world map with numbered pins, a date-check strip, and a
  verification label + source on every story.

All illustrations are drawn in code (PIL). No photos, no network at
render time. Output is deterministic: same JSON in -> same bytes out.

Usage:
    python3 render.py stories.json entry.png
"""

import json
import sys

from PIL import Image, ImageDraw, ImageFont

W = H = 1024
M = 14  # outer margin

SERIF_B = "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
SERIF = "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
SANS = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
SANS_B = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

PAPER = (247, 241, 222)
INK = (20, 20, 20)
NAVY = (20, 36, 61)
NAVY2 = (28, 52, 88)
RED = (178, 34, 34)
DARKRED = (140, 20, 20)
GREY = (110, 105, 95)
LIGHT_LINE = (205, 196, 172)
CARD = (255, 252, 244)

REGION_COLORS = {
    "EUROPE": (30, 80, 160),
    "MIDDLE EAST": (178, 34, 34),
    "AFRICA": (30, 120, 70),
    "ASIA": (120, 60, 150),
    "AMERICAS": (0, 130, 130),
    "OCEANIA": (200, 110, 0),
    "WORLD": (90, 90, 90),
}

LABEL_COLORS = {
    "CONFIRMED": (30, 120, 70),
    "OFFICIAL": (20, 36, 61),
    "REPORTED": (0, 110, 140),
    "CLAIM": (190, 130, 0),
    "ONGOING": (200, 90, 0),
}


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, text, f):
    box = draw.textbbox((0, 0), text, font=f)
    return box[2] - box[0]


def wrap(draw, text, f, max_w):
    """Greedy word wrap; returns a list of lines that fit max_w."""
    words = text.split()
    lines, cur = [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if text_w(draw, trial, f) <= max_w:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def fit(draw, text, f, max_w, max_lines):
    """Wrap text and truncate to max_lines with an ellipsis."""
    lines = wrap(draw, text, f, max_w)
    if len(lines) <= max_lines:
        return lines
    lines = lines[:max_lines]
    while lines and text_w(draw, lines[-1] + " …", f) > max_w:
        lines[-1] = lines[-1][:-1].rstrip()
    lines[-1] = (lines[-1] + " …").strip()
    return lines


def draw_lines(draw, x, y, lines, f, fill=INK, leading=None):
    if leading is None:
        leading = int(f.size * 1.18)
    for line in lines:
        draw.text((x, y), line, font=f, fill=fill)
        y += leading
    return y


def chip(draw, x, y, text, f, bg, fg=(255, 255, 255)):
    """Small rounded label chip; returns its right edge."""
    pad = 5
    w = text_w(draw, text, f) + pad * 2
    h = f.size + 7
    draw.rounded_rectangle([x, y, x + w, y + h], radius=3, fill=bg)
    draw.text((x + pad, y + 3), text, font=f, fill=fg)
    return x + w


def num_badge(draw, x, y, n, d=20, bg=NAVY, fg=(255, 255, 255)):
    draw.ellipse([x, y, x + d, y + d], fill=bg)
    f = font(SANS_B, 11)
    t = str(n)
    draw.text(
        (x + (d - text_w(draw, t, f)) / 2, y + 4), t, font=f, fill=fg
    )


def draw_icon(img, kind, x, y, w, h, sky):
    """Draw one flat illustration and paste it into box (x, y, w, h).

    The art is drawn at its natural size (90px tall) on a scratch canvas
    and then resized into the target box, so the same icon works in a
    320px feature band and a 190px medium band without overflowing.
    """
    if kind not in ("gavel", "drones", "radar", "ballot", "ship", "flame",
                    "trophy", "racecar", "cricket", "football", "bolt",
                    "globe", "health", "quake"):
        kind = "globe"
    tw, th = max(w, 120), 90
    canvas = Image.new("RGB", (tw, th), sky)
    draw = ImageDraw.Draw(canvas)
    cx, cy = tw / 2, th / 2
    if kind == "gavel":  # COP / talks
        # gavel head (horizontal bar) + handle + sound block
        draw.rectangle([cx - 36, cy - 18, cx + 20, cy - 4], fill=(150, 105, 55))
        draw.rectangle([cx - 40, cy - 22, cx + 24, cy - 18], fill=(120, 82, 40))
        draw.line([cx + 8, cy - 10, cx + 30, cy + 26], fill=(90, 60, 30), width=6)
        draw.rectangle([cx - 20, cy + 24, cx + 34, cy + 32], fill=(90, 60, 30))
    elif kind == "drones":  # war / drones
        for dx, dy in [(-38, -14), (0, -26), (38, -8)]:
            draw.polygon(
                [(cx + dx - 14, cy + dy), (cx + dx + 16, cy + dy - 4),
                 (cx + dx + 16, cy + dy + 4)], fill=(230, 230, 230))
        draw.polygon([(cx - 16, cy + 18), (cx, cy + 2), (cx + 16, cy + 18),
                      (cx + 6, cy + 34), (cx - 6, cy + 34)], fill=(240, 140, 40))
        draw.ellipse([cx - 4, cy + 14, cx + 4, cy + 22], fill=(255, 200, 60))
    elif kind == "radar":  # claim / radar
        draw.ellipse([cx - 30, cy - 30, cx + 30, cy + 30], outline=(230, 230, 230), width=3)
        draw.ellipse([cx - 18, cy - 18, cx + 18, cy + 18], outline=(230, 230, 230), width=2)
        draw.line([cx, cy, cx + 26, cy - 26], fill=(255, 200, 60), width=4)
        draw.ellipse([cx - 4, cy - 4, cx + 4, cy + 4], fill=(255, 200, 60))
        draw.rectangle([0, cy + 30, tw, cy + 34], fill=(90, 120, 90))
    elif kind == "ballot":  # elections
        draw.rectangle([cx - 30, cy - 26, cx + 30, cy + 26], fill=(240, 240, 240))
        draw.rectangle([cx - 30, cy - 26, cx + 30, cy - 12], fill=(30, 80, 160))
        draw.line([cx - 16, cy + 4, cx - 4, cy + 16], fill=(30, 120, 70), width=5)
        draw.line([cx - 4, cy + 16, cx + 18, cy - 12], fill=(30, 120, 70), width=5)
    elif kind == "ship":  # sea / navy
        draw.polygon([(cx - 44, cy + 6), (cx + 44, cy + 6), (cx + 30, cy + 26),
                      (cx - 30, cy + 26)], fill=(70, 70, 80))
        draw.rectangle([cx - 4, cy - 26, cx + 2, cy + 6], fill=(50, 50, 60))
        draw.polygon([(cx + 2, cy - 26), (cx + 26, cy - 8), (cx + 2, cy - 8)],
                     fill=(240, 240, 240))
        draw.rectangle([0, cy + 26, tw, cy + 34], fill=(40, 90, 140))
    elif kind == "flame":  # fire / disaster
        draw.polygon([(cx, cy - 30), (cx + 14, cy - 6), (cx + 26, cy + 8),
                      (cx + 12, cy + 28), (cx - 12, cy + 28), (cx - 26, cy + 8),
                      (cx - 14, cy - 6)], fill=(240, 140, 40))
        draw.polygon([(cx, cy - 8), (cx + 9, cy + 8), (cx, cy + 22),
                      (cx - 9, cy + 8)], fill=(255, 200, 60))
    elif kind == "trophy":  # tennis / sport titles
        draw.polygon([(cx - 12, cy - 26), (cx + 12, cy - 26), (cx + 8, cy + 2),
                      (cx - 8, cy + 2)], fill=(230, 190, 60))
        draw.arc([cx - 24, cy - 26, cx - 8, cy - 4], 90, 270, fill=(230, 190, 60), width=4)
        draw.arc([cx + 8, cy - 26, cx + 24, cy - 4], -90, 90, fill=(230, 190, 60), width=4)
        draw.rectangle([cx - 4, cy + 2, cx + 4, cy + 16], fill=(200, 160, 40))
        draw.rectangle([cx - 14, cy + 16, cx + 14, cy + 24], fill=(200, 160, 40))
    elif kind == "racecar":  # F1
        draw.polygon([(cx - 44, cy + 2), (cx - 20, cy - 12), (cx + 10, cy - 12),
                      (cx + 44, cy + 4), (cx + 44, cy + 12), (cx - 44, cy + 12)],
                     fill=(200, 30, 30))
        draw.ellipse([cx - 28, cy + 8, cx - 8, cy + 28], fill=(20, 20, 20))
        draw.ellipse([cx + 16, cy + 8, cx + 36, cy + 28], fill=(20, 20, 20))
        draw.rectangle([cx - 52, cy - 8, cx - 40, cy + 2], fill=(20, 20, 20))
    elif kind == "cricket":  # cricket
        draw.polygon([(cx - 26, cy - 28), (cx - 12, cy - 28), (cx - 2, cy + 6),
                      (cx - 16, cy + 6)], fill=(200, 170, 120))
        draw.rectangle([cx - 16, cy + 6, cx - 2, cy + 30], fill=(150, 120, 80))
        draw.ellipse([cx + 12, cy + 10, cx + 30, cy + 28], fill=(200, 30, 30))
    elif kind == "football":  # football
        draw.ellipse([cx - 26, cy - 26, cx + 26, cy + 26], fill=(245, 245, 245))
        draw.polygon([(cx, cy - 10), (cx + 10, cy - 3), (cx + 6, cy + 8),
                      (cx - 6, cy + 8), (cx - 10, cy - 3)], fill=(20, 20, 20))
        draw.ellipse([cx - 30, cy + 20, cx + 30, cy + 34], fill=(60, 140, 60))
    elif kind == "bolt":  # energy / power
        draw.polygon([(cx + 6, cy - 32), (cx - 16, cy + 2), (cx - 2, cy + 2),
                      (cx - 8, cy + 32), (cx + 16, cy - 4), (cx + 2, cy - 4)],
                     fill=(255, 200, 40))
    elif kind == "globe":  # world / diplomacy
        draw.ellipse([cx - 28, cy - 28, cx + 28, cy + 28], fill=(70, 130, 180))
        draw.ellipse([cx - 28, cy - 28, cx + 28, cy + 28], outline=(230, 230, 230), width=2)
        draw.arc([cx - 14, cy - 28, cx + 14, cy + 28], -90, 90, fill=(230, 230, 230), width=2)
        draw.line([cx - 28, cy, cx + 28, cy], fill=(230, 230, 230), width=2)
    elif kind == "health":  # health / hospitals
        draw.rectangle([cx - 26, cy - 26, cx + 26, cy + 26], fill=(240, 240, 240))
        draw.rectangle([cx - 6, cy - 18, cx + 6, cy + 18], fill=(200, 30, 30))
        draw.rectangle([cx - 18, cy - 6, cx + 18, cy + 6], fill=(200, 30, 30))
    elif kind == "quake":  # earthquake
        draw.polygon([(cx - 30, cy + 20), (cx - 10, cy - 20), (cx + 8, cy + 10),
                      (cx + 28, cy - 24)], fill=(120, 90, 60))
        draw.line([cx - 34, cy + 28, cx + 34, cy + 28], fill=(90, 70, 50), width=4)
    # Paste aspect-fit, centred on a sky-filled box, so the art is never
    # squashed or clipped when the target band is wider than it is tall.
    scale = min(w / tw, h / th)
    nw, nh = max(1, int(tw * scale)), max(1, int(th * scale))
    box = Image.new("RGB", (w, h), sky)
    box.paste(canvas.resize((nw, nh), Image.LANCZOS),
              ((w - nw) // 2, (h - nh) // 2))
    img.paste(box, (x, y))


# ---------------------------------------------------------------- map
# Crude but recognisable continent blobs (fractions of the map panel).
CONTINENTS = [
    # North America
    [(0.03, 0.28), (0.10, 0.10), (0.24, 0.08), (0.30, 0.18), (0.26, 0.30),
     (0.18, 0.42), (0.10, 0.44), (0.04, 0.38)],
    # South America
    [(0.22, 0.52), (0.30, 0.50), (0.34, 0.60), (0.30, 0.78), (0.25, 0.86),
     (0.21, 0.68)],
    # Europe
    [(0.44, 0.16), (0.52, 0.10), (0.58, 0.16), (0.56, 0.26), (0.48, 0.30),
     (0.43, 0.24)],
    # Africa
    [(0.44, 0.36), (0.56, 0.34), (0.60, 0.44), (0.56, 0.62), (0.50, 0.72),
     (0.45, 0.56)],
    # Asia
    [(0.58, 0.10), (0.72, 0.06), (0.92, 0.10), (0.96, 0.22), (0.88, 0.34),
     (0.76, 0.38), (0.66, 0.30), (0.58, 0.24)],
    # SE Asia / Indonesia
    [(0.78, 0.44), (0.86, 0.42), (0.88, 0.50), (0.80, 0.52)],
    # Australia
    [(0.82, 0.62), (0.92, 0.60), (0.96, 0.68), (0.90, 0.76), (0.82, 0.72)],
]

LAND = (168, 178, 150)
SEA = (214, 228, 232)


def draw_map(draw, x, y, w, h, pins):
    draw.rectangle([x, y, x + w, y + h], fill=SEA, outline=NAVY, width=2)
    for poly in CONTINENTS:
        pts = [(x + fx * w, y + fy * h) for fx, fy in poly]
        draw.polygon(pts, fill=LAND)
    for n, (fx, fy) in pins:
        px, py = x + fx * w, y + fy * h
        r = 9
        draw.ellipse([px - r, py - r, px + r, py + r], fill=RED,
                     outline=(255, 255, 255), width=2)
        f = font(SANS_B, 10)
        t = str(n)
        draw.text((px - text_w(draw, t, f) / 2, py - 5), t, font=f,
                  fill=(255, 255, 255))


# ---------------------------------------------------------------- render

def render(data, out_path):
    img = Image.new("RGB", (W, H), PAPER)
    d = ImageDraw.Draw(img)

    stories = data["features"] + data["medium"] + data["also"]
    n_total = len(stories)
    # Region counts are computed from each story's "region" field, so the
    # masthead can never disagree with the stories on the page.
    region_order = ["EUROPE", "MIDDLE EAST", "AFRICA", "ASIA", "AMERICAS",
                    "OCEANIA", "WORLD"]
    regions = {}
    for s in stories:
        r = s.get("region", "WORLD")
        regions[r] = regions.get(r, 0) + 1
    regions = {r: regions[r] for r in region_order if r in regions}
    n_regions = len(regions)

    # --- top band ------------------------------------------------------
    d.rectangle([0, 0, W, 26], fill=NAVY)
    f_band = font(SANS_B, 13)
    d.text((M, 5), "THE WORLD IN ONE DAY", font=f_band, fill=(255, 255, 255))
    right = f"{n_total} STORIES · {n_regions} REGIONS · ALL FROM THIS ONE DAY"
    d.text((W - M - text_w(d, right, f_band), 5), right, font=f_band,
           fill=(255, 210, 90))

    # --- masthead ------------------------------------------------------
    f_date = font(SERIF_B, 56)
    d.text((M, 30), data["date_label"], font=f_date, fill=INK)
    f_kick = font(SERIF, 17)
    kicker = fit(d, data["kicker"], f_kick, W - 2 * M, 1)[0]
    d.text((M, 96), kicker, font=f_kick, fill=RED)
    d.line([M, 120, W - M, 120], fill=NAVY, width=2)

    # --- region chips --------------------------------------------------
    x = M
    f_chip = font(SANS_B, 12)
    for region, count in regions.items():
        label = f"{region} {count}"
        x = chip(d, x, 128, label, f_chip, REGION_COLORS.get(region, (90, 90, 90)))
        x += 6

    # --- UTC timeline --------------------------------------------------
    d.rectangle([M, 152, W - M, 176], fill=NAVY2)
    f_tl = font(SANS_B, 11)
    d.text((M + 8, 158), "UTC", font=f_tl, fill=(255, 210, 90))
    tl = data["timeline"]
    slot_w = (W - 2 * M - 60) / max(len(tl), 1)
    for i, item in enumerate(tl):
        tx = M + 60 + i * slot_w
        d.text((tx, 158), item["time"], font=f_tl, fill=(255, 255, 255))
        f_tl2 = font(SANS, 10)
        label = fit(d, item["label"], f_tl2, slot_w - 42, 1)[0]
        d.text((tx + 38, 159), label, font=f_tl2, fill=(210, 220, 235))

    # --- feature stories (3 across) ------------------------------------
    feat_y, feat_h = 184, 168
    card_w = (W - 2 * M - 2 * 12) // 3
    for i, s in enumerate(data["features"][:3]):
        cx = M + i * (card_w + 12)
        d.rectangle([cx, feat_y, cx + card_w, feat_y + feat_h], fill=CARD,
                    outline=LIGHT_LINE, width=1)
        # illustration band
        draw_icon(img, s.get("icon", "globe"), cx + 1, feat_y + 1, card_w - 2, 64,
                  tuple(s.get("sky", (40, 60, 90))))
        num_badge(d, cx + 6, feat_y + 70, s["n"])
        f_place = font(SANS_B, 11)
        place = f'{s["place"]} · {s["topic"]}'.upper()
        d.text((cx + 30, feat_y + 72), fit(d, place, f_place, card_w - 36, 1)[0],
               font=f_place, fill=NAVY)
        chip(d, cx + card_w - 78, feat_y + 70, s["label"], font(SANS_B, 9),
             LABEL_COLORS.get(s["label"], (90, 90, 90)))
        y = feat_y + 92
        f_head = font(SANS_B, 16)
        y = draw_lines(d, cx + 8, y, fit(d, s["headline"], f_head, card_w - 16, 2),
                       f_head, leading=19)
        f_body = font(SANS, 11)
        draw_lines(d, cx + 8, feat_y + 130,
                   fit(d, s["body"], f_body, card_w - 16, 2), f_body, leading=13)
        f_src = font(SANS, 9)
        d.text((cx + 8, feat_y + feat_h - 14), s["source"], font=f_src, fill=GREY)

    # --- medium stories (5 x 2) ---------------------------------------
    med_y, med_h = 360, 98
    col_w = (W - 2 * M - 4 * 8) // 5
    for i, s in enumerate(data["medium"][:10]):
        col, row = i % 5, i // 5
        cx = M + col * (col_w + 8)
        cy = med_y + row * (med_h + 8)
        d.rectangle([cx, cy, cx + col_w, cy + med_h], fill=CARD,
                    outline=LIGHT_LINE, width=1)
        draw_icon(img, s.get("icon", "globe"), cx + 1, cy + 1, col_w - 2, 30,
                  tuple(s.get("sky", (60, 80, 110))))
        num_badge(d, cx + 5, cy + 34, s["n"], d=16)
        f_place = font(SANS_B, 9)
        place = f'{s["place"]} · {s["topic"]}'.upper()
        d.text((cx + 24, cy + 36), fit(d, place, f_place, col_w - 28, 1)[0],
               font=f_place, fill=NAVY)
        f_head = font(SANS_B, 12)
        draw_lines(d, cx + 6, cy + 52,
                   fit(d, s["headline"], f_head, col_w - 12, 2), f_head, leading=14)
        f_src = font(SANS, 8)
        chip_r = chip(d, cx + 6, cy + med_h - 15, s["label"], font(SANS_B, 8),
                      LABEL_COLORS.get(s["label"], (90, 90, 90)))
        src = fit(d, s["source"], f_src, col_w - (chip_r - cx) - 10, 1)
        if src:
            d.text((chip_r + 4, cy + med_h - 14), src[0], font=f_src, fill=GREY)

    # --- "also on" header ----------------------------------------------
    y = 578
    f_also = font(SANS_B, 14)
    d.text((M, y), f"ALSO ON {data['date_label'].upper()}", font=f_also, fill=NAVY)
    d.line([M, y + 20, W - M, y + 20], fill=NAVY, width=1)

    # --- map (left) + also list (right) --------------------------------
    map_x, map_y, map_w, map_h = M, 606, 292, 188
    pins = []
    for s in stories:
        if "pin" in s:
            pins.append((s["n"], tuple(s["pin"])))
    draw_map(d, map_x, map_y, map_w, map_h, pins[:13])
    f_map = font(SANS_B, 11)
    d.text((map_x + 6, map_y + map_h - 20), "WHERE IT HAPPENED — pins = story numbers",
           font=font(SANS_B, 9), fill=NAVY)

    list_x = map_x + map_w + 14
    list_w = W - M - list_x
    col_w2 = list_w // 2
    f_item = font(SANS, 11)
    f_item_b = font(SANS_B, 11)
    for i, s in enumerate(data["also"][:18]):
        col, row = i % 2, i // 2
        ix = list_x + col * col_w2
        iy = map_y + 4 + row * 21
        d.text((ix, iy), f"{s['n']}", font=f_item_b, fill=RED)
        line = fit(d, s["headline"], f_item, col_w2 - 30, 1)[0]
        d.text((ix + 24, iy), line, font=f_item, fill=INK)
        src = fit(d, s["source"], font(SANS, 8), col_w2 - 30, 1)
        if src:
            d.text((ix + 24, iy + 11), src[0], font=font(SANS, 8), fill=GREY)

    # --- day in numbers -------------------------------------------------
    num_y, num_h = 804, 66
    d.rectangle([M, num_y, W - M, num_y + num_h], fill=NAVY)
    f_num = font(SANS_B, 22)
    f_num_l = font(SANS, 10)
    nums = data["numbers"][:5]
    slot = (W - 2 * M) / len(nums)
    d.text((M + 10, num_y + 4), "THE DAY IN NUMBERS", font=font(SANS_B, 9),
           fill=(255, 210, 90))
    for i, item in enumerate(nums):
        nx = M + i * slot
        d.text((nx + 10, num_y + 16), item["value"], font=f_num, fill=(255, 210, 90))
        lab = fit(d, item["label"], f_num_l, slot - 16, 2)
        draw_lines(d, nx + 10, num_y + 42, lab, f_num_l, fill=(220, 225, 235),
                   leading=11)
    # (label sits inside the strip; nothing is drawn above it, so it can
    # never collide with the map panel)

    # --- date check -----------------------------------------------------
    dc_y, dc_h = 878, 62
    d.rectangle([M, dc_y, W - M, dc_y + dc_h], outline=RED, width=2)
    d.rectangle([M, dc_y, M + 96, dc_y + dc_h], fill=RED)
    f_dc = font(SANS_B, 12)
    d.text((M + 8, dc_y + 12), "DATE", font=f_dc, fill=(255, 255, 255))
    d.text((M + 8, dc_y + 28), "CHECK", font=f_dc, fill=(255, 255, 255))
    f_dc_t = font(SANS, 11)
    dc_text = ("Every story here happened, or was first reported, on "
               f"{data['date_label']} (UTC). Left out because they happened "
               f"on an earlier day: {data['excluded']}")
    draw_lines(d, M + 108, dc_y + 6,
               fit(d, dc_text, f_dc_t, W - 2 * M - 120, 3), f_dc_t, leading=14)

    # --- footer ---------------------------------------------------------
    fy = 946
    f_leg = font(SANS_B, 10)
    x = M
    d.text((x, fy), "HOW SURE:", font=f_leg, fill=NAVY)
    x += text_w(d, "HOW SURE: ", f_leg)
    for label in ["CONFIRMED", "OFFICIAL", "REPORTED", "CLAIM"]:
        x = chip(d, x, fy - 2, label, font(SANS_B, 9),
                 LABEL_COLORS[label]) + 6
    legend = ("CONFIRMED = 2+ outlets · OFFICIAL = on record · REPORTED = "
              "carried by the outlets named · CLAIM = one side's word")
    d.text((x + 4, fy), fit(d, legend, font(SANS, 9), W - M - x - 4, 1)[0],
           font=font(SANS, 9), fill=GREY)
    f_foot = font(SANS, 9)
    foot = (f"Sources: {data['footer_sources']} · Illustrations and map drawn "
            f"in code — no photos · All {n_total} stories dated "
            f"{data['date_label']} (UTC)")
    d.text((M, fy + 20), fit(d, foot, f_foot, W - 2 * M, 1)[0], font=f_foot,
           fill=GREY)
    d.text((M, fy + 36),
           f"THE WORLD IN ONE DAY · {data['date_label'].upper()} · "
           f"{n_total} STORIES · {n_regions} REGIONS",
           font=font(SANS_B, 9), fill=NAVY)

    img.save(out_path, format="PNG", optimize=False)
    print(f"wrote {out_path} ({len(open(out_path, 'rb').read())} bytes)")


def main():
    if len(sys.argv) != 3:
        print("usage: python3 render.py stories.json entry.png", file=sys.stderr)
        sys.exit(2)
    with open(sys.argv[1], encoding="utf-8") as fh:
        data = json.load(fh)
    render(data, sys.argv[2])


if __name__ == "__main__":
    main()
