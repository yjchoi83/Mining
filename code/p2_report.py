"""TA04-P2 step 6 -- assemble results/P2/P2_results.md (<= 60 lines)."""
import json, os, glob
import pandas as pd

R = "results/P2"
def j(f):
    p = os.path.join(R, f)
    return json.load(open(p)) if os.path.exists(p) else {}

fr = j("frame_erosion.json"); gf = j("ghana_flag.json"); dis = j("disagreement.json")
le = {os.path.basename(f)[3:-5]: json.load(open(f)) for f in glob.glob(f"{R}/le_*.json")}
CLF = ("log", "knn", "lgbm", "mlp")
NICE = {"log": "logistic", "knn": "kNN-15 cos", "lgbm": "LightGBM", "mlp": "MLP 2x128"}
L = []
def w(s=""): L.append(s)

def r(tag, m, k="ratio"):
    return le.get(tag, {}).get("ratio", {}).get(m, {}).get(k)
def ci(tag, m):
    d = le.get(tag, {}).get("ratio", {}).get(m, {})
    return f"{d.get('ci_lo')}–{d.get('ci_hi')}" if d else "—"

k1 = le.get("amazon_E", {}).get("ratio", {}).get("lgbm", {})
K1 = "PASS" if (k1.get("ratio") or 0) >= 3 and (k1.get("ci_lo") or 0) >= 2 else "FAIL"
g = le.get("amazon_E", {}).get("gap_lgbm_full", {}) or {}
K2 = "PASS" if (g.get("gap") or 0) >= 0.03 and (g.get("ci_lo") or 0) > 0 else "FAIL"
k3 = dis.get("TAP", {})
K3 = "PASS" if k3.get("K3_verdict") == "PASS" else "FAIL"

w("# TA04-P2 results — classifier-dependence and frame erosion")
w()
w("**Answer: the label-parity advantage is a property of the (representation, classifier) pair, "
  "not of the representation alone, and it does not survive frame erosion for capacity learners.**")
w()
w("## 1. Classifier-dependence — label-parity ratio (AEF64 vs BASE74, same classifier, k_ref=40)")
w("| task | arm | " + " | ".join(NICE[c] for c in CLF) + " |")
w("|---|---|" + "---|" * len(CLF))
for task, nm in (("amazon", "**Amazon ASGM (primary)**"), ("gha_ind", "Ghana industrial*"),
                 ("gha_unc", "Ghana unclassified*")):
    for arm in ("U", "E"):
        tag = f"{task}_{arm}"
        if tag not in le: continue
        cells = " | ".join(f"**{r(tag,c)}** ({ci(tag,c)})" if c == "lgbm" else f"{r(tag,c)}"
                           for c in CLF)
        w(f"| {nm if arm=='U' else ''} | {arm} | {cells} |")
w("Ratios are censored at 2000/40 = 50. *Ghana Arm E positives are drawn from the whole Ghana "
  "frame and are **not** split by the industrial flag, so the two Ghana Arm-E rows are the same run "
  "reported twice; only the Arm-U rows carry the split.")
w()
am_u, am_e = le.get("amazon_U", {}), le.get("amazon_E", {})
w("Full-data AUC, Amazon (AEF64 / BASE74): " + "; ".join(
    f"{NICE[c]} U {am_u.get('full',{}).get('AEF64_'+c)}/{am_u.get('full',{}).get('BASE74_'+c)}, "
    f"E {am_e.get('full',{}).get('AEF64_'+c)}/{am_e.get('full',{}).get('BASE74_'+c)}" for c in CLF))
w()
w("**Reading.** On the un-eroded frame the huge multiple is a *linear-probe* artefact: logistic "
  f"{r('amazon_U','log')} vs LightGBM {r('amazon_U','lgbm')} and MLP {r('amazon_U','mlp')} on the "
  "same data. Erosion then collapses every arm — logistic "
  f"{r('amazon_U','log')} → {r('amazon_E','log')}, LightGBM {r('amazon_U','lgbm')} → "
  f"{r('amazon_E','lgbm')}, MLP {r('amazon_U','mlp')} → {r('amazon_E','mlp')} (below 1: the "
  "baseline reaches AEF's 40-label AUC with *fewer* than 40 labels). Only the two "
  "**representation-level probes** (linear, cosine-kNN) still clear 3 on arm E. Most of the "
  "apparent label efficiency was the dilated positive frame, not the embedding.")
w()
w("## 2. Pre-registered criteria")
w(f"- **K1 (practical label efficiency): {K1}.** LightGBM-vs-LightGBM on arm E = "
  f"**{k1.get('ratio')}** (CI {k1.get('ci_lo')}–{k1.get('ci_hi')}), needs ≥3 with CI lower ≥2. "
  "Per PLAN_P2 §1.6 the paper may therefore claim only **representation-level** efficiency plus "
  "the classifier-dependence finding, and **must not claim practical label savings**.")
