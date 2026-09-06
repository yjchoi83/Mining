# TA04 — progress board

Topic: **How few labels does artisanal gold mining need?** (AEF label efficiency,
asymmetric cross-region transfer, negative label pooling). Stage-4 verdict:
CONDITIONAL-GO, gate = ASGM-only reference.

## Packages
- [x] **P1 — ASGM-only reference, reference purity QC, label-efficiency re-test** (complete)
- [ ] **P2 — classifier-dependence + frame erosion** (in progress; `PLAN_P2.md` pre-registered)
  - [x] P2.0 PLAN_P2.md written before any analysis
  - [x] P2.1 Arm E frame: TAP keeps 21.5% / MDD 57.1% / GHA 48.6%; eroded TAP 409 km2 ~ MapBiomas garimpo 494 km2
  - [ ] P2.2 Reference disagreement (TAP+MDD three-way + characterisation) — K3
  - [x] P2.3 Ghana industrial rule redefinition — new rule flags 342/528 (vs 78); 20 ha clause does almost all of it, texture clause adds 1
  - [ ] P2.4 Classifier grid (4 classifiers x 2 feature sets x arms U/E) — K1, K2
  - [ ] P2.5 Sensitivities S1-S3
  - [ ] P2.6 results/P2/P2_results.md
- [ ] P3 — transfer / data-denied target (DPRK recommendation comes out of P1 step 5)
- [ ] P4
- [ ] P5
- [ ] P6
- [ ] P7

## P1 steps
- [x] 0. Provenance: Stage-4 G2 + TA04 pilot scripts -> `code/upstream/`, `code/SOURCES.md`; ROI boxes reused
- [x] 1. References (Amazon ASGM-only / Ghana mixed / DPRK counts / hard negatives)
- [x] 2. Purity QC chips + `results/P1/qc_table.csv` (160 chips, 3.67 MB) + 4 contact sheets in `results/P1/qc_sheets/`
- [x] A. Human adjudication of all 160 chips — `results/P1/qc_decisions.md`; purity TAP ~91%, MDD ~87%, GHA-unclassified ~87%; Ghana industrial flag unreliable; only 21/50 DPRK polygons visible
- [x] 3. Label-efficiency re-test, Amazon ASGM-only — **SURVIVES** on the pre-registered primary (25.0, CI 9.12–25.0); LightGBM arm 2.75 fails the line
- [x] 4. Ghana mixed-label curve (transfer-only framing) — industrial and unclassified reported separately
- [x] 5. DPRK feasibility summary + P3 recommendation (detection-only; source ROI = Ghana)
- [x] 6. `results/P1/P1_results.md` (60 lines)

## Verdict
P1 ratio verdict: **SURVIVES** on the pre-registered primary (logistic, 25.0, CI 9.12–25.0)
and on the hostile strongest-baseline arm (6.56, CI 3.30–9.69) — but the capacity-matched
**LightGBM arm is 2.75 (CI 1.69–3.82), below the pre-registered line of 3**. Stage 4's 19.9x
was a LightGBM number, so the multiple is classifier-dependent and P2 must lead with that.
Open reference question for P2: MapBiomas confirms only 25.9% of our ASGM positives as garimpo, and
the 74% remainder is **95% vegetated**, not water/sandbar — i.e. the frame is geometrically dilated
(AMW 480 m patches x coarse Maus hulls), so P2 must erode/mask the positive frame before training.
