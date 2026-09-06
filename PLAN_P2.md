# TA04-P2 — PLAN (pre-registered)

Written 2026-09-06 **before any P2 analysis was run**, from the specification issued after P1.
Repository: `Mining` only. Upstream: `PLAN.md`, `RESEARCH_LOG.md`, `results/P1/`.

## 0. Research question
**Is the label-parity advantage of AEF a property of the representation itself, or of the
(representation, classifier) pair — and does it survive erosion of the positive frame?**

P1 forced this question. The pre-registered primary (logistic) gave a right-censored ratio of
**25.0** (CI 9.12–25.0) while the capacity-matched **LightGBM arm gave 2.75** (CI 1.69–3.82),
*below* P1's own falsification line; Stage 4's headline 19.9× was a LightGBM number. Separately the
P1 pixel overlap showed **74.1%** of the Amazon positive frame is outside any MapBiomas mining and
**95%** of that area is vegetated — the frame is geometrically dilated (AMW 480 m patches × coarse
Maus hulls). P2 varies the classifier and the frame and reports both axes side by side.

## 1. Fixed decisions (pre-registered; any change after seeing results is logged with a reason)

### 1.1 Arms
- **Arm U (un-eroded).** The existing P1 sample, reused **as is**: 23,269 points
  (TAP 8,000 / MDD 7,271 / GHA 7,998), AEF-2019 64 bands + the Stage-4 G2 74 classical features.
- **Arm E (eroded).** Positive frame = Maus v2 × AMW pixels that are **NOT forest in 2019**:
  `NDVI(S2-2019 annual median) < 0.5` **OR** `ESA WorldCover 2020 != 10 (tree cover)`.
  NDVI is computed from the **annual-median bands** already in the 74-feature stack,
  `(B8_p50 − B4_p50)/(B8_p50 + B4_p50)`, so Arm E uses the identical composite as Arm U.
  Ghana has no AMW component, so its frame is Maus v2 only; the same non-forest rule applies.
  **Negatives are unchanged** — Arm E swaps positives only, so any U→E difference is attributable
  to the positive frame and nothing else.

### 1.2 Arm E sampling (rejection sampling — also the area estimator)
1. Draw **16,000** uniform candidate points inside each ROI's un-eroded positive frame (shapely).
2. Screen them in Earth Engine with a **cheap 3-band stack** (WorldCover `Map`, S2-2019 annual
   median `B4`,`B8`).
3. **Acceptance rate = eroded share of the frame.** Eroded area = acceptance × un-eroded area,
   with a Wilson 95% interval. This is a design-based estimate, not a raster intersection; it is
   stated as such.
4. Sample the full 138-band stack at up to **4,000** accepted points per ROI (≤ 10k as specified;
   4,000 matches Arm U exactly so the two arms are size-matched and the comparison is not
   confounded by n).

### 1.3 Reference-disagreement analysis (TAP **and** MDD)
Three-way pixel table Maus×AMW / MapBiomas garimpo / MapBiomas industrial, as in P1 but for both
Amazon ROIs. MapBiomas covers Brazil only, so **MDD is expected to be entirely outside its
footprint**; that is reported as a coverage fact, not a disagreement. Positives falling outside
MapBiomas mining are characterised by:
- **NDVI class** — `water` (NDWI_p50 > 0), `bare` (NDVI < 0.5, not water), `forest` (NDVI ≥ 0.5);
- **patch size** — area of the connected component of the Maus×AMW positive frame containing the
  point (slivers are intersection/registration artefacts);
- **distance to MapBiomas mining** — `fastDistanceTransform` on the MapBiomas mining mask at 30 m.

### 1.4 Ghana (secondary, transfer-only)
Industrial flag **redefined**: `area >= 20 ha` **OR** (`within 2 km of a named mine` **AND**
`grey terraced texture`). "Grey terraced texture" is operationalised at polygon level from the
sampled points, pre-registered here as: polygon-median **`NDVI_p50 < 0.35`** (grey/bare) **AND**
polygon-median **`B8_sd7` above the median of all Ghana positive polygons** (terraced relief).
`GHA_IND_000/001/003` are **reassigned to ASM-like** per the P1 adjudication regardless of what the
rule returns; the reassignment is applied to the Maus polygons those chips sit in.

