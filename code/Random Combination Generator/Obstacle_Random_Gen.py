#!/usr/bin/env python3
"""
WRO Future Engineers 2026 -- Obstacle Challenge random field generator (v3)
=============================================================================

Overlays randomised traffic-sign and parking-lot placements directly on
top of the REAL official playfield artwork (WRO-2026_FutureEngineers_
Playfield.pdf), instead of hand-drawing the mat. Output is a small,
self-contained "popup" HTML file (fixed-size card, not a full page) that
just opens in a browser.

SEAT GEOMETRY -- measured directly from the official artwork
-----------------------------------------------------------------
The 6 traffic-sign seats per straightforward section were located by
pixel-detecting the actual printed marker squares in the reference
image (connected-component analysis, sub-pixel accurate). This gives
a genuine 3 (along the length of the section) x 2 (across its width)
grid -- confirmed empirically, not guessed from ambiguous rule text.
The orange/blue diagonal lines are already part of the artwork and are
confined to the 4 corner (turn) sections only; they are NOT involved
in seat placement, and this script draws nothing extra for them.

RANDOMISATION -- follows Section 8 "Obstacle Challenge rounds" exactly
-----------------------------------------------------------------
 * 9.3      Driving direction (CW / CCW) chosen randomly.
 * step 1-2 Coin tosses select which section gets the single sign, and
            its colour.
 * step 3   36-card deck; card #9 = single green, #10 = single red
            (used directly, not drawn); remaining 35 shuffled, 3 drawn
            without replacement for the other three sections in
            clockwise order.
 * step 4   Coin tosses select the starting/parking section; signs in
            that section are moved to the inner-wall row (Fig. 8e).
 * Fig. 4   Parking lot: 200mm fixed width, length = 1.5 x robot length,
            two 200x20x100mm magenta markers.

HONEST LIMITATION
------------------
The 36-card deck's exact artwork (Fig. 8c) can't be recovered pixel-
perfectly from the source PDF. Cards #9/#10 are exactly as specified
by the rules; the other 34 are a clearly-labelled, self-consistent
reconstruction. The traffic-sign SEAT POSITIONS, however, are now
taken directly from the real mat artwork, not reconstructed.

Usage
-----
    python wro_fe_obstacle_generator.py --seed 42 --robot-length 250 \
        --output field.html
"""

import argparse
import base64
import io
import random
import webbrowser
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from PIL import Image

HERE = Path(__file__).resolve().parent
PLAYFIELD_IMAGE = HERE / "playfield.png"   # the real mat artwork, rasterised

# ---------------------------------------------------------------------------
# Pixel calibration of the reference artwork (2730 x 2730 px)
# ---------------------------------------------------------------------------
RAW_SIZE = 2730.0
# outer track boundary (yellow line), measured via connected-component
# analysis of the raw artwork -> defines the 3000x3000mm track in pixels
X0_RAW, X1_RAW = 131.5, 2597.0
Y0_RAW, Y1_RAW = 131.0, 2597.0
SCALE_RAW = (X1_RAW - X0_RAW) / 3000.0   # px per mm, at native 2730px resolution

# the 6 traffic-sign seat pixel centres per straightforward section,
# measured directly from the artwork (sub-pixel accurate connected-
# component centroids of the printed marker squares). Indexed as
# [len_idx (0,1,2 along the section's length)][wid_idx (0=outer,1=inner)]
SEAT_PIXELS_RAW = {
    'N': {(0, 0): (939.5, 428.5), (1, 0): (1364.5, 428.5), (2, 0): (1790.0, 428.5),
          (0, 1): (939.5, 598.5), (1, 1): (1364.5, 598.5), (2, 1): (1790.0, 598.5)},
    'S': {(0, 1): (939.5, 2129.5), (1, 1): (1364.5, 2129.5), (2, 1): (1790.0, 2129.5),
          (0, 0): (939.5, 2299.5), (1, 0): (1364.5, 2299.5), (2, 0): (1790.0, 2299.5)},
    'W': {(0, 0): (430.0, 939.5), (1, 0): (430.0, 1364.5), (2, 0): (430.0, 1790.0),
          (0, 1): (599.5, 939.5), (1, 1): (599.5, 1364.5), (2, 1): (599.5, 1790.0)},
    'E': {(0, 1): (2130.5, 939.5), (1, 1): (2130.5, 1364.5), (2, 1): (2130.5, 1790.0),
          (0, 0): (2300.5, 939.5), (1, 0): (2300.5, 1364.5), (2, 0): (2300.5, 1790.0)},
}
# len_idx orientation per section (which physical end is len_idx=0), so that
# "clockwise order along the section" is consistent -- N/E/S/W run
# clockwise, so len_idx increases in the clockwise travel direction.

