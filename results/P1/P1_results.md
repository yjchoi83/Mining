# TA04-P1 results — ASGM-only reference, purity QC, label-efficiency re-test

Verdict (pre-registered, PLAN §1.8): **SURVIVES** (ratio 25.0 >= 3, CI lower 9.119 >= 2)

## 1. References
| ROI | Maus v2 polys | AMW-intersecting | dropped <5 km of named industrial | positives | positive frame km² |
|---|---|---|---|---|---|
| TAP | 623 | 570 | 13 | 557 | 1904 |
| MDD | 5 | 1 | 0 | 1 | 814 |
| GHA (mixed, transfer-only) | 528 | n/a | n/a | 78 industrial / 450 unclassified | 1777 |

Sources: **Maus v2** PANGAEA doi 10.1594/PANGAEA.942325 (44,929 polys / 101,583 km² — the GEE `global_mining_polygons` asset used by Stage 2/4 is **v1**: 21,060 / 57,278). **AMW** `earthrise-media/mining-detector` `48px_v3.2-3.7ensemble` 2019 (5,751 feats) + 2020 (6,110). 20 named industrial mines in `data/industrial_mines.csv` (Wikidata P625; SEC/NI 43-101 for Tocantinzinho, Palito, São Chico). Negatives ≥1 km from any mining polygon, ESA WorldCover-stratified.

**MapBiomas separates garimpo: YES** (ATBD C10 Table 3: 1xx industrial, 2xx garimpo, 215 garimpo gold). TAP 2019 at 30 m: garimpo 573.81 km² (gold 563.52), industrial 4.0 km² — Tapajós is ~99% garimpo by area.
**Source agreement (TAP sample points):** 25.9% of our ASGM positives are MapBiomas garimpo, 0.0% MapBiomas industrial; 0.25% of our negatives are any MapBiomas mining. MapBiomas is 3.3× smaller than the Maus×AMW frame — the largest reference disagreement found.

## 2. Purity QC chips
160/160 chips written (3.7 MB, committed), S2-2019 annual-median RGB, 1×1 km @10 m, polygon outline burnt in; `decision` left blank in `qc_table.csv` for human adjudication. Inventory: GHA industrial 15, GHA mining, unclassified 15, GHA not mining 14, MDD ASGM 15, MDD not mining 7, PRK mining, unclassified (data-denied) 50, TAP ASGM 35, TAP not mining 9.

## 3. Label efficiency — Amazon ASGM-only (TAP+MDD), 0.5° block CV, 20 draws/budget, AUC
| Amazon ASGM-only — n=15271, pos=8000, blocks=79, 74 baseline feats | 10 | 20 | 40 | 80 | 160 | 320 | 640 | 1000 | full |
|---|---|---|---|---|---|---|---|---|---|
| AEF64_log | 0.701 | 0.772 | 0.840 | 0.875 | 0.905 | 0.925 | 0.936 | 0.942 | 0.953 |
| BASE74_log | 0.593 | 0.661 | 0.697 | 0.748 | 0.783 | 0.809 | 0.831 | 0.838 | 0.857 |
| AEF64_lgbm | 0.579 | 0.725 | 0.793 | 0.850 | 0.893 | 0.919 | 0.938 | 0.945 | 0.960 |
| BASE74_lgbm | 0.525 | 0.651 | 0.711 | 0.772 | 0.818 | 0.849 | 0.875 | 0.885 | 0.909 |

| arm | ratio | 95% CI (block bootstrap, 1000 draws over 0.5° blocks) | ≥3 & CI≥2 |
|---|---|---|---|
| logistic — **PRE-REGISTERED PRIMARY** | 25.0 (censored_at_1000) | 9.119 – 25.0 | ✅ |
| LightGBM — capacity-matched | 2.745 (interpolated) | 1.693 – 3.824 | ❌ |
| strongest-baseline — post-hoc, hostile to us | 6.56 (interpolated) | 3.298 – 9.693 | ✅ |
- AEF AUC at the 40-label reference budget: logistic 0.84, LightGBM 0.7931. **The pre-registered primary passes and the hostile arm passes, but the capacity-matched LightGBM arm (2.745, CI 1.693–3.824) falls BELOW the falsification line.** Stage 4 reported 19.9× (17.3–22.4) on a *LightGBM* baseline; on the ASGM-only reference with 0.5° blocks that same arm collapses to 2.745. The headline multiple is a linear-probe phenomenon: with trees, AEF at 40 labels is only 0.793 and the 74-feature baseline catches it by ~110 labels. Any P2 claim must lead with the classifier-dependence, not with 25×.
- Pre-registered rule: survives iff ratio ≥ 3 **and** CI lower ≥ 2. → **SURVIVES** (ratio 25.0 >= 3, CI lower 9.119 >= 2)

