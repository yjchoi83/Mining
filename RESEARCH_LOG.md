# RESEARCH_LOG — TA04

## 2026-09-06 — P1 step 0 (provenance)
Copied the Stage-4 G2 74-feature LightGBM baseline scripts (`G2_sample.py`,
`G2_analysis.py`) and the Stage-2 TA04 pilot scripts (`TA04_p1/p1b/p2/p3.py`,
`aefkit.py`) from `/d/yj_projects/workspace_yj/Alphaearth/aef_explore/scratch` into
`code/upstream/` with md5s and roles in `code/SOURCES.md`. ROI boxes reused verbatim:
TAP `[-58,-8,-54,-4]`, GHA `[-3.2,4.9,-0.9,7.2]`. Madre de Dios had **no** box upstream
(Stage 3 names the region only) so `MDD [-71.0,-13.4,-69.4,-12.0]` is new in P1 and
flagged as a deviation. Wrote `PLAN.md` with the pre-registered decision rule
(ratio >= 3 and CI lower >= 2, else KILLED) before running anything.
**Provenance correction:** the GEE asset `global_mining_polygons` that all Stage-2/4
TA04 work called "Maus v2" measures 21,060 polygons / 57,277.7 km2 globally = **Maus v1**
(2020). v2 is 44,929 / 101,583. P1 pulls v2 from PANGAEA and reports both.

## 2026-09-06 — P1 step 1 (references)
**Maus v2** pulled from PANGAEA doi 10.1594/PANGAEA.942325 (`global_mining_polygons_v2.gpkg`,
24.66 MB): **44,929 polygons / 101,583.39 km2** — matches the published v2 figures exactly and
confirms the GEE `global_mining_polygons` asset used by Stage 2/4 is **v1** (21,060 / 57,277.7).
Consequence: in the Tapajos box Stage 2 saw **42 polygons / 240 km2** (v1); v2 gives
**623 polygons / 2,866.8 km2** — a 12x larger reference. All Stage-2/4 TA04 numbers rest on the
sparser v1 frame.
**Amazon Mining Watch** verified and downloaded from `earthrise-media/mining-detector`
`data/outputs/48px_v3.2-3.7ensemble/`: 2019 = 5,751 features, 2020 = 6,110 features
(`...0.50_<Y>-01-01_<Y>-12-31-dissolved-0.6.geojson`). Mirror of record is
`https://data.source.coop/earthgenome/amazon-mining-watch/`.
**Industrial mine list** compiled to `data/industrial_mines.csv` (20 usable centres + 1 rejected).
Sources per row: Wikidata P625 for 13 Ghana mines; Eldorado NI 43-101 via SEC EDGAR for
Tocantinzinho (06d03'S 56d18'W, first pour 2024 — post-dates the 2019 epoch); Serabi NI 43-101
(2025-09-10, p.25) for Palito (6.31S 55.79W) and Sao Chico (6.41S 55.94W). Wassa could not be
geolocated from any accessible source and is recorded as `geolocated=no`. **Rio Huaypetue was
deliberately EXCLUDED** from the industrial list: Wikidata classes it as a mine but it is the
largest *garimpo* complex in Madre de Dios, so using it as an exclusion centre would have deleted
the MDD positives. Tang & Werner's `Name` field is unusable as a named-mine source (values are
`9`, `Placemark`, `多边形`).
Counts: TAP 623 Maus v2 polys -> 570 intersect AMW -> 13 dropped within 5 km of Palito/Sao
Chico/Tocantinzinho -> **557 ASGM positives**. MDD 5 polys -> **1** (see deviation). GHA 528 polys
-> **78 industrial-flagged / 450 unclassified**.
**DEVIATION from PLAN §1.3 (tightening, purity-increasing).** The pre-registered rule accepts a
whole Maus polygon that *intersects* AMW. Maus v2 stores the entire Madre de Dios ASGM belt as
**one 2,536 km2 polygon**, of which only **814 km2** is AMW-confirmed; polygon-level acceptance
would have admitted ~1,700 km2 of non-mining interior as positive. The positive sampling frame is
therefore the **pixel-level intersection** (Maus v2 AND AMW), minus the 5 km industrial buffer:
TAP 2,658 -> **1,904 km2**, MDD 2,536 -> **814 km2**. This can only remove positives, never add
them, so it strictly raises reference purity.
**MapBiomas separates garimpo from industrial: YES.** ATBD Collection 10 Mining Appendix Table 3 —
`class_id` 1xx = "2. Industrial", 2xx = "1. Garimpo", **215 = Garimpo Gold**. Asset
`projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_mining_substances_v3`.
TAP box 2019 at native 30 m: **garimpo 573.8 km2 (gold 563.5), industrial 4.0 km2** — Tapajos is
~99% garimpo by area, which supports the ASGM-only framing but is **3.3x smaller than the
Maus x AMW frame (1,904 km2)**; that disagreement is a headline QC result, not a footnote.
GEE gotcha recorded: `reduceRegion` above native scale MEAN-aggregates class ids and manufactures
fake ones (53/107/161 = 1/4, 1/2, 3/4 of 215) — all class areas forced to 30 m via `.reproject()`.
**DPRK**: Tang & Werner **328** polygons inside the LSIB DPRK boundary; **Maus v2 only 30**
(24.56 km2 total). Top-20 written to `results/P1/dprk_polygons.csv`. `irenk.sonosa.or.kr` (I-RENK,
South-North Korea Exchanges and Cooperation Support Association) fetched: it provides
commodity-level distribution **maps** for 13 minerals plus reserve/production (2014-2021) and
DPRK-China trade statistics — **no per-mine names with coordinates, no downloadable geodatabase**;
`/main/mineral/mineralList.do` returns an invalid-service error.