CLOCKWISE = ['N', 'E', 'S', 'W']

RED_RGB = "#ee2737"     # 13.21
GREEN_RGB = "#44d62c"   # 13.22
MAGENTA_RGB = "#ff00ff"  # 13.27

PARK_WIDTH = 200.0       # mm, Fig. 4
PARK_MARKER_LEN = 200.0
PARK_MARKER_THICK = 20.0

# ---------------------------------------------------------------------------
# 36-card deck (Fig. 8c). Cards 9 & 10 are exactly as specified by the rules.
# Each sign = (len_idx 0-2, wid_idx 0=upper/1=lower, colour)
# ---------------------------------------------------------------------------
DECK = [
    [(0, 0, 'green')],                                             # 1
    [(0, 0, 'red')],                                                # 2
    [(1, 0, 'green')],                                              # 3
    [(1, 0, 'red')],                                                # 4
    [(2, 0, 'green')],                                              # 5
    [(2, 0, 'red')],                                                # 6
    [(0, 1, 'green')],                                              # 7
    [(0, 1, 'red')],                                                # 8
    [(1, 1, 'green')],           # 9  <- single GREEN template (removed, not drawn)
    [(1, 1, 'red')],             # 10 <- single RED template (removed, not drawn)
    [(2, 0, 'green')],                                              # 11
    [(2, 0, 'red')],                                                # 12
    [(2, 0, 'green'), (0, 1, 'green')],                             # 13
    [(2, 0, 'red'), (0, 1, 'green')],                               # 14
    [(2, 0, 'green'), (0, 1, 'red')],                               # 15
    [(2, 0, 'red'), (0, 1, 'green')],                               # 16
    [(2, 0, 'green'), (0, 1, 'red')],                               # 17
    [(2, 0, 'red'), (0, 1, 'red')],                                 # 18
    [(0, 0, 'green'), (2, 1, 'green')],                             # 19
    [(0, 0, 'green'), (2, 1, 'red')],                               # 20
    [(0, 0, 'red'), (2, 1, 'green')],                               # 21
    [(0, 0, 'green'), (2, 1, 'red')],                               # 22
    [(0, 0, 'red'), (2, 1, 'green')],                               # 23
    [(0, 0, 'red'), (2, 1, 'red')],                                 # 24
    [(2, 0, 'green'), (0, 0, 'green')],                             # 25
    [(2, 0, 'red'), (0, 0, 'green')],                               # 26
    [(2, 0, 'green'), (0, 0, 'red')],                               # 27
    [(2, 0, 'red'), (0, 0, 'green')],                               # 28
    [(0, 0, 'red'), (2, 0, 'green')],                               # 29
    [(0, 0, 'red'), (2, 0, 'red')],                                 # 30
    [(0, 1, 'green'), (2, 1, 'green')],                             # 31
    [(0, 1, 'green'), (2, 1, 'red')],                               # 32
    [(0, 1, 'red'), (2, 1, 'green')],                               # 33
    [(0, 1, 'green'), (2, 1, 'red')],                               # 34
    [(0, 1, 'red'), (2, 1, 'green')],                               # 35
    [(0, 1, 'red'), (2, 1, 'red')],                                 # 36
]
assert len(DECK) == 36

SECTION_FROM_TOSS = {('H', 'H'): 'N', ('T', 'H'): 'W', ('H', 'T'): 'E', ('T', 'T'): 'S'}


def next_sections_clockwise(start, n=3):
    i = CLOCKWISE.index(start)
    return [CLOCKWISE[(i + k) % 4] for k in range(1, n + 1)]


def section_bbox_mm(section):
    """(x0, y0, x1, y1) in mm, origin = bottom-left of the outer wall,
    used only for the parking lot (which isn't pre-printed on the mat)."""
    lo, hi = 1000.0, 2000.0
    if section == 'S':
        return (lo, 0.0, hi, 1000.0)
    if section == 'N':
        return (lo, 2000.0, hi, 3000.0)
    if section == 'W':
        return (0.0, lo, 1000.0, hi)
    if section == 'E':
        return (2000.0, lo, 3000.0, hi)
    raise ValueError(section)