### 1.5 Feature sets, classifiers, protocol
- Feature sets: **AEF64** vs **BASE74** (Stage-4 G2 features), on every classifier.
- Classifiers, run on **both** feature sets:
  1. **logistic** — standardised, `class_weight='balanced'`;
  2. **LightGBM** — the Stage-4 G2 configuration verbatim;
  3. **kNN k=15, cosine** — raw AEF64; **standardised** BASE74;
  4. **MLP 2×128** — standardised, `adam`, `early_stopping`.
- Budgets **{10, 20, 40, 80, 160, 320, 640, 1000, 2000}**, **20 draws** each, class-ratio
  preserving, ≥4 per class.
- **5-fold GroupKFold on 0.5° blocks**; metric **ROC-AUC**.
- **Block bootstrap, 1,000 draws**, resampling 0.5° blocks **with multiplicity**.
- **Label-parity ratio** = (BASE74 labels to reach the AEF AUC at k=40) / 40, per classifier, per
  arm; right-censored at 2000/40 = **50** when the baseline never reaches it.

### 1.6 PRE-REGISTERED CRITERIA
- **K1 (practical label efficiency).** Capacity-matched **LightGBM-vs-LightGBM** ratio on **arm E**
  **≥ 3** with **CI lower ≥ 2**.
  *If K1 fails, the paper claims only **representation-level** (linear/kNN) efficiency plus the
  classifier-dependence finding, and does **NOT** claim practical label savings.*
- **K2 (information gain).** Full-data AUC gap **AEF − BASE74 under LightGBM on arm E ≥ +0.03**,
  with a block-bootstrap CI **excluding 0**.
- **K3 (reference disagreement explained).** **≥ 60%** of Maus×AMW positives outside MapBiomas
  mining are **non-forest/water** or in **patches < 1 ha** → disagreement attributed to frame
  dilation. *Otherwise flag reference uncertainty in the results.*
  (P1's numbers make failure likely — 95% of that area was vegetated. K3 is retained exactly as
  specified so the failure is on the record rather than rationalised away.)

### 1.7 Sensitivities
- **S1** exclude the `uncertain` ids from `results/P1/qc_decisions.md` (the Maus polygons those
  chips sit in): TAP 017/022/034, MDD 010/013, GHA_IND 009–013, GHA_UNC 011/012.
- **S2** stratified vs **landscape-proportional** negatives. Landscape proportions are estimated
  from a fresh uniform WorldCover sample inside each negative frame; the existing negatives are
  then resampled to those proportions.
- **S3** Ghana **old** (5 km proximity) vs **new** (§1.4) industrial rule.
Sensitivities run **logistic + LightGBM only**, to keep the run inside budget; that restriction is
pre-registered, not chosen after seeing results.

### 1.8 Budget
Earth Engine **≤ 30 EECU-hours**, **point sampling only** — no image exports, no thumbnails.
Planned EE work: 48k cheap 3-band screening points, ≤12k full 138-band points, ~12k WorldCover
points for S2, and point sampling of the MapBiomas distance transform. This is below the P1 run.

## 2. What P2 does not settle
- Arm E removes forest from the *positive* frame; it does not fix AMW's 480 m detection footprint.
- MapBiomas is Landsat-derived and Brazil-only, so it cannot adjudicate MDD at all.
- The 0.5° blocks and single year (2019) are unchanged from P1; no transfer is measured here.
- Ghana remains **transfer-only**: no ASGM claim rests on it.

## 3. Outputs
`PLAN_P2.md`, `code/p2_*.py`, `results/P2/P2_results.md` (≤ 60 lines: classifier-dependence table
first, then K1–K3 verdicts, then the reference-disagreement table, then sensitivities),
`results/P2/*.csv`, `PROGRESS.md`. Per step: a `RESEARCH_LOG.md` line, `PROGRESS.md` update, then
`git add . && git commit && git pull --rebase && git push`. **P3 (transfer) is not started.**
