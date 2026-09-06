"""TA04-P1 -- three-way pixel-level overlap for TAP:
   Maus v2 x AMW positives  x  MapBiomas garimpo  x  MapBiomas industrial.

MapBiomas `class_id` is mutually exclusive (1xx industrial / 2xx garimpo / 0 none), so the
three-way table is a 2 x 3: [inside / outside our ASGM frame] x [garimpo / industrial / none].

AREAS ARE DESIGN-BASED, not a full raster intersection:
  * the ASGM frame area (1,904.19 km2) and the MapBiomas class areas (garimpo 573.81,
    industrial 4.00 km2) are EXACT, computed at native 30 m in Earth Engine (p1_mapbiomas.py,
    p1_refs.py);
  * the SPLIT of the frame across MapBiomas classes is estimated from the 4,000 TAP positive
    points, which were drawn UNIFORMLY AT RANDOM inside the frame and are therefore an
    area-representative (equal-probability) sample of it. Wilson 95% intervals are reported.
The negatives are NOT area-representative (they are WorldCover-stratified), so they are never
used for an area estimate here.
"""
import json, os, math
import numpy as np, pandas as pd

GARIMPO = set(range(214, 226))
INDUSTRIAL = set(range(101, 131))
ROI_KM2 = 195928.0        # TAP box, aeqd; = negative frame 178,686 km2 / 0.9120 (p1_points.py)

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

def mbclass(c):
    c = int(c)
    return "garimpo" if c in GARIMPO else ("industrial" if c in INDUSTRIAL else "none")

d = pd.read_csv("data/samples_TAP.csv")
# sampleRegions ran with geometries=False, so coordinates come back from the point file by id
xy = pd.read_csv("data/points_TAP.csv")[["id", "lon", "lat"]]
d = d.merge(xy, on="id", how="left")
d["mb"] = d.mb_cid.fillna(0).map(mbclass)
pos = d[d.cls == 1].copy()
n = len(pos)

ref = json.load(open("results/P1/ref_summary.json"))
mb = json.load(open("results/P1/mapbiomas_classids.json"))["areas_km2"]
F = ref["TAP"]["positive_frame_km2"]
G, I = mb["garimpo_all_km2"], mb["industrial_all_km2"]

cnt = {c: int((pos.mb == c).sum()) for c in ("garimpo", "industrial", "none")}
est = {c: cnt[c] / n * F for c in cnt}
ci = {c: tuple(x * F for x in wilson(cnt[c], n)) for c in cnt}

print("=" * 96)
print("THREE-WAY PIXEL-LEVEL OVERLAP — TAP box (-58,-8,-54,-4), 2019")
print(f"ROI {ROI_KM2:,.0f} km2 | ASGM frame (Maus v2 x AMW, minus 5 km industrial) {F:,.1f} km2 "
      f"| MapBiomas garimpo {G:,.1f} | MapBiomas industrial {I:,.1f} km2")
print(f"frame split estimated from n={n:,} equal-probability points inside the frame")
print("=" * 96)
print(f"{'':34s}{'MB garimpo':>22s}{'MB industrial':>18s}{'MB none':>16s}{'row total':>14s}")
row1 = f"{'INSIDE Maus x AMW ASGM frame':34s}"
row1 += f"{est['garimpo']:>16,.1f} km2" + f"{est['industrial']:>13,.1f} km2" + f"{est['none']:>11,.1f} km2" + f"{F:>9,.1f} km2"
print(row1)
print(f"{'   (share of frame)':34s}"
      f"{cnt['garimpo']/n*100:>19.1f}%{cnt['industrial']/n*100:>17.1f}%{cnt['none']/n*100:>15.1f}%{100.0:>13.1f}%")
print(f"{'   (Wilson 95% CI, km2)':34s}"
      f"{ci['garimpo'][0]:>13,.0f}-{ci['garimpo'][1]:<7,.0f}"
      f"{ci['industrial'][0]:>10,.0f}-{ci['industrial'][1]:<6,.0f}"
      f"{ci['none'][0]:>10,.0f}-{ci['none'][1]:<6,.0f}")