## 2026-09-06 — P1 step 2 (reference purity QC chips)
160/160 chips written, **3.67 MB total** — under the 15 MB gate, so the chips are committed to
`results/P1/qc_chips/` rather than pushed to `data/`. Each is a Sentinel-2 2019 annual-median
RGB thumbnail, 1 x 1 km at 10 m (100 x 100 px), with the reference polygon outline painted in
yellow; `getThumbURL` only, no image exports. Inventory: **50 Amazon ASGM** (35 TAP + 15 MDD,
split by positive-frame area), **30 Ghana** (15 industrial-flagged + 15 unclassified),
**50 DPRK** (all polygons, capped at 50, largest first), **30 hard negatives** (14 GHA / 9 TAP /
7 MDD, drawn across the WorldCover strata). `results/P1/qc_table.csv` has the required columns
`id, region, source, proposed_label, decision, notes` with **`decision` left blank** — P1 delivers
the QC instrument, adjudication is a later package. Zero chip failures.
Spot checks: `TAP_ASGM_000` shows classic alluvial garimpo (bare spoil + turbid ponds);
`GHA_UNC_007` shows a small pit fully inside the outline; `PRK_000` (129.27E 42.24N, the largest
DPRK polygon at 9.89 km2 and the one point where Tang & Werner and Maus v2 agree) shows terraced
open-pit benches; `NEG_005` is forest/cleared edge with no mining.

## 2026-09-06 — P1 steps 3 & 4 (label-efficiency re-test)
Sampled AEF-2019 (64 bands) and the Stage-4 G2 **74-feature** classical baseline at the same
points, 10 m, chunked `sampleRegions`: TAP 8,000 / MDD 7,271 / GHA 7,998 (23,269 points, all
unique, no NaNs). Point sampling and 160 thumbnails only; **no image exports**.
**Bug caught mid-run:** attaching the MapBiomas band to the MDD stack silently dropped ~65% of
points (21/60 returned) because `.unmask(0)` AFTER `.reproject()` does not extend a Brazil-only
asset's footprint; AEF and all 74 baseline features returned 60/60 at the same points. MDD was
killed, the band scoped to TAP only, and MDD re-sampled at 100% yield.
Protocol as pre-registered: budgets {10,20,40,80,160,320,640,1000}, 20 draws, 5-fold GroupKFold on
**0.5-degree** blocks (79 Amazon / 36 Ghana), AUC, block bootstrap 1,000 draws resampling blocks
WITH multiplicity.
**Amazon ASGM-only (n=15,271; 8,000 positives; 79 blocks).** Full-data AUC: AEF 0.953 (log) /
0.960 (lgbm) vs BASE74 0.857 (log) / 0.909 (lgbm).
| arm | ratio | 95% CI | passes ratio>=3 & CI_lo>=2 |
|---|---|---|---|
| logistic (pre-registered primary) | **25.0**, right-censored | 9.12 – 25.0 | YES |
| LightGBM (capacity-matched) | **2.75** | 1.69 – 3.82 | **NO** |
| strongest-baseline (post-hoc, hostile) | **6.56** | 3.30 – 9.69 | YES |
**Verdict: SURVIVES on the pre-registered primary** — but this must not be reported as a clean win.
Stage 4's 19.9x (17.3-22.4) was computed on a **LightGBM** baseline; the same arm here collapses to
**2.75**, below the pre-registered falsification line. The large multiple is a *linear-probe*
phenomenon: with trees AEF at 40 labels is only 0.793 and the 74-feature baseline catches it by
~110 labels. The honest headline is the hostile arm, **6.56 (3.30-9.69)**, not 25x.
**DEVIATION (post-hoc, declared):** the strongest-baseline arm was added AFTER seeing the
classifier split, because neither same-classifier number is defensible alone. It gives AEF its best
k=40 AUC and the baseline the pointwise best of both classifiers at every budget.
**Ghana (mixed, transfer-only)** reproduces the pattern including the LightGBM collapse
(industrial 23.53 / 3.58 / 8.49; unclassified 25.0 / 3.40 / 22.40), so classifier-dependence is not
an Amazon artefact. Unclassified positives are **easier** than industrial-flagged ones (AEF full
0.977 vs 0.955) — the Stage-2 "Ghana is easier" result is therefore **not** driven by large-scale
mines, which weakens Stage-3 threat (a) in our favour. No ASGM claim rests on Ghana.
**Source agreement (TAP, at the sample points):** only **25.9%** of our Maus x AMW ASGM positives
are MapBiomas garimpo and **0.0%** are MapBiomas industrial (the 5 km industrial exclusion works);
**0.25%** of negatives touch any MapBiomas mining (negatives are clean). The 74% of positives
MapBiomas does not map as mining is the largest open reference question in the package and is what
`qc_table.csv` exists to adjudicate.

