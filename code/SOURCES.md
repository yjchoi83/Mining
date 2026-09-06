# code/upstream — provenance

Copied verbatim (no edits) on 2026-09-06 from
`/d/yj_projects/workspace_yj/Alphaearth/aef_explore/scratch/`.
That directory is the Stage 2 / Stage 4 AEF-exploration scratch space and is
**not** part of this repository; nothing in `Mining` is ever committed back to it.

| file in `code/upstream/` | original path | md5 | role |
|---|---|---|---|
| `G2_sample.py` | `.../scratch/G2_sample.py` | `63f317e2ec5b66a1a467e4402f28152c` | **Stage-4 G2 74-feature baseline sampler.** Builds the strong classical baseline stack (S2 percentiles 55 + intra-annual stdDev 4 + focal texture 5 + S1 percentiles 6 + S1 stdDev 2 + VV-VH ratio 1 + VV_sd3 1 = **74**) and AEF-64 at the same stratified points. Source of the 74-feature definition reused in P1. |
| `G2_analysis.py` | `.../scratch/G2_analysis.py` | `01903192e7d82c509328df51b76ba6c0` | **Stage-4 G2 LightGBM baseline analysis.** Label-efficiency curves, `interp_labels` log-linear parity interpolation, `bootstrap_ratio`. Produced the restated multiples AMZ 19.9x (17.3-22.4) / GHA 15.7x (12.8-19.5). P1 reuses the parity-interpolation logic but replaces the CI with a **block** bootstrap over 0.5-deg blocks. |
| `TA04_p1.py` | `.../scratch/TA04_p1.py` | `9d7931c694e0570f6a2cfdd01519c92f` | Stage-2 TA04 pilot sampler. **Source of the ROI boxes** `AMZ = [-58,-8,-54,-4]`, `GHA = [-3.2,4.9,-0.9,7.2]` reused verbatim in P1 (as `TAP`, `GHA`), and of the Maus/Hansen label construction. |
| `TA04_p1b.py` | `.../scratch/TA04_p1b.py` | `ad0d68951b318f9ca7495b60af8c1c50` | Stage-2 TA04 annulus-based resampler (GEE restricted-mode workaround). |
| `TA04_p2.py` | `.../scratch/TA04_p2.py` | `4158172ab182ebc6d8bd74580f2f5513` | Stage-2 TA04 label-efficiency + transfer + retrieval analysis (the original "25-40x" numbers). |
| `TA04_p3.py` | `.../scratch/TA04_p3.py` | `01b87e334a21bcc2a13ebe5011acf373` | Stage-2 TA04 z-score / few-shot / negative-pooling analysis. |
| `aefkit.py` | `.../scratch/aefkit.py` | `22202c256ebf813243111896f74e1047` | Shared Stage-2 GEE helpers. Carries the two gotchas P1 honours: label rasters must be `.unmask(0)` before `sampleRegions`, and mosaics have no fixed projection so `img.sample(numPixels=)` under-returns. |

## ROI boxes reused
- `TAP` (Tapajos) `[-58.0, -8.0, -54.0, -4.0]` — from `TA04_p1.py` / `G2_sample.py` `ROIS['AMZ']`.
- `GHA` (Ghana SW) `[-3.2, 4.9, -0.9, 7.2]` — from `TA04_p1.py` / `G2_sample.py` `ROIS['GHA']`.
- `MDD` (Madre de Dios) `[-71.0, -13.4, -69.4, -12.0]` — **not** present upstream. Stage 3 names Madre de Dios as a planned region but no box was ever instantiated in Stage 2 or Stage 4. This box is new in P1 and is flagged as such in `PLAN.md` §1.1.

## Provenance correction found while doing this
`G2_sample.py` and `TA04_p1.py` both read
`projects/sat-io/open-datasets/global-mining/global_mining_polygons` and Stage 2/3/4
describe it as "Maus v2 (10.1038/s41597-022-01547-4)". Measured in-session:
**21,060 polygons, 57,277.7 km2** — that is **Maus v1** (Maus et al. 2020,
Sci Data 7:289). Maus v2 has 44,929 polygons / 101,583 km2. All Stage-2/4 TA04
numbers were therefore computed on **v1**. P1 uses v2 from PANGAEA
(doi 10.1594/PANGAEA.942325) and reports both.
