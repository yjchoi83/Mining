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