## 4. Ghana (mixed reference, transfer-only framing — not evidence for the ASGM claim)
| Ghana positives (n=5,998, 36 blocks each) | arm | 10 | 40 | 160 | 1000 | full | ratio log | ratio lgbm | ratio best |
|---|---|---|---|---|---|---|---|---|---|
| industrial-flagged | AEF64_log | 0.737 | 0.864 | 0.930 | 0.954 | 0.955 | 23.53 (3.789–25.0) | 3.584 (1.748–5.51) | 8.493 (2.679–18.023) |
|  | BASE74_log | 0.689 | 0.754 | 0.818 | 0.864 | 0.873 |  |  |  |
|  | AEF64_lgbm | 0.600 | 0.822 | 0.912 | 0.953 | 0.963 |  |  |  |
|  | BASE74_lgbm | 0.509 | 0.745 | 0.829 | 0.893 | 0.909 |  |  |  |
| unclassified | AEF64_log | 0.722 | 0.883 | 0.952 | 0.973 | 0.977 | 25.0 (9.533–25.0) | 3.403 (1.54–15.053) | 22.402 (8.719–25.0) |
|  | BASE74_log | 0.669 | 0.779 | 0.834 | 0.876 | 0.888 |  |  |  |
|  | AEF64_lgbm | 0.572 | 0.817 | 0.919 | 0.958 | 0.967 |  |  |  |
|  | BASE74_lgbm | 0.529 | 0.741 | 0.825 | 0.886 | 0.902 |  |  |  |
Ghana reproduces the Amazon pattern exactly, including the LightGBM collapse (3.58 / 3.40), so the classifier-dependence is not an Amazon artefact. Unclassified positives are *easier* than industrial-flagged ones (AEF full 0.977 vs 0.955), i.e. the Stage-2 'Ghana is easier' result is not driven by large-scale mines. **Transfer-only: no ASGM claim rests on Ghana.**

## 5. DPRK feasibility (no training in P1)
- Tang & Werner `global_mining_footprints` inside the LSIB DPRK boundary: **328** polygons, 46.0 km² total; median 0.017 km², 262 below 0.1 km², only 7 at or above 1 km².
- Maus v2 inside DPRK: **30** polygons, 24.6 km² — Maus effectively does not map DPRK. Top-20 with coordinates in `results/P1/dprk_polygons.csv`.
- **Minerals are not attributable.** The only `Name` values on DPRK Tang & Werner polygons are ['2', 'Placemark', '未命名多边形'] (i.e. '2', 'Placemark', 'unnamed polygon'). `irenk.sonosa.or.kr` (I-RENK) provides commodity distribution *maps* for 13 minerals plus reserves/production 2014–2021 and DPRK–China trade statistics, but **no per-mine names with coordinates and no downloadable geodatabase**.
- **P3 recommendation:** treat DPRK as a *detection* transfer target only, never a commodity-attribution target. Source ROI should be **Ghana** rather than the Amazon: DPRK footprints are small (median 1.7 ha), hard-rock and non-forest, which is far closer to Ghana's mixed hard-rock/LSM signature than to Amazonian alluvial garimpo. Reference for P3 = Tang & Werner (the only source with usable DPRK coverage), used as a *frame* only, with VHR adjudication of a sample — its DPRK polygons carry no attributes at all.

## 6. Deviations from PLAN
- **§1.3 tightened:** positives are the *pixel-level* Maus v2 ∩ AMW intersection, not whole intersecting polygons. Maus v2 stores the entire Madre de Dios belt as one 2,536 km² polygon of which only 814 km² is AMW-confirmed. Purity-increasing only; it can never add a positive.
- **§1.5 tightened:** negatives are drawn by EE WorldCover-stratified sampling, not uniform local sampling — uniform sampling gave 10 bare / 2 built-up points per 16,000 in Tapajós. Negatives are now near-equal across land-cover classes, which makes the task harder than a landscape-proportional draw (conservative).
- **§1.1:** the Madre de Dios box is new in P1 (Stage 2/4 never instantiated one). The block bootstrap reuses 8 of the 20 subsample draws per iteration; CI width is driven by block resampling.

**P2 is not started.**