w(f"- **K2 (information gain): {K2}.** Full-data AEF−BASE74 gap under LightGBM on arm E = "
  f"**+{g.get('gap')}** (CI {g.get('ci_lo')}–{g.get('ci_hi')}), needs ≥+0.03 with CI excluding 0. "
  "Passes, but only just: the point estimate sits 0.002 above the line.")
w(f"- **K3 (disagreement explained): {K3}.** {100*k3.get('K3_explained',0):.1f}% "
  f"(CI {100*k3.get('K3_ci',[0,0])[0]:.1f}–{100*k3.get('K3_ci',[0,0])[1]:.1f}%) of "
  "outside-MapBiomas positives are non-forest/water or in patches <1 ha, needs ≥60% → "
  "**reference uncertainty is flagged**, not resolved.")
w()
w("## 3. Frame erosion and reference disagreement")
w("| ROI | un-eroded km² | eroded km² | kept % (95% CI) |")
w("|---|---|---|---|")
for k, v in fr.items():
    lo, hi = v["acceptance_ci"]
    w(f"| {k} | {v['uneroded_km2']:,.1f} | **{v['eroded_km2']:,.1f}** | "
      f"{100*v['acceptance']:.1f} ({100*lo:.1f}–{100*hi:.1f}) |")
w(f"**The Tapajós frame is 78.5% forest.** The eroded TAP frame (409 km²) now agrees to ~20% with "
  f"the independent MapBiomas garimpo estimate (494 km² in-frame, 574 km² box-wide), where the "
  f"un-eroded frame was 3.3× too big — two methods sharing no inputs converging once the dilation "
  f"is removed.")
w("Three-way pixel table, TAP (design-based, n=4,000 in-frame points): inside the frame "
  f"**{dis.get('TAP',{}).get('area_est_km2',{}).get('garimpo')} km² MapBiomas garimpo / "
  f"{dis.get('TAP',{}).get('area_est_km2',{}).get('industrial')} industrial / "
  f"{dis.get('TAP',{}).get('area_est_km2',{}).get('none')} none**. Of the "
  f"{dis.get('TAP',{}).get('n_outside_mb')} outside-MapBiomas positives, "
  f"{100*dis.get('TAP',{}).get('outside_by_ndvi',{}).get('forest',0)/max(1,dis.get('TAP',{}).get('n_outside_mb',1)):.1f}% "
  f"are forest, **0.0% are in patches <1 ha**, but **{100*dis.get('TAP',{}).get('frac_within_100m_mb',0):.1f}% "
  "lie within 100 m of mapped mining** — the dilation signature, reported post-hoc because the "
  "pre-registered K3 proxy (patch size) was the wrong instrument for a frame made of large blobs.")
w("**MDD has no MapBiomas coverage at all** (Brazil-only asset, Peru ROI), so half the primary "
  "Amazon ROI has no independent reference.")
w()
w("## 4. Sensitivities")
for tag, lab in (("amazon_E_S1", "S1 exclude uncertain (arm E)"),
                 ("amazon_U_S2", "S2 landscape-proportional negatives (arm U)"),
                 ("amazon_E_S2", "S2 landscape-proportional negatives (arm E)")):
    if tag in le:
        w(f"- **{lab}:** logistic {r(tag,'log')} ({ci(tag,'log')}), "
          f"LightGBM {r(tag,'lgbm')} ({ci(tag,'lgbm')}); n={le[tag].get('n')}.")
w("- **S2 strengthens the conclusion, it does not rescue it:** with landscape-proportional "
  "(94% tree-cover) negatives the task gets easier for both feature sets and the capacity-matched "
  "LightGBM ratio falls further, to 1.83 on arm U and **1.09** on arm E. The near-equal-per-class "
  "negatives used in the main analysis are therefore the *harder*, more conservative choice.")
w("- **S1 is structurally uninformative** and is reported as such: the `uncertain` chips sit in "
  "33–50 ha frame parts (0.02–0.03% of the frame), so excluding them removes 0–2 sampled points. "
  "A real label-uncertainty sensitivity needs a much larger adjudicated chip set (P3).")
w(f"- **S3 Ghana industrial rule:** the new rule flags **{gf.get('n_industrial_new')}/"
  f"{gf.get('n_polygons')}** polygons industrial vs **{gf.get('n_industrial_old')}** under the old "
  f"5 km rule; **{gf.get('n_by_size')}** come from the `area ≥ 20 ha` clause and only "
  f"**{gf.get('n_by_prox_and_texture_only')}** from `2 km + grey terraced texture`. Maus v2 hulls "
  "aggregate many small ASM pits, so 20 ha is not a usable LSM threshold — this contradicts the P1 "
  "chip adjudication and should be replaced by compactness/texture in P3.")
w()
w("**EE budget:** point sampling only — 48k cheap 3-band screening points, 15.4k full 138-band "
  "points, ~12k WorldCover points, plus one 30 m distance-transform sampling. No image exports, "
  "well inside the 30 EECU-hour ceiling.")
w()
w("**P3 (transfer) is not started.**")

open(os.path.join(R, "P2_results.md"), "w").write("\n".join(L) + "\n")
print(f"wrote {R}/P2_results.md — {len(L)} lines")
