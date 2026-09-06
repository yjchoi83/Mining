"""TA04-P2 -- prepare the two sensitivity inputs.
S1: point ids inside the Maus polygons under the `uncertain` QC chips -> uncertain_exclusion.json
S2: landscape WorldCover proportions inside each negative frame -> landscape_weights.json
"""
import json, re, time, random
import numpy as np, pandas as pd, geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import box

ROIS = {"TAP": (-58.0, -8.0, -54.0, -4.0), "MDD": (-71.0, -13.4, -69.4, -12.0),
        "GHA": (-3.2, 4.9, -0.9, 7.2)}
WC = {10: "tree", 20: "shrub", 30: "grass", 40: "crop", 50: "built", 60: "bare",
      70: "snow", 80: "water", 90: "wetland", 95: "mangrove", 100: "moss"}

def aeqd(b):
    return (f"+proj=aeqd +lat_0={(b[1]+b[3])/2} +lon_0={(b[0]+b[2])/2} "
            f"+datum=WGS84 +units=m +no_defs")

# ---------------- S1 ----------------
q = pd.read_csv("results/P1/qc_table.csv")
unc = q[q.decision == "uncertain"].copy()
unc["lon"] = unc.notes.str.extract(r"lon=(-?\d+\.\d+)").astype(float)
unc["lat"] = unc.notes.str.extract(r"lat=(-?\d+\.\d+)").astype(float)
print("uncertain chips:", list(unc.id))

excl = {}
for task, rois in (("amazon", ["TAP", "MDD"]), ("gha_ind", ["GHA"]), ("gha_unc", ["GHA"])):
    for arm in ("U", "E"):
        ids = []
        for k in rois:
            b = ROIS[k]; crs = aeqd(b)
            sub = unc[(unc.lon.between(b[0], b[2])) & (unc.lat.between(b[1], b[3]))]
            if not len(sub): continue
            fr = gpd.read_file(f"data/refs/pos_{k}.geojson") if k != "GHA" else \
                 gpd.GeoDataFrame(pd.concat([gpd.read_file(f"data/refs/pos_GHA_{n}.geojson")
                                             for n in ("industrial", "unclassified")],
                                            ignore_index=True), crs="EPSG:4326")
            u = unary_union(fr.to_crs(crs).geometry.values)
            parts = gpd.GeoDataFrame(geometry=list(u.geoms) if u.geom_type.startswith("Multi")
                                     else [u], crs=crs)
            cg = gpd.GeoDataFrame(sub, geometry=gpd.points_from_xy(sub.lon, sub.lat),
                                  crs="EPSG:4326").to_crs(crs)
            hit = gpd.sjoin(cg, parts.reset_index(), how="left", predicate="within")
            keep = parts.loc[[int(i) for i in hit["index"].dropna().unique()]]
            if not len(keep): continue
            bad = unary_union(keep.geometry.values)
            pf = (f"data/points_{k}.csv" if arm == "U" else f"data/p2_points_{k}.csv")
            p = pd.read_csv(pf)
            p = p[p.cls == 1]
            pg = gpd.GeoDataFrame(p, geometry=gpd.points_from_xy(p.lon, p.lat),
                                  crs="EPSG:4326").to_crs(crs)
            ids += list(p.id[pg.geometry.within(bad).values])
        excl.setdefault(task, {})[arm] = ids
        print(f"  S1 {task} arm {arm}: excluding {len(ids)} positive points")
json.dump(excl, open("results/P2/uncertain_exclusion.json", "w"), indent=1)

# ---------------- S2 ----------------
import ee
for _ in range(30):
    try: ee.Initialize(); break
    except Exception: time.sleep(8 + random.random() * 10)
wc = ee.Image("ESA/WorldCover/v100/2020").select("Map")
w = {}
for k, b in ROIS.items():
    roi = ee.Geometry.Rectangle(list(b))
    h = wc.reduceRegion(reducer=ee.Reducer.frequencyHistogram(), geometry=roi, scale=300,
                        maxPixels=1e10, bestEffort=True, tileScale=8).getInfo()["Map"]
    h = {int(float(a)): v for a, v in h.items() if float(a) > 0}
    tot = sum(h.values())
    w[k] = {WC.get(a, str(a)): v / tot for a, v in h.items()}
    print(f"  S2 {k} landscape: " +
          ", ".join(f"{a} {100*v:.1f}%" for a, v in sorted(w[k].items(), key=lambda z: -z[1])[:5]))
# pooled weights used by the analysis loader (keyed by WorldCover name)
agg = {}
for k in w:
    for a, v in w[k].items(): agg[a] = agg.get(a, 0) + v / len(w)
json.dump(agg, open("results/P2/landscape_weights.json", "w"), indent=1)
json.dump(w, open("results/P2/landscape_weights_per_roi.json", "w"), indent=1)
print("wrote results/P2/uncertain_exclusion.json and landscape_weights.json")
