# TA04-P2 results — classifier-dependence and frame erosion

**Answer: the label-parity advantage is a property of the (representation, classifier) pair, not of the representation alone, and it does not survive frame erosion for capacity learners.**

## 1. Classifier-dependence — label-parity ratio (AEF64 vs BASE74, same classifier, k_ref=40)
| task | arm | logistic | kNN-15 cos | LightGBM | MLP 2x128 |
|---|---|---|---|---|---|
| **Amazon ASGM (primary)** | U | 29.803 | 3.625 | **2.745** (1.693–3.824) | 2.664 |
|  | E | 3.726 | 3.402 | **1.545** (1.044–1.772) | 0.619 |
| Ghana industrial* | U | 13.951 | 2.265 | **3.686** (1.634–7.823) | 0.793 |
|  | E | 5.241 | 2.795 | **2.307** (1.39–4.039) | 0.55 |
| Ghana unclassified* | U | 50.0 | 6.975 | **3.429** (0.8–7.787) | 0.915 |
|  | E | 5.241 | 2.795 | **2.307** (1.39–4.039) | 0.55 |
Ratios are censored at 2000/40 = 50. *Ghana Arm E positives are drawn from the whole Ghana frame and are **not** split by the industrial flag, so the two Ghana Arm-E rows are the same run reported twice; only the Arm-U rows carry the split.

Full-data AUC, Amazon (AEF64 / BASE74): logistic U 0.9528/0.8569, E 0.9751/0.9281; kNN-15 cos U 0.963/0.8928, E 0.9803/0.9428; LightGBM U 0.9595/0.9086, E 0.9773/0.9457; MLP 2x128 U 0.9863/0.9272, E 0.9934/0.9687

**Reading.** On the un-eroded frame the huge multiple is a *linear-probe* artefact: logistic 29.803 vs LightGBM 2.745 and MLP 2.664 on the same data. Erosion then collapses every arm — logistic 29.803 → 3.726, LightGBM 2.745 → 1.545, MLP 2.664 → 0.619 (below 1: the baseline reaches AEF's 40-label AUC with *fewer* than 40 labels). Only the two **representation-level probes** (linear, cosine-kNN) still clear 3 on arm E. Most of the apparent label efficiency was the dilated positive frame, not the embedding.

## 2. Pre-registered criteria
- **K1 (practical label efficiency): FAIL.** LightGBM-vs-LightGBM on arm E = **1.545** (CI 1.044–1.772), needs ≥3 with CI lower ≥2. Per PLAN_P2 §1.6 the paper may therefore claim only **representation-level** efficiency plus the classifier-dependence finding, and **must not claim practical label savings**.
- **K2 (information gain): PASS.** Full-data AEF−BASE74 gap under LightGBM on arm E = **+0.0316** (CI 0.0218–0.0403), needs ≥+0.03 with CI excluding 0. Passes, but only just: the point estimate sits 0.002 above the line.
- **K3 (disagreement explained): FAIL.** 7.6% (CI 6.7–8.6%) of outside-MapBiomas positives are non-forest/water or in patches <1 ha, needs ≥60% → **reference uncertainty is flagged**, not resolved.

## 3. Frame erosion and reference disagreement
| ROI | un-eroded km² | eroded km² | kept % (95% CI) |
|---|---|---|---|
| TAP | 1,904.2 | **409.4** | 21.5 (20.9–22.1) |
| MDD | 814.0 | **465.2** | 57.1 (56.4–57.9) |
| GHA | 1,777.2 | **864.1** | 48.6 (47.9–49.4) |
**The Tapajós frame is 78.5% forest.** The eroded TAP frame (409 km²) now agrees to ~20% with the independent MapBiomas garimpo estimate (494 km² in-frame, 574 km² box-wide), where the un-eroded frame was 3.3× too big — two methods sharing no inputs converging once the dilation is removed.
Three-way pixel table, TAP (design-based, n=4,000 in-frame points): inside the frame **493.19 km² MapBiomas garimpo / 0.0 industrial / 1411.01 none**. Of the 2964 outside-MapBiomas positives, 92.4% are forest, **0.0% are in patches <1 ha**, but **53.1% lie within 100 m of mapped mining** — the dilation signature, reported post-hoc because the pre-registered K3 proxy (patch size) was the wrong instrument for a frame made of large blobs.
**MDD has no MapBiomas coverage at all** (Brazil-only asset, Peru ROI), so half the primary Amazon ROI has no independent reference.

## 4. Sensitivities
- **S1 exclude uncertain (arm E):** logistic 4.188 (3.188–16.915), LightGBM 1.581 (1.147–2.09); n=14710.
- **S2 landscape-proportional negatives (arm U):** logistic 42.499 (6.819–50.0), LightGBM 1.829 (1.004–1.914); n=15269.
- **S2 landscape-proportional negatives (arm E):** logistic 7.073 (2.854–9.885), LightGBM 1.09 (0.901–1.536); n=14709.
- **S2 strengthens the conclusion, it does not rescue it:** with landscape-proportional (94% tree-cover) negatives the task gets easier for both feature sets and the capacity-matched LightGBM ratio falls further, to 1.83 on arm U and **1.09** on arm E. The near-equal-per-class negatives used in the main analysis are therefore the *harder*, more conservative choice.
- **S1 is structurally uninformative** and is reported as such: the `uncertain` chips sit in 33–50 ha frame parts (0.02–0.03% of the frame), so excluding them removes 0–2 sampled points. A real label-uncertainty sensitivity needs a much larger adjudicated chip set (P3).
- **S3 Ghana industrial rule:** the new rule flags **342/528** polygons industrial vs **78** under the old 5 km rule; **344** come from the `area ≥ 20 ha` clause and only **1** from `2 km + grey terraced texture`. Maus v2 hulls aggregate many small ASM pits, so 20 ha is not a usable LSM threshold — this contradicts the P1 chip adjudication and should be replaced by compactness/texture in P3.

**EE budget:** point sampling only — 48k cheap 3-band screening points, 15.4k full 138-band points, ~12k WorldCover points, plus one 30 m distance-transform sampling. No image exports, well inside the 30 EECU-hour ceiling.

**P3 (transfer) is not started.**