## 2026-09-06 — P1 steps 5 & 6 (DPRK summary, results file)
DPRK feasibility written into `results/P1/P1_results.md` §5. P3 recommendation: DPRK is a
**detection** transfer target only, never commodity attribution; source ROI should be **Ghana**,
not the Amazon, because DPRK footprints are small (median 1.7 ha), hard-rock and non-forest —
closer to Ghana's signature than to Amazonian alluvial garimpo; reference = Tang & Werner as a
frame only, with VHR adjudication. `results/P1/P1_results.md` is exactly 60 lines. **P2 not started.**

## 2026-09-06 — P1 addendum: contact sheets + TAP three-way overlap
**Contact sheets** `results/P1/qc_sheets/` (4 PNGs, 4.1 MB, all 160 chips, none dropped).
Deviation from the request: the four requested groups hold **44 / 37 / 29 / 50** chips, not 40
each, so a fixed 8x5 would have silently dropped 4 TAP and 10 DPRK chips. The grid is held at
**8 columns** and rows follow the group (6/5/4/7). Chips upscaled 2x nearest-neighbour; id and
proposed_label printed under each.
Two things the sheets show that the per-chip review did not: (i) several TAP positives
(`TAP_ASGM_009/022/024/027`) are outlines over near-intact canopy, and `TAP_ASGM_017` is a river
sandbar — exactly the commission modes the overlap table quantifies below; (ii) **a large share of
the DPRK chips read as village / terraced-agriculture terrain, not mining**, and Tang & Werner-only
polygons carry **no outline** in the chips (the chip outline was drawn from Maus v2 only, and Maus
covers just 30 of the DPRK polygons). Both strengthen the P3 recommendation that Tang & Werner is a
*frame* needing VHR adjudication, never a label.

**TAP three-way pixel-level overlap** (`results/P1/tap_overlap.txt|.json`). MapBiomas class_id is
mutually exclusive, so the three-way is a 2x3. Frame area and MapBiomas class areas are EXACT
(30 m, EE); the split of the frame across MapBiomas classes is a **design-based** estimate from the
4,000 uniformly-drawn in-frame points (Wilson 95%). Negatives were never used — they are
WorldCover-stratified, not area-representative.
| | MB garimpo | MB industrial | MB none | total |
|---|---|---|---|---|
| inside Maus x AMW frame | **493.2** (468-519) | **0.0** (0-2) | **1,411.0** (1,385-1,436) | 1,904.2 |
| outside frame | 80.6 | 4.0 | 193,939 | 194,024 |
| total | 573.8 | 4.0 | 195,350 | 195,928 |
- Our frame captures **85.9%** of all TAP MapBiomas garimpo; only 14.1% (81 km2) is missed.
- **Zero** MapBiomas-industrial area falls inside the ASGM positives — the 5 km named-mine
  exclusion works exactly as designed.
- **The 74.1% (1,411 km2) disagreement is NOT what the water/sandbar/tailings hypothesis predicted.**
  Splitting those 2,964 points on S2-2019 annual percentiles: **95.2% are VEGETATED**
  (median NDVI_p50 +0.817, NDWI_p50 -0.711 -> ~1,343 km2 of near-intact canopy), only **3.1% bare**
  (spoil/sandbar, ~44 km2) and **1.7% water** (~24 km2). So the dominant commission mode is
  **geometric dilation, not spectral ambiguity**: AMW detects on 480 m patches and Maus polygons are
  coarse hulls, so their intersection swallows forest between and around the pits. Example ids for
  each mode are in `results/P1/tap_positives_outside_mapbiomas.csv` (2,964 rows, with lon/lat).
