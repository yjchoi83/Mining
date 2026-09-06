"""TA04-P1 step 6 -- assemble results/P1/P1_results.md (<= 60 lines) from the JSON outputs."""
import json, os
import pandas as pd

R = "results/P1"
def j(f):
    p = os.path.join(R, f)
    return json.load(open(p)) if os.path.exists(p) else {}

ref = j("ref_summary.json"); mb = j("mapbiomas_classids.json")
ag = j("source_agreement.json"); dp = j("dprk_summary.json")
le = {**j("labeleff_amazon.json"), **j("labeleff_ghana.json")}
inv = j("qc_chip_inventory.json")
qt = pd.read_csv(os.path.join(R, "qc_table.csv")) if os.path.exists(os.path.join(R, "qc_table.csv")) else None

L = []
def w(s=""): L.append(s)

am = le.get("AMAZON_ASGM", {})
rlog = am.get("ratio", {}).get("log", {})       # pre-registered primary
rlgb = am.get("ratio", {}).get("lgbm", {})
rbst = am.get("ratio", {}).get("best", {})
ratio, lo, hi = rlog.get("ratio"), rlog.get("ci_lo"), rlog.get("ci_hi")
if ratio is None:
    verdict = "INCONCLUSIVE (no ratio computed)"
elif ratio >= 3 and lo is not None and lo >= 2:
    verdict = f"**SURVIVES** (ratio {ratio} >= 3, CI lower {lo} >= 2)"
elif ratio < 3:
    verdict = f"**KILLED** (ratio {ratio} < 3 -- pre-registered falsification line)"
else:
    verdict = f"**WOUNDED** (ratio {ratio} >= 3 but CI lower {lo} < 2)"

w("# TA04-P1 results — ASGM-only reference, purity QC, label-efficiency re-test")
w()
w(f"Verdict (pre-registered, PLAN §1.8): {verdict}")
w()
w("## 1. References")
w("| ROI | Maus v2 polys | AMW-intersecting | dropped <5 km of named industrial | positives | positive frame km² |")
w("|---|---|---|---|---|---|")
for k in ("TAP", "MDD"):
    r = ref.get(k, {})
    w(f"| {k} | {r.get('maus_v2_polygons_in_box')} | {r.get('amw_intersecting')} | "
      f"{r.get('excluded_within_5km_industrial')} | {r.get('ASGM_positives')} | "
      f"{r.get('positive_frame_km2',0):.0f} |")
g = ref.get("GHA", {})
w(f"| GHA (mixed, transfer-only) | {g.get('maus_v2_polygons_in_box')} | n/a | n/a | "
  f"{g.get('industrial_flagged')} industrial / {g.get('unclassified')} unclassified | "
  f"{g.get('positive_frame_km2',0):.0f} |")
w()
w("Sources: **Maus v2** PANGAEA doi 10.1594/PANGAEA.942325 (44,929 polys / 101,583 km² — the GEE "
  "`global_mining_polygons` asset used by Stage 2/4 is **v1**: 21,060 / 57,278). **AMW** "
  "`earthrise-media/mining-detector` `48px_v3.2-3.7ensemble` 2019 (5,751 feats) + 2020 (6,110). "
  "20 named industrial mines in `data/industrial_mines.csv` (Wikidata P625; SEC/NI 43-101 for "
  "Tocantinzinho, Palito, São Chico). Negatives ≥1 km from any mining polygon, ESA WorldCover-stratified.")
w()
mbg = mb.get("areas_km2", {})
w(f"**MapBiomas separates garimpo: YES** (ATBD C10 Table 3: 1xx industrial, 2xx garimpo, 215 garimpo gold). "
  f"TAP 2019 at 30 m: garimpo {mbg.get('garimpo_all_km2','?')} km² (gold {mbg.get('garimpo_gold_215_km2','?')}), "
  f"industrial {mbg.get('industrial_all_km2','?')} km² — Tapajós is ~99% garimpo by area.")
