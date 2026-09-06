# TA04-P1 — PLAN (pre-registered)

Package: **ASGM-only reference, reference purity QC, label-efficiency re-test.**
Written 2026-09-06, before any P1 analysis was run. Repository: `Mining` only.
Upstream provenance: `provenance/stage2_TA04.md`, `provenance/stage3_TA04.md`,
`provenance/stage4_SUMMARY.md` (Stage 4 restated the Stage-2 "25-40x" claim as
**AMZ 19.9x (CI 17.3-22.4) / GHA 15.7x (12.8-19.5)** against a 74-feature
classical + LightGBM baseline; pre-registered falsification line was ratio < 3).

## 0. Why this package exists

Stage-3 threat (a) is binding: `global_mining_polygons` does not separate ASGM
from large-scale mining (LSM), and the Ghana box contains Tarkwa/Obuasi. The
Stage-4 label-parity multiple may therefore be an **LSM-contamination artefact**.
P1 rebuilds the Amazon reference as **ASGM-only** and re-runs the label-efficiency
test on it. Ghana stays **mixed** and is reported **transfer-only**, not as
evidence for the headline. DPRK is **feasibility only** — no training.

## 1. Fixed decisions (pre-registered; changing any of these after seeing results
   must be logged in RESEARCH_LOG.md with a reason)

### 1.1 ROI boxes
| ROI | lon/lat box | provenance |
|---|---|---|
| `TAP` Tapajos | -58.0, -8.0, -54.0, -4.0 | Stage-2/4 `AMZ` box, reused verbatim |
| `GHA` Ghana SW | -3.2, 4.9, -0.9, 7.2 | Stage-2/4 `GHA` box, reused verbatim |
| `MDD` Madre de Dios | -71.0, -13.4, -69.4, -12.0 | **new in P1** — Stage 2/4 never
  instantiated a MDD box (Stage 3 names the region only). Chosen to cover
  Huepetuhe / Delta-1 / La Pampa along the Interoceanic highway. Flagged as a
  P1 deviation, not a reuse. |

### 1.2 Reference sources (verified in-session before PLAN was finalised)
- **Maus.** The GEE asset `projects/sat-io/open-datasets/global-mining/global_mining_polygons`
  returns **21,060 polygons / 57,278 km2 globally** = **Maus v1 (2020, Sci Data 7:289)**,
  NOT v2. Stage 2/3/4 all assumed v2. P1 therefore downloads **Maus v2** from
  PANGAEA (`https://download.pangaea.de/dataset/942325/files/global_mining_polygons_v2.gpkg`,
  HTTP 200, 24.66 MB, doi 10.1594/PANGAEA.942325, expected 44,929 polygons /
  101,583 km2) and uses v2 as the frame. v1 counts are reported alongside as a
  provenance correction.
- **Amazon Mining Watch (ASGM).** `earthrise-media/mining-detector`
  `data/outputs/48px_v3.2-3.7ensemble/amazon_basin_48px_v3.2-3.7ensemble_0.50_<Y>-01-01_<Y>-12-31-dissolved-0.6.geojson`
  for Y in {2019, 2020} (5.7 / 6.0 MB, verified present via GitHub API).
  Mirror of record: `https://data.source.coop/earthgenome/amazon-mining-watch/`.
- **MapBiomas mining.** `projects/mapbiomas-public/assets/brazil/lulc/collection10/mapbiomas_brazil_collection10_mining_substances_v3`
  loads, bands `classification_1985..2024`. P1 will test whether the 2019 band's
  `class_id` values separate garimpo from industrial inside the TAP box; if yes it
  becomes a **third Amazon source** and source agreement is reported (TAP only).
- **Tang & Werner.** `projects/sat-io/open-datasets/global-mining/global_mining_footprints`,
  74,548 polygons globally, props include `Name`, `Shape_Area`. DPRK counts only.
- **Negatives / stratification.** `ESA/WorldCover/v100/2020` (`Map`).

### 1.3 Amazon ASGM-only positive definition (pre-registered)
A polygon enters the Amazon positive set iff **all** hold:
1. it is a Maus v2 polygon whose centroid lies in the TAP or MDD box;
2. it **intersects** an AMW 2019 or 2020 detection footprint (AMW is a
   Sentinel-2 CNN ASGM detector -> the intersection is the ASGM filter);
3. its centroid is **>= 5 km** from every named industrial mine in
   `data/industrial_mines.csv` (compiled from public sources in P1 and committed).
Rationale for (3): AMW fires on some LSM tailings/pits too, so intersection alone
does not exclude industrial. The 5 km radius is the same buffer used for Ghana.

### 1.4 Ghana positive definition (mixed; transfer-only)
All Maus v2 polygons with centroid in the GHA box. Each is flagged
`industrial` if its centroid is within 5 km of a named large-scale mine
(Tarkwa, Obuasi, Damang, Iduapriem, Ahafo, Akyem + any further verified in P1),
else `unclassified`. **No claim about ASGM label efficiency is made from Ghana.**

