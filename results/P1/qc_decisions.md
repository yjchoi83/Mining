# TA04-P1 — reference purity QC: human adjudications

Adjudicated by the human reviewer against `results/P1/qc_sheets/*.png`
(1 x 1 km Sentinel-2 2019 annual-median RGB at 10 m, reference outline burnt in).
Decisions are written into the `decision` column of `results/P1/qc_table.csv`
by `code/p1_decisions.py`; that script only transcribes them.

## Decision vocabulary
| value | meaning |
|---|---|
| `ASGM_confirmed` | Amazon positive; artisanal workings visible inside the outline |
| `ASM_confirmed` | Ghana unclassified positive; artisanal workings visible |
| `industrial_confirmed` | Ghana flagged positive; large-scale mine visible |
| `ASM_like_flag_error` | flagged industrial but reads as artisanal — the 5 km proximity rule misfired |
| `PRK_VISIBLE` | DPRK polygon with a surface mining footprint at 10 m annual median |
| `PRK_NOT_VISIBLE` | DPRK polygon with no surface footprint at 10 m annual median |
| `non_mining_confirmed` | hard negative; no mining visible |
| `uncertain` | not adjudicable from a 1 km annual-median chip |

## Amazon — TAP (Tapajos), 35 ASGM chips
- **`ASGM_confirmed` (32):** `TAP_ASGM_000`–`016`, `018`–`021`, `023`–`033`
- **`uncertain` (3):**
  - `TAP_ASGM_017` — river-bend sandbar vs dredging; cannot separate
  - `TAP_ASGM_022` — polygon mostly forest in 2019
  - `TAP_ASGM_034` — polygon offset from visible mining
- **Purity ~91% (32/35).**

## Amazon — MDD (Madre de Dios), 15 ASGM chips
- **`ASGM_confirmed` (13):** `MDD_ASGM_000`–`009`, `011`, `012`, `014`
- **`uncertain` (2):** `MDD_ASGM_010`, `MDD_ASGM_013` — natural river sandbar possible
- **Purity ~87% (13/15).**

## Ghana — industrial-flagged, 15 chips
- **`industrial_confirmed` (7):** `GHA_IND_002`, `004`, `005`, `006`, `007`, `008`, `014`
- **`ASM_like_flag_error` (3):** `GHA_IND_000`, `001`, `003`
- **`uncertain` (5):** `GHA_IND_009`, `010`, `011`, `012`, `013`
- **The industrial flag is unreliable from the proximity rule alone.** Only 7/15 survive
  inspection, 3/15 are outright wrong, and 5/15 cannot be settled from the chip. A 5 km
  radius around a named mine does not separate large-scale from artisanal workings in the
  Ghana box, because galamsey clusters immediately around the concessions.

## Ghana — unclassified, 15 chips
- **`ASM_confirmed` (13):** `GHA_UNC_000`–`010`, `013`, `014`
- **`uncertain` (2):** `GHA_UNC_011` (settlement), `GHA_UNC_012` (rectangular bare patch — quarry?)
- **Purity ~87% (13/15).**

## DPRK — 50 chips (feasibility only, no training)
- **`PRK_VISIBLE` (21):** `PRK_000`, `001`, `002`, `003`, `004`, `005`, `007`, `008`, `010`,
  `011`, `015`, `018`, `020`, `024`, `027`, `030`, `031`, `032`, `035`, `037`, `038`
- **`PRK_NOT_VISIBLE` (29):** all remaining ids — no surface footprint at 10 m annual median.
- **Only 42% of the DPRK polygons show visible surface mining.** Any future DPRK work must use
  **only the 21 `PRK_VISIBLE` polygons as the evaluation frame**; Tang & Werner as shipped is a
  candidate list, not a label set.

## Negatives — 30 chips
- **`non_mining_confirmed` (30):** all `NEG_000`–`029`, across TAP (9), MDD (7) and GHA (14).
- No unmapped mining was found in the negative sample, so the omission-driven "reported AUC is a
  lower bound" caveat from Stage 2 is **not** supported at this sample size.

## Purity summary
| stratum | confirmed | n | purity |
|---|---|---|---|
| TAP ASGM | 32 | 35 | **~91%** |
| MDD ASGM | 13 | 15 | **~87%** |
| GHA unclassified (ASM) | 13 | 15 | **~87%** |
| GHA industrial-flagged | 7 | 15 | **flag unreliable by proximity rule alone** |
| DPRK visible | 21 | 50 | **42%** |
| negatives | 30 | 30 | 100% |

## How this squares with the MapBiomas disagreement
The chips say the Amazon positives are ~87–91% pure *at the chip scale*, while the pixel-level
overlap (`tap_overlap.txt`) says 74.1% of the frame's **area** is outside any MapBiomas mining and
95% of that area is vegetated. These are consistent, not contradictory: a chip is scored on whether
*the workings are there*, whereas the area statistic is dominated by the forest the dilated
Maus x AMW intersection sweeps up **around** those workings. The positives are in the right places
and the frame is too fat. That is a geometry problem, not a labelling problem.
