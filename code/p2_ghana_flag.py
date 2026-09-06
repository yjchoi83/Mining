"""TA04-P2 step 3 -- Ghana industrial flag, redefined (PLAN_P2 §1.4).

OLD (P1): centroid within 5 km of a named large-scale mine.
NEW     : area >= 20 ha  OR  (within 2 km of a named mine AND grey terraced texture),
          where "grey terraced texture" is, at polygon level and pre-registered:
              median NDVI_p50 < 0.35            (grey / bare, not vegetated)
          AND median B8_sd7  > median of all Ghana positive polygons   (terraced relief)
P1 adjudication overrides: the Maus polygons under chips GHA_IND_000/001/003 are forced to
ASM-like, whatever the rule returns.
"""
import json
import numpy as np, pandas as pd, geopandas as gpd

CRS = "+proj=aeqd +lat_0=6.05 +lon_0=-2.05 +datum=WGS84 +units=m +no_defs"
AREA_HA = 20.0
PROX_M = 2000.0
NDVI_T = 0.35

ref = gpd.read_file("data/refs/ref_GHA.geojson").to_crs(CRS).reset_index(drop=True)
ref["poly"] = np.arange(len(ref))
ref["area_ha"] = ref.geometry.area / 1e4

# --- attach sampled points to their polygon so we can get per-polygon texture -----------
s = pd.read_csv("data/samples_GHA.csv")
xy = pd.read_csv("data/points_GHA.csv")[["id", "lon", "lat"]]
s = s.merge(xy, on="id", how="left")
pos = s[s.cls == 1].copy()
gp = gpd.GeoDataFrame(pos, geometry=gpd.points_from_xy(pos.lon, pos.lat),
                      crs="EPSG:4326").to_crs(CRS)
j = gpd.sjoin(gp, ref[["poly", "geometry"]], how="left", predicate="within")
pos["poly"] = j["poly"].values
agg = (pos.dropna(subset=["poly"]).groupby("poly")
       .agg(ndvi=("NDVI_p50", "median"), tex=("B8_sd7", "median"), npts=("id", "size")))
TEX_T = float(agg.tex.median())

ref = ref.merge(agg, left_on="poly", right_index=True, how="left")
grey_terraced = (ref.ndvi < NDVI_T) & (ref.tex > TEX_T)
big = ref.area_ha >= AREA_HA
near2 = ref.d_ind_km < (PROX_M / 1000.0)
ref["industrial_new"] = big | (near2 & grey_terraced.fillna(False))
ref["industrial_old"] = ref.proposed_label == "industrial"

# --- P1 adjudication override ----------------------------------------------------------
q = pd.read_csv("results/P1/qc_table.csv")
q = q[q.id.isin(["GHA_IND_000", "GHA_IND_001", "GHA_IND_003"])].copy()
q["lon"] = q.notes.str.extract(r"lon=(-?\d+\.\d+)").astype(float)
q["lat"] = q.notes.str.extract(r"lat=(-?\d+\.\d+)").astype(float)
cg = gpd.GeoDataFrame(q, geometry=gpd.points_from_xy(q.lon, q.lat),
                      crs="EPSG:4326").to_crs(CRS)
ov = gpd.sjoin(cg, ref[["poly", "geometry"]], how="left", predicate="within")
forced = [int(p) for p in ov["poly"].dropna().unique()]
ref.loc[ref.poly.isin(forced), "industrial_new"] = False
print(f"P1 override: {len(forced)} polygons forced to ASM-like from GHA_IND_000/001/003 "
      f"(poly ids {forced})")

n_new, n_old = int(ref.industrial_new.sum()), int(ref.industrial_old.sum())
print(f"texture threshold B8_sd7 median over Ghana positive polygons = {TEX_T:.5f}")
print(f"OLD rule (5 km proximity)      : {n_old} industrial / {len(ref)-n_old} unclassified")
print(f"NEW rule (>=20 ha OR 2 km+grey): {n_new} industrial / {len(ref)-n_new} unclassified")
print(f"  by size alone >=20 ha        : {int(big.sum())}")
print(f"  by 2 km + grey terraced only : {int((~big & near2 & grey_terraced.fillna(False)).sum())}")
ct = pd.crosstab(ref.industrial_old, ref.industrial_new)
print("\nold (rows) x new (cols):\n" + ct.to_string())

# --- point-level relabel ---------------------------------------------------------------
m = ref.set_index("poly").industrial_new
pos["industrial_new"] = pos.poly.map(m)
pos["sub_new"] = np.where(pos.industrial_new.fillna(False), "industrial", "unclassified")
sw = pd.crosstab(pos["sub"], pos.sub_new)
print("\npositive POINTS, old sub (rows) x new sub (cols):\n" + sw.to_string())
pos[["id", "poly", "sub", "sub_new"]].to_csv("data/p2_gha_relabel.csv", index=False)

out = {"area_ha_threshold": AREA_HA, "prox_m": PROX_M, "ndvi_thresh": NDVI_T,
       "tex_thresh_B8_sd7": TEX_T, "n_polygons": int(len(ref)),
       "n_industrial_old": n_old, "n_industrial_new": n_new,
       "n_by_size": int(big.sum()),
       "n_by_prox_and_texture_only": int((~big & near2 & grey_terraced.fillna(False)).sum()),
       "p1_override_polys": forced,
       "points_old_x_new": {str(a): {str(b): int(v) for b, v in r.items()}
                            for a, r in sw.iterrows()}}
json.dump(out, open("results/P2/ghana_flag.json", "w"), indent=1)
ref.drop(columns="geometry").to_csv("results/P2/ghana_polygons_flagged.csv", index=False)
print("\nwrote results/P2/ghana_flag.json and ghana_polygons_flagged.csv")
