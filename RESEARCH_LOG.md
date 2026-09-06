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