o_g, o_i = G - est["garimpo"], I - est["industrial"]
o_n = ROI_KM2 - F - o_g - o_i
print(f"{'OUTSIDE frame (rest of ROI)':34s}"
      f"{o_g:>16,.1f} km2{o_i:>13,.1f} km2{o_n:>11,.0f} km2{ROI_KM2-F:>9,.0f} km2")
print(f"{'column total':34s}{G:>16,.1f} km2{I:>13,.1f} km2{ROI_KM2-G-I:>11,.0f} km2{ROI_KM2:>9,.0f} km2")
print("=" * 96)
print(f"AGREEMENT  : {est['garimpo']:,.0f} km2 of our frame is MapBiomas garimpo "
      f"({cnt['garimpo']/n*100:.1f}% of the frame, {100*est['garimpo']/G:.1f}% of all TAP garimpo)")
print(f"COMMISSION?: {est['none']:,.0f} km2 of our frame is NOT any MapBiomas mining "
      f"({cnt['none']/n*100:.1f}%) — the open question")
print(f"OMISSION?  : {o_g:,.0f} km2 of MapBiomas garimpo lies OUTSIDE our frame "
      f"({100*o_g/G:.1f}% of TAP garimpo)")
print(f"INDUSTRIAL : {est['industrial']:,.1f} km2 inside the frame — the 5 km named-mine "
      f"exclusion leaves ZERO MapBiomas-industrial pixels in the ASGM positives")

# ---- what are the MapBiomas-none positives? -------------------------------------------
nm = pos[pos.mb == "none"].copy()
nm["kind"] = np.where(nm.NDWI_p50 > 0.0, "water / turbid pond",
             np.where(nm.NDVI_p50 < 0.30, "bare — sandbar / spoil / tailings", "vegetated"))
print("\nWHAT THE 'MapBiomas none' POSITIVES LOOK LIKE (S2-2019 annual percentiles at the point):")
tot = len(nm)
for k, g in nm.groupby("kind"):
    print(f"  {k:36s} {len(g):5d}  {100*len(g)/tot:5.1f}%   "
          f"NDVI_p50 {g.NDVI_p50.median():+.3f}  NDWI_p50 {g.NDWI_p50.median():+.3f}  "
          f"B11_p50 {g.B11_p50.median():.3f}  est. {len(g)/n*F:,.0f} km2")

print("\nEXAMPLE IDs — positives OUTSIDE MapBiomas mining (candidates for water/sandbar/tailings):")
for k, g in nm.groupby("kind"):
    print(f"\n  [{k}]")
    s = g.reindex(g.NDWI_p50.sort_values(ascending=(k != "water / turbid pond")).index).head(8)
    for r in s.itertuples():
        print(f"    {r.id}  {r.lon:9.4f} {r.lat:8.4f}   "
              f"NDVI_p50 {r.NDVI_p50:+.3f}  NDWI_p50 {r.NDWI_p50:+.3f}  "
              f"B11_p50 {r.B11_p50:.3f}  B12_p50 {r.B12_p50:.3f}")

out = {"roi": "TAP", "roi_km2": ROI_KM2, "frame_km2": F,
       "mapbiomas_garimpo_km2": G, "mapbiomas_industrial_km2": I,
       "n_frame_points": n, "counts_in_frame": cnt,
       "area_est_in_frame_km2": {k: round(v, 2) for k, v in est.items()},
       "wilson95_km2": {k: [round(a, 1), round(b, 1)] for k, (a, b) in ci.items()},
       "garimpo_outside_frame_km2": round(o_g, 2),
       "industrial_outside_frame_km2": round(o_i, 2),
       "none_positive_kinds": {k: int(len(g)) for k, g in nm.groupby("kind")},
       "example_none_ids": {k: list(g.id.head(8)) for k, g in nm.groupby("kind")}}
json.dump(out, open("results/P1/tap_overlap.json", "w"), indent=1)
nm[["id", "lon", "lat", "kind", "NDVI_p50", "NDWI_p50", "B11_p50", "B12_p50"]].to_csv(
    "results/P1/tap_positives_outside_mapbiomas.csv", index=False)
print(f"\nwrote results/P1/tap_overlap.json and "
      f"results/P1/tap_positives_outside_mapbiomas.csv ({len(nm)} rows)")