def mm_to_raw_px(x_mm, y_mm):
    return (X0_RAW + x_mm * SCALE_RAW, Y0_RAW + (3000.0 - y_mm) * SCALE_RAW)


# ---------------------------------------------------------------------------
# Round generation
# ---------------------------------------------------------------------------
@dataclass
class RoundConfig:
    direction: str
    single_section: str
    single_color: str
    section_cards: dict
    signs: list
    start_section: str
    park_length: float
    start_in_parking: bool
    log: list = field(default_factory=list)


def coin(rng):
    return rng.choice(['H', 'T'])


def generate_round(seed: Optional[int] = None, robot_length: float = 250.0) -> RoundConfig:
    rng = random.Random(seed)
    log = []

    direction = rng.choice(['CW', 'CCW'])
    log.append(f"[9.3] Driving direction: {direction}")

    t1, t2 = coin(rng), coin(rng)
    single_section = SECTION_FROM_TOSS[(t1, t2)]
    log.append(f"[8-step1] Coin toss {t1}{t2} -> single-sign section = {single_section}")

    t3 = coin(rng)
    single_color = 'green' if t3 == 'H' else 'red'
    log.append(f"[8-step2] Coin toss {t3} -> single-sign colour = {single_color}")

    deck = [(i + 1, layout) for i, layout in enumerate(DECK)]
    remove_idx = 8 if single_color == 'green' else 9
    removed_card = deck.pop(remove_idx)
    rng.shuffle(deck)
    drawn = deck[:3]
    other_sections = next_sections_clockwise(single_section, 3)

    section_cards = {single_section: removed_card}
    for sec, card in zip(other_sections, drawn):
        section_cards[sec] = card
    for sec in CLOCKWISE:
        cid, _ = section_cards[sec]
        tag = " (template)" if sec == single_section else " (drawn)"
        log.append(f"[8-step3] Section {sec}: card #{cid}{tag}")

    signs = []
    for sec in CLOCKWISE:
        _, layout = section_cards[sec]
        for len_idx, wid_idx, color in layout:
            signs.append({'section': sec, 'len_idx': len_idx, 'wid_idx': wid_idx, 'color': color})

    t4, t5 = coin(rng), coin(rng)
    start_section = SECTION_FROM_TOSS[(t4, t5)]
    log.append(f"[8-step4] Coin toss {t4}{t5} -> starting/parking section = {start_section}")

    moved = False
    for s in signs:
        if s['section'] == start_section and s['wid_idx'] != 1:
            s['wid_idx'] = 1
            moved = True
    if moved:
        log.append(f"[Fig 8e] Signs in {start_section} moved closer to the inner wall")

    park_length = 1.5 * robot_length
    log.append(f"[Fig 4] Parking lot: {PARK_WIDTH:.0f}mm x {park_length:.0f}mm")

    start_in_parking = rng.choice([True, False])
    log.append(f"[8/1.8.1] Team choice - start inside parking lot: {start_in_parking}")

    return RoundConfig(
        direction=direction, single_section=single_section, single_color=single_color,
        section_cards=section_cards, signs=signs, start_section=start_section,
        park_length=park_length, start_in_parking=start_in_parking, log=log,
    )