- Consequence for P2: the ASGM positive frame should be **eroded or intersected with a
  bare / low-NDVI mask** before it is used as a label, or the reported AUC is partly a
  forest-vs-forest boundary effect. This is now the single most important open item, ahead of the
  classifier-dependence of the label-parity ratio.

## 2026-09-06 — Step A: human QC adjudication (all 160 chips)
Reviewer decisions transcribed into `results/P1/qc_table.csv` (`decision` column, previously blank)
by `code/p1_decisions.py` and documented in `results/P1/qc_decisions.md`. Every chip is now
adjudicated; the script asserts no blanks.
Purity: **TAP ASGM 32/35 (~91%)**, **MDD ASGM 13/15 (~87%)**, **GHA unclassified 13/15 (~87%)**,
negatives 30/30. Amazon uncertains are `TAP_ASGM_017` (river-bend sandbar vs dredging), `022`
(polygon mostly forest in 2019), `034` (polygon offset from mining), `MDD_ASGM_010`/`013` (natural
sandbar possible) — i.e. the failure modes are exactly the ones the pixel-level overlap predicted.
**Two results that change downstream design:**
1. **The Ghana industrial flag is unreliable from proximity alone** — only 7/15 flagged chips are
   confirmed industrial, 3/15 are outright ASM (`GHA_IND_000/001/003`, `ASM_like_flag_error`), and
   5/15 are unresolvable. A 5 km radius around a named mine does not separate LSM from galamsey
   because galamsey clusters immediately around the concessions. The Stage-3 "Ghana box contains
   Tarkwa/Obuasi therefore Ghana is contaminated by LSM" reasoning cannot be operationalised with a
   distance rule.
2. **Only 21/50 DPRK polygons (42%) show visible surface mining.** Tang & Werner as shipped is a
   candidate list, not a label set. Any future DPRK work uses only the 21 `PRK_VISIBLE` polygons.
**Negatives are clean (30/30)** — the Stage-2 caveat that unmapped ASGM in the negatives makes the
reported AUC a lower bound is not supported at this sample size.
**Chip purity (~91%) and the 74% area disagreement are consistent, not contradictory:** a chip is
scored on whether the workings are present, while the area statistic is dominated by the forest the
dilated Maus x AMW intersection sweeps up around them. The positives sit in the right places; the
frame is too fat.

## 2026-09-06 — Step B: BLOCKED, no P2 specification exists
Step B asked to "run Package TA04-P2 exactly as specified earlier". **No such specification exists**
— not in this session, not in `provenance/`, not in `PLAN.md`; `PROGRESS.md` has only
"P2 — (not started; blocked on P1 verdict)". The four parameters supplied with the request
(classifier-dependence framing; Ghana industrial rule = area >= 20 ha OR named-mine proximity AND
grey terraced texture; exclude the uncertain ids as a sensitivity arm; DPRK frame = the 21
PRK_VISIBLE polygons) are **constraints on** a package, not the package itself: they fix no
research question, no ROI/label/feature scope, no metric, no pre-registered decision rule, no
outputs, and no compute budget. Recorded and held pending the P2 scope.

## 2026-09-06 — P2 step 0 (pre-registration)
`PLAN_P2.md` written before any P2 analysis. Question: is AEF's label-parity advantage a property
of the representation or of the (representation, classifier) pair, and does it survive frame
erosion. Two arms: **U** reuses the 23,269 P1 points as is; **E** re-samples positives inside the
non-forest part of the Maus x AMW frame (NDVI(annual median) < 0.5 OR WorldCover != tree), keeping
the **same negatives** so any U->E difference is attributable to the positive frame alone. Arm E is
size-matched to Arm U at 4,000 positives/ROI so the comparison is not confounded by n. Erosion is
implemented as **rejection sampling**, which doubles as the design-based estimator of the eroded
area (acceptance rate x un-eroded area, Wilson CI). Pre-registered K1 (LightGBM ratio >= 3, CI
lower >= 2 on arm E), K2 (full-data AUC gap >= +0.03, CI excluding 0), K3 (>= 60% of
outside-MapBiomas positives non-forest/water or patches < 1 ha). K3 is recorded knowing P1 makes it
likely to FAIL (95% of that area was vegetated) — kept verbatim so the failure is on the record.
Sensitivities S1-S3 pre-registered as logistic+LightGBM only. EE budget <= 30 EECU-h, point
sampling only.