tap_ag = ag.get("TAP", {})
if tap_ag.get("crosstab"):
    w(f"**Source agreement (TAP sample points):** {100*tap_ag['frac_our_positives_that_MapBiomas_calls_garimpo']:.1f}% "
      f"of our ASGM positives are MapBiomas garimpo, "
      f"{100*tap_ag['frac_our_positives_MapBiomas_calls_industrial']:.1f}% MapBiomas industrial; "
      f"{100*tap_ag['frac_our_negatives_MapBiomas_calls_mining']:.2f}% of our negatives are any MapBiomas mining. "
      f"MapBiomas is {ref.get('TAP',{}).get('positive_frame_km2',0)/max(1e-9,mbg.get('garimpo_all_km2',1)):.1f}× "
      f"smaller than the Maus×AMW frame — the largest reference disagreement found.")
w()
w("## 2. Purity QC chips")
if qt is not None:
    cnt = qt.groupby(["region", "proposed_label"]).size()
    inv_s = ", ".join(f"{rg} {lb} {n}" for (rg, lb), n in cnt.items())
    w(f"{inv.get('n_chips','?')}/{inv.get('n_rows','?')} chips written "
      f"({inv.get('chip_dir_bytes',0)/1e6:.1f} MB, committed), S2-2019 annual-median RGB, 1×1 km @10 m, "
      f"polygon outline burnt in; `decision` left blank in `qc_table.csv` for human adjudication. "
      f"Inventory: {inv_s}.")
w()
w("## 3. Label efficiency — Amazon ASGM-only (TAP+MDD), 0.5° block CV, 20 draws/budget, AUC")
def curve_rows(res, name):
    c = res.get("curves", {}); f = res.get("full", {})
    ns = [k for k in ("10", "20", "40", "80", "160", "320", "640", "1000")]
    w(f"| {name} — n={res.get('n')}, pos={res.get('n_pos')}, blocks={res.get('n_blocks')}, "
      f"74 baseline feats | " + " | ".join(ns) + " | full |")
    w("|---|" + "---|" * (len(ns) + 1))
    for arm in ("AEF64_log", "BASE74_log", "AEF64_lgbm", "BASE74_lgbm"):
        row = c.get(arm, {})
        w(f"| {arm} | " + " | ".join(f"{row[n]:.3f}" if n in row else "—" for n in ns) + f" | {f.get(arm,0):.3f} |")
if am: curve_rows(am, "Amazon ASGM-only")
w()
w("| arm | ratio | 95% CI (block bootstrap, 1000 draws over 0.5° blocks) | ≥3 & CI≥2 |")
w("|---|---|---|---|")
for mdl, nm in (("log", "logistic — **PRE-REGISTERED PRIMARY**"),
                ("lgbm", "LightGBM — capacity-matched"),
                ("best", "strongest-baseline — post-hoc, hostile to us")):
    r = am.get("ratio", {}).get(mdl, {})
    ok = "✅" if (r.get("ratio") or 0) >= 3 and (r.get("ci_lo") or 0) >= 2 else "❌"
    w(f"| {nm} | {r.get('ratio')} ({r.get('how')}) | {r.get('ci_lo')} – {r.get('ci_hi')} | {ok} |")
w(f"- AEF AUC at the 40-label reference budget: logistic {rlog.get('aef_auc_at_40')}, "
  f"LightGBM {rlgb.get('aef_auc_at_40')}. **The pre-registered primary passes and the hostile arm passes, but the capacity-matched "
  f"LightGBM arm ({rlgb.get('ratio')}, CI {rlgb.get('ci_lo')}–{rlgb.get('ci_hi')}) falls BELOW the "
  f"falsification line.** Stage 4 reported 19.9× (17.3–22.4) on a *LightGBM* baseline; on the "
  f"ASGM-only reference with 0.5° blocks that same arm collapses to {rlgb.get('ratio')}. The "
  f"headline multiple is a linear-probe phenomenon: with trees, AEF at 40 labels is only 0.793 "
  f"and the 74-feature baseline catches it by ~110 labels. Any P2 claim must lead with the "
  f"classifier-dependence, not with 25×.")