### 1.5 Negatives (both regions)
Background points **>= 1 km from any mining polygon** (Maus v2 union, plus AMW
union in the Amazon), sampled inside the same ROI, **stratified by ESA
WorldCover 2020 class**, with bare/sparse (60), herbaceous+shrub (20/30),
built-up (50), permanent water (80) and cropland (40) forced to be represented
so that **bare soil, river sandbars and built-up are hard negatives**, alongside
tree cover (10). Equal quota per available class, remainder to tree cover.

### 1.6 Sampling and features
- AEF: `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` **2019**, 64 bands, 10 m.
- Baseline: the **same 74 classical features** as Stage-4 G2
  (S2_SR_HARMONIZED 2019 11-var x 5 percentiles = 55; 4 intra-annual stdDev;
  5 focal-texture; S1_GRD VV/VH 3 percentiles = 6; 2 stdDev; VV-VH ratio; VV_sd3
  = 74), sampled at the **same points** in one `sampleRegions` stack.
- <= 10,000 points per class per ROI; chunked `sampleRegions` (150 pts/chunk),
  `tileScale=8`. **No image exports.** EE budget <= 25 EECU-h.

### 1.7 Label-efficiency protocol (pre-registered)
- Label budgets **k in {10, 20, 40, 80, 160, 320, 640, 1000}**.
- **20 repeated draws** per k, class-ratio-preserving, min 4 per class.
- **Spatial-block CV with 0.5-degree blocks** (`GroupKFold`, 5 splits; coarser
  than Stage-2/4's 0.1 deg -> a stricter, more conservative test).
- Metric **ROC-AUC** on the held-out block fold.
- Models: AEF-64 and BASE-74, each with LogisticRegression (standardised,
  class-balanced) as primary and LightGBM as the capacity-matched arm.
  Primary comparison = **same classifier both sides**.
- **Label-parity ratio** = (baseline labels needed to reach the AEF AUC at k=40)
  / 40, by log-linear interpolation of the baseline curve; if the baseline never
  reaches that AUC within k<=1000 the ratio is reported as **> 1000/40 = 25
  (right-censored)** and treated as passing.
- **CIs: block bootstrap, 1,000 draws**, resampling **0.5-deg blocks** (not
  individual draws) so spatial dependence is respected.
- Also report **full-data AUC** for both feature sets.

### 1.8 PRE-REGISTERED DECISION RULE (falsification line, from Stage 4)
Let `R` = Amazon ASGM-only label-parity ratio, with block-bootstrap 95% CI.

> **The paper's claim survives iff `R >= 3` AND `CI_lower >= 2`.**
> **If `R < 3`: write the results, mark the package KILLED, and STOP.**

If `R >= 3` but `CI_lower < 2`, the package is **WOUNDED**: results are written,
no kill, and P2 must not start until the CI is tightened. In all cases **P2 is
not started in this package.**

### 1.9 QC chips (step 2)
Sentinel-2 2019 annual-median RGB (B4/B3/B2), **1 x 1 km at 10 m**, polygon
outline drawn, `getThumbURL` only (no export), saved to
`results/P1/qc_chips/<id>.png`:
- 50 Amazon ASGM positives, stratified across TAP and MDD;
- 30 Ghana positives = 15 industrial-flagged + 15 unclassified;
- all DPRK polygons, capped at 50;
- 30 hard negatives.
Total 160 chips. `results/P1/qc_table.csv` columns exactly:
`id, region, source, proposed_label, decision, notes` with `decision` **blank**
(human adjudication is a later package). If the chip directory exceeds
**15 MB**, chips move to `data/qc_chips/` (gitignored) and only the table is
committed; this is decided by measurement, not preference.

### 1.10 DPRK (feasibility only)
Count Tang & Werner and Maus v2 polygons inside North Korea, list the **20
largest with coordinates**, and `WebFetch` `irenk.sonosa.or.kr` to report what it
actually provides. **No DPRK training in this package.**

## 2. Threats P1 does not fix (stated up front)
- AMW is Sentinel-2-derived, so it shares lineage with the S2 half of the 74
  baseline. This biases **against** our claim (baseline sees the label's own
  sensor) -> conservative.
- Maus v2 is a single ~2019 cumulative epoch with no year attribute.
- Negatives may still contain unmapped ASGM -> reported AUC is a lower bound.
- MDD box is new, so MDD is not a Stage-4 replication.
- `decision` in `qc_table.csv` is left blank: P1 delivers the QC instrument, not
  the adjudicated purity rate.

## 3. Step order and commit discipline
Steps 0-5 as issued. After each numbered step: append one line to
`RESEARCH_LOG.md`, update `PROGRESS.md`, then
`git add . && git commit && git pull --rebase && git push`.

## 4. Outputs
`PLAN.md`, `code/` (+ `code/SOURCES.md`), `results/P1/P1_results.md` (<= 60 lines),
`results/P1/qc_table.csv`, `RESEARCH_LOG.md`, `PROGRESS.md`.