# ---------------------------------------------------------------------------
# Rendering: overlay on the real artwork, produce a compact popup HTML
# ---------------------------------------------------------------------------
def render_popup_html(cfg: RoundConfig, robot_length: float,
                       output: str = "obstacle_challenge_field.html",
                       display_size: int = 560):
    img = Image.open(PLAYFIELD_IMAGE).convert("RGB")
    scale = display_size / RAW_SIZE

    def px(raw_x, raw_y):
        return raw_x * scale, raw_y * scale

    buf = io.BytesIO()
    img.resize((display_size, display_size), Image.LANCZOS).save(buf, format="PNG")
    b64 = base64.b64encode(buf.getvalue()).decode()

    svg_parts = [f'<svg width="{display_size}" height="{display_size}" '
                 f'viewBox="0 0 {display_size} {display_size}" '
                 f'style="position:absolute;top:0;left:0;pointer-events:none;">']

    seat_r = max(6, display_size * 0.018)
    for s in cfg.signs:
        raw_x, raw_y = SEAT_PIXELS_RAW[s['section']][(s['len_idx'], s['wid_idx'])]
        cx, cy = px(raw_x, raw_y)
        color = GREEN_RGB if s['color'] == 'green' else RED_RGB
        svg_parts.append(
            f'<rect x="{cx - seat_r:.1f}" y="{cy - seat_r:.1f}" '
            f'width="{seat_r * 2:.1f}" height="{seat_r * 2:.1f}" '
            f'fill="{color}" stroke="black" stroke-width="1.2" rx="1.5"/>'
        )

    # ---- parking lot (mm-based, since it's not pre-printed on the mat) ----
    x0, y0, x1, y1 = section_bbox_mm(cfg.start_section)
    if cfg.start_section in ('N', 'S'):
        length_lo, length_hi = x0, x1
        pad = max(0.0, (length_hi - length_lo - cfg.park_length) / 2)
        p_lo = length_lo + pad
        p_hi = length_lo + pad + min(cfg.park_length, length_hi - length_lo)
        if cfg.start_section == 'S':
            park_y0, park_y1 = y0, y0 + PARK_WIDTH
        else:
            park_y0, park_y1 = y1 - PARK_WIDTH, y1
        rect_mm = (p_lo, park_y0, p_hi, park_y1)
        marker_rects_mm = [
            (p_lo - PARK_MARKER_THICK / 2, park_y0, p_lo + PARK_MARKER_THICK / 2, park_y0 + PARK_MARKER_LEN),
            (p_hi - PARK_MARKER_THICK / 2, park_y0, p_hi + PARK_MARKER_THICK / 2, park_y0 + PARK_MARKER_LEN),
        ]
    else:
        length_lo, length_hi = y0, y1
        pad = max(0.0, (length_hi - length_lo - cfg.park_length) / 2)
        p_lo = length_lo + pad
        p_hi = length_lo + pad + min(cfg.park_length, length_hi - length_lo)
        if cfg.start_section == 'W':
            park_x0, park_x1 = x0, x0 + PARK_WIDTH
        else:
            park_x0, park_x1 = x1 - PARK_WIDTH, x1
        rect_mm = (park_x0, p_lo, park_x1, p_hi)
        marker_rects_mm = [
            (park_x0, p_lo - PARK_MARKER_THICK / 2, park_x0 + PARK_MARKER_LEN, p_lo + PARK_MARKER_THICK / 2),
            (park_x0, p_hi - PARK_MARKER_THICK / 2, park_x0 + PARK_MARKER_LEN, p_hi + PARK_MARKER_THICK / 2),
        ]

    def rect_mm_to_svg(rx0, ry0, rx1, ry1, **attrs):
        rax, ray = mm_to_raw_px(rx0, ry1)
        rbx, rby = mm_to_raw_px(rx1, ry0)
        ax, ay = px(rax, ray)
        bx, by = px(rbx, rby)
        x0_, x1_ = sorted((ax, bx))
        y0_, y1_ = sorted((ay, by))
        attr_str = " ".join(f'{k}="{v}"' for k, v in attrs.items())
        return f'<rect x="{x0_:.1f}" y="{y0_:.1f}" width="{x1_ - x0_:.1f}" height="{y1_ - y0_:.1f}" {attr_str}/>'

    svg_parts.append(rect_mm_to_svg(*rect_mm, fill="#000000", **{"fill-opacity": "0.06"}))
    for m in marker_rects_mm:
        svg_parts.append(rect_mm_to_svg(*m, fill=MAGENTA_RGB, stroke="black", **{"stroke-width": "0.8"}))

    # ---- start marker ----
    if cfg.start_in_parking:
        scx_mm, scy_mm = (rect_mm[0] + rect_mm[2]) / 2, (rect_mm[1] + rect_mm[3]) / 2
    else:
        x0, y0, x1, y1 = section_bbox_mm(cfg.start_section)
        length_center = (p_lo + p_hi) / 2
        if cfg.start_section in ('N', 'S'):
            inner_w = y0 + 0.75 * (y1 - y0) if cfg.start_section == 'S' else y1 - 0.75 * (y1 - y0)
            scx_mm, scy_mm = length_center, inner_w
        else:
            inner_w = x0 + 0.75 * (x1 - x0) if cfg.start_section == 'W' else x1 - 0.75 * (x1 - x0)
            scx_mm, scy_mm = inner_w, length_center
    raw_sx, raw_sy = mm_to_raw_px(scx_mm, scy_mm)
    sx, sy = px(raw_sx, raw_sy)
    star_r = display_size * 0.02
    svg_parts.append(
        f'<text x="{sx:.1f}" y="{sy + star_r:.1f}" font-size="{star_r*2.4:.0f}" '
        f'text-anchor="middle" fill="black">&#9733;</text>'
    )

    svg_parts.append('</svg>')
    svg = "\n".join(svg_parts)

    start_label = "Starts IN parking lot" if cfg.start_in_parking else "Starts opposite parking lot"
    log_html = "\n".join(f"<li>{l}</li>" for l in cfg.log)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Obstacle Challenge Field</title>