w(f"- Pre-registered rule: survives iff ratio ≥ 3 **and** CI lower ≥ 2. → {verdict}")
w()
w("## 4. Ghana (mixed reference, transfer-only framing — not evidence for the ASGM claim)")
gns = ["10", "40", "160", "1000"]
w("| Ghana positives (n=5,998, 36 blocks each) | arm | " + " | ".join(gns) + " | full | ratio log | ratio lgbm | ratio best |")
w("|---|---|" + "---|" * (len(gns) + 4))
for key, nm in (("GHANA_industrial", "industrial-flagged"),
                ("GHANA_unclassified", "unclassified")):
    v = le.get(key, {})
    if not v: continue
    rr = v.get("ratio", {})
    rs = " | ".join(f"{rr[m].get('ratio')} ({rr[m].get('ci_lo')}–{rr[m].get('ci_hi')})"
                    for m in ("log", "lgbm", "best"))
    for arm in ("AEF64_log", "BASE74_log", "AEF64_lgbm", "BASE74_lgbm"):
        c = v["curves"].get(arm, {})
        cells = " | ".join(f"{c[n]:.3f}" if n in c else "—" for n in gns)
        w(f"| {nm if arm=='AEF64_log' else ''} | {arm} | {cells} | {v['full'].get(arm,0):.3f} | "
          + (rs if arm == "AEF64_log" else " | ".join([""] * 3)) + " |")
w("Ghana reproduces the Amazon pattern exactly, including the LightGBM collapse (3.58 / 3.40), so "
  "the classifier-dependence is not an Amazon artefact. Unclassified positives are *easier* than "
  "industrial-flagged ones (AEF full 0.977 vs 0.955), i.e. the Stage-2 'Ghana is easier' result is "
  "not driven by large-scale mines. **Transfer-only: no ASGM claim rests on Ghana.**")
w()
w("## 5. DPRK feasibility (no training in P1)")
tw = dp.get("tang_werner_size_km2_all", {})
w(f"- Tang & Werner `global_mining_footprints` inside the LSIB DPRK boundary: **{dp.get('tang_werner_n')}** polygons, "
  f"{tw.get('sum',0):.1f} km² total; median {tw.get('median',0):.3f} km², "
  f"{tw.get('n_lt_0.1km2')} below 0.1 km², only {tw.get('n_ge_1km2')} at or above 1 km².")
w(f"- Maus v2 inside DPRK: **{dp.get('maus_v2_n')}** polygons, {dp.get('maus_v2_total_km2',0):.1f} km² — "
  f"Maus effectively does not map DPRK. Top-20 with coordinates in `results/P1/dprk_polygons.csv`.")
w(f"- **Minerals are not attributable.** The only `Name` values on DPRK Tang & Werner polygons are "
  f"{dp.get('tang_werner_distinct_names')} (i.e. '2', 'Placemark', 'unnamed polygon'). `irenk.sonosa.or.kr` "
  f"(I-RENK) provides commodity distribution *maps* for 13 minerals plus reserves/production 2014–2021 and "
  f"DPRK–China trade statistics, but **no per-mine names with coordinates and no downloadable geodatabase**.")
w("- **P3 recommendation:** treat DPRK as a *detection* transfer target only, never a commodity-attribution "
  "target. Source ROI should be **Ghana** rather than the Amazon: DPRK footprints are small (median 1.7 ha), "
  "hard-rock and non-forest, which is far closer to Ghana's mixed hard-rock/LSM signature than to Amazonian "
  "alluvial garimpo. Reference for P3 = Tang & Werner (the only source with usable DPRK coverage), used as a "
  "*frame* only, with VHR adjudication of a sample — its DPRK polygons carry no attributes at all.")
w()
w("## 6. Deviations from PLAN")
w("- **§1.3 tightened:** positives are the *pixel-level* Maus v2 ∩ AMW intersection, not whole intersecting "
  "polygons. Maus v2 stores the entire Madre de Dios belt as one 2,536 km² polygon of which only 814 km² is "
  "AMW-confirmed. Purity-increasing only; it can never add a positive.")
w("- **§1.5 tightened:** negatives are drawn by EE WorldCover-stratified sampling, not uniform local sampling — "
  "uniform sampling gave 10 bare / 2 built-up points per 16,000 in Tapajós. Negatives are now near-equal across "
  "land-cover classes, which makes the task harder than a landscape-proportional draw (conservative).")
w("- **§1.1:** the Madre de Dios box is new in P1 (Stage 2/4 never instantiated one). The block "
  "bootstrap reuses 8 of the 20 subsample draws per iteration; CI width is driven by block resampling.")
w()
w("**P2 is not started.**")

open(os.path.join(R, "P1_results.md"), "w").write("\n".join(L) + "\n")
print(f"wrote {R}/P1_results.md — {len(L)} lines")
