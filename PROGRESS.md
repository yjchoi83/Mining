# TA04 — progress board

Topic: **How few labels does artisanal gold mining need?** (AEF label efficiency,
asymmetric cross-region transfer, negative label pooling). Stage-4 verdict:
CONDITIONAL-GO, gate = ASGM-only reference.

## Packages
- [x] **P1 — ASGM-only reference, reference purity QC, label-efficiency re-test** (complete)
- [x] **P2 — classifier-dependence + frame erosion** (complete)
  - [x] P2.0 PLAN_P2.md written before any analysis
  - [x] P2.1 Arm E frame: TAP keeps 21.5% / MDD 57.1% / GHA 48.6%; eroded TAP 409 km2 ~ MapBiomas garimpo 494 km2
  - [x] P2.2 Reference disagreement — **K3 FAILS (7.6%, CI 6.7-8.6)**; MDD has no MapBiomas coverage; 53% of outside-MB positives within 100 m of mapped mining (post-hoc)
  - [x] P2.3 Ghana industrial rule redefinition — new rule flags 342/528 (vs 78); 20 ha clause does almost all of it, texture clause adds 1
  - [x] P2.4 Classifier grid — **K1 FAILS** (LightGBM arm E 1.55, CI 1.04-1.77); **K2 passes narrowly** (+0.032)
  - [x] P2.5 Sensitivities S1-S3 (S2 lowers the LightGBM ratio further to 1.09; S1 uninformative; S3 exposes the 20 ha clause)
  - [x] P2.6 `results/P2/P2_results.md` (45 lines)
- [ ] P3 — transfer / data-denied target. **Carry-ins:** claim representation-level efficiency only (K1 failed);
  erode the positive frame before training; MDD has no independent reference; replace the Ghana 20 ha clause;
  DPRK evaluation frame = the 21 PRK_VISIBLE polygons only.
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
