"""TA04-P1 -- contact sheets from results/P1/qc_chips.

Four sheets, grouped as requested:
  1 TAP              (TAP ASGM + TAP hard negatives)
  2 MDD + GHA-IND    (MDD ASGM + MDD hard negatives + Ghana industrial-flagged)
  3 GHA-UNC + GHA-NEG(Ghana unclassified + Ghana hard negatives)
  4 PRK              (all DPRK polygons)

NOTE ON LAYOUT: the request was "40 chips each, 8x5". The four groups actually hold
44 / 37 / 29 / 50 chips, so a fixed 8x5 would silently drop 4 TAP and 10 DPRK chips.
The grouping is what carries the meaning, so the grid is held at 8 COLUMNS and the row
count follows the group (6 / 5 / 4 / 7 rows). Every one of the 160 chips appears exactly
once. Chips are 1 x 1 km at 10 m (100 x 100 px) and are upscaled 2x nearest-neighbour so
the pit texture stays readable; id and proposed_label are printed under each.
"""
import os, math
import pandas as pd
from PIL import Image, ImageDraw, ImageFont

CHIPS = "results/P1/qc_chips"
OUT = "results/P1/qc_sheets"
os.makedirs(OUT, exist_ok=True)

COLS = 8
SCALE = 2                      # 100 px chip -> 200 px
CHIP = 100 * SCALE
PAD = 10
CAP_H = 30                     # caption band under each chip
TITLE_H = 44
BG = (250, 250, 248)
FG = (25, 25, 25)
SUB = (95, 95, 95)

F_REG = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf"
F_BOLD = "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf"
f_id = ImageFont.truetype(F_BOLD, 13)
f_lab = ImageFont.truetype(F_REG, 12)
f_title = ImageFont.truetype(F_BOLD, 22)

SHORT = {"ASGM": "ASGM",
         "industrial": "industrial",
         "mining, unclassified": "mining, unclass.",
         "mining, unclassified (data-denied)": "unclass. (data-denied)",
         "not mining": "not mining"}

def groups(q):
    neg = q.id.str.startswith("NEG_")
    return [
        ("01_TAP", "TAP (Tapajos) — Maus v2 x AMW ASGM positives + hard negatives",
         q[q.id.str.startswith("TAP_ASGM") | (neg & (q.region == "TAP"))]),
        ("02_MDD_GHA-industrial", "MDD (Madre de Dios) ASGM + hard negatives, and Ghana industrial-flagged",
         q[q.id.str.startswith("MDD_ASGM") | (neg & (q.region == "MDD")) | q.id.str.startswith("GHA_IND")]),
        ("03_GHA-unclassified_GHA-negatives", "Ghana 'mining, unclassified' + Ghana hard negatives",
         q[q.id.str.startswith("GHA_UNC") | (neg & (q.region == "GHA"))]),
        ("04_PRK", "DPRK — all polygons (Tang & Werner / Maus v2), feasibility only, no training",
         q[q.id.str.startswith("PRK_")]),
    ]

def sheet(name, title, rows):
    n = len(rows)
    nr = math.ceil(n / COLS)
    cw = CHIP + PAD
    ch = CHIP + CAP_H + PAD
    W = COLS * cw + PAD
    H = TITLE_H + nr * ch + PAD
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    d.text((PAD, 12), f"{title}   [{n} chips, 1 x 1 km @ 10 m, S2-2019 annual median]",
           font=f_title, fill=FG)
    d.line([(PAD, TITLE_H - 6), (W - PAD, TITLE_H - 6)], fill=(200, 200, 195), width=1)
    missing = 0
    for i, r in enumerate(rows.itertuples()):
        cx = PAD + (i % COLS) * cw
        cy = TITLE_H + (i // COLS) * ch
        p = os.path.join(CHIPS, f"{r.id}.png")
        if os.path.exists(p):
            c = Image.open(p).convert("RGB").resize((CHIP, CHIP), Image.NEAREST)
        else:
            c = Image.new("RGB", (CHIP, CHIP), (215, 215, 215)); missing += 1
        im.paste(c, (cx, cy))
        d.rectangle([cx, cy, cx + CHIP - 1, cy + CHIP - 1], outline=(170, 170, 165))
        d.text((cx + 2, cy + CHIP + 3), r.id, font=f_id, fill=FG)
        d.text((cx + 2, cy + CHIP + 17), SHORT.get(r.proposed_label, r.proposed_label),
               font=f_lab, fill=SUB)
    f = os.path.join(OUT, f"{name}.png")
    im.save(f, optimize=True)
    print(f"  {f}  {n} chips  {COLS}x{nr}  {im.size[0]}x{im.size[1]}px  "
          f"{os.path.getsize(f)/1e6:.2f} MB" + (f"  MISSING {missing}" if missing else ""))
    return n

if __name__ == "__main__":
    q = pd.read_csv("results/P1/qc_table.csv")
    tot = 0
    for name, title, rows in groups(q):
        tot += sheet(name, title, rows.reset_index(drop=True))
    print(f"total chips placed {tot} / {len(q)}")
    assert tot == len(q), "chips lost between groups"