<style>
  html, body {{ margin:0; padding:0; background:#eef0f3; font-family:-apple-system,Segoe UI,Roboto,sans-serif; }}
  .popup {{
    width: {display_size}px; margin: 24px auto; background:#fff; border-radius:14px;
    box-shadow: 0 8px 28px rgba(0,0,0,0.18); overflow:hidden;
  }}
  .stage {{ position:relative; width:{display_size}px; height:{display_size}px; }}
  .stage img {{ width:100%; height:100%; display:block; }}
  .bar {{ padding:10px 14px; font-size:13px; color:#222; border-top:1px solid #eee; }}
  .bar b {{ color:#000; }}
  .dot {{ display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:5px; vertical-align:middle;}}
  details {{ padding: 0 14px 10px; }}
  summary {{ cursor:pointer; font-size:12px; color:#666; }}
  ul {{ font-family: ui-monospace, Consolas, monospace; font-size:11px; color:#444; line-height:1.5; padding-left:16px;}}
</style>
</head>
<body>
<div class="popup">
  <div class="stage">
    <img src="data:image/png;base64,{b64}" />
    {svg}
  </div>
  <div class="bar">
    <b>{cfg.direction}</b> &middot; single sign: <b>{cfg.single_section} ({cfg.single_color})</b>
    &middot; parking: <b>{cfg.start_section}</b> &middot; {start_label}<br>
    <span class="dot" style="background:{GREEN_RGB}"></span>keep LEFT
    <span class="dot" style="background:{RED_RGB}"></span>keep RIGHT
    <span class="dot" style="background:{MAGENTA_RGB}"></span>parking markers
  </div>
  <details>
    <summary>Randomisation log</summary>
    <ul>{log_html}</ul>
  </details>
</div>
</body>
</html>"""

    with open(output, "w") as f:
        f.write(html)
    return output


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    # Just run this file with no options: `python wro_fe_obstacle_generator.py`
    # It will build a new random round and open it in your browser automatically.
    # (The flags below are entirely optional, for people who want them.)
    ap = argparse.ArgumentParser(description="WRO FE 2026 Obstacle Challenge field generator")
    ap.add_argument('--seed', type=int, default=None,
                     help="Optional: reuse the same number to get the exact same round again.")
    ap.add_argument('--robot-length', type=float, default=250.0,
                     help="Optional: your robot's length in mm (default 250).")
    ap.add_argument('--output', type=str, default='obstacle_challenge_field.html')
    ap.add_argument('--size', type=int, default=560, help='Popup display size in px')
    ap.add_argument('--no-open', action='store_true', help="Don't auto-open the result in a browser")
    args = ap.parse_args()

    cfg = generate_round(seed=args.seed, robot_length=args.robot_length)
    print("=" * 70)
    for line in cfg.log:
        print(line)
    print("=" * 70)
    for s in cfg.signs:
        print(f"  section={s['section']}  len_idx={s['len_idx']}  "
              f"wid_idx={'inner' if s['wid_idx'] else 'outer'}  colour={s['color']}")
    print("=" * 70)

    path = render_popup_html(cfg, args.robot_length, output=args.output, display_size=args.size)
    full_path = Path(path).resolve()
    print(f"Saved: {full_path}")

    if not args.no_open:
        try:
            webbrowser.open(f"file://{full_path}")
            print("Opened it in your browser. If nothing appeared, just double-click the file above.")
        except Exception:
            print("Couldn't auto-open a browser -- just double-click the file above.")


if __name__ == '__main__':
    main()
