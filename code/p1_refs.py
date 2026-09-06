"""TA04-P1 step 1 -- build the reference sets.

Amazon (TAP, MDD): ASGM-only  = Maus v2 polygon INTERSECTING an Amazon Mining Watch
                                2019 or 2020 detection, AND >= 5 km from every named
                                industrial mine in data/industrial_mines.csv.
Ghana (GHA):       mixed      = all Maus v2 polygons in the box; flagged 'industrial'
                                if within 5 km of a named large-scale mine, else
                                'mining, unclassified'. Transfer-only.
Outputs GeoJSON per region under data/refs/ and a summary json.
"""
import json, os, sys
import numpy as np, pandas as pd, geopandas as gpd
from shapely.ops import unary_union

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
D = os.path.join(ROOT, "data")
os.makedirs(os.path.join(D, "refs"), exist_ok=True)

ROIS = {                                   # lon0, lat0, lon1, lat1
    "TAP": (-58.0, -8.0, -54.0, -4.0),     # Stage-2/4 'AMZ' box, reused verbatim
    "MDD": (-71.0, -13.4, -69.4, -12.0),   # NEW in P1 (no upstream MDD box existed)
    "GHA": (-3.2, 4.9, -0.9, 7.2),         # Stage-2/4 'GHA' box, reused verbatim
}
AMAZON = ["TAP", "MDD"]
BUF_KM = 5.0

def aeqd(lon, lat):
    """Local azimuthal-equidistant CRS (metres) centred on the ROI."""
    return f"+proj=aeqd +lat_0={lat} +lon_0={lon} +x_0=0 +y_0=0 +datum=WGS84 +units=m +no_defs"

def roi_centre(b):
    return (b[0] + b[2]) / 2, (b[1] + b[3]) / 2

def main():
    maus = gpd.read_file(os.path.join(D, "maus_v2.gpkg"))
    print(f"Maus v2 global: {len(maus)} polygons, {maus.AREA.sum():.1f} km2", flush=True)

    amw = []
    for y in (2019, 2020):
        g = gpd.read_file(os.path.join(D, f"amw_{y}.geojson"))
        g["amw_year"] = y
        amw.append(g)
        print(f"AMW {y}: {len(g)} features", flush=True)
    amw = pd.concat(amw, ignore_index=True)
    amw = gpd.GeoDataFrame(amw, geometry="geometry", crs="EPSG:4326")

    ind = pd.read_csv(os.path.join(D, "industrial_mines.csv"))
    ind = ind[(ind.geolocated == "yes") & (~ind.name.str.contains("Huaypetue"))]

    summary = {}
    for k, b in ROIS.items():
        cx, cy = roi_centre(b)
        crs = aeqd(cx, cy)
        box = gpd.GeoDataFrame(geometry=gpd.points_from_xy([b[0], b[2]], [b[1], b[3]]),
                               crs="EPSG:4326").total_bounds
        sub = maus.cx[b[0]:b[2], b[1]:b[3]].copy()
        sub = sub[sub.geometry.centroid.within(
            gpd.GeoSeries.from_wkt([f"POLYGON(({b[0]} {b[1]},{b[2]} {b[1]},{b[2]} {b[3]},{b[0]} {b[3]},{b[0]} {b[1]}))"],
                                   crs="EPSG:4326").iloc[0])].reset_index(drop=True)
        sub["maus_id"] = [f"{k}_M{i:05d}" for i in range(len(sub))]
        subm = sub.to_crs(crs)
        subm["area_km2"] = subm.geometry.area / 1e6

        # distance to nearest named industrial mine
        mines = ind[ind.region == k]
        if len(mines):
            mp = gpd.GeoDataFrame(mines.copy(),
                                  geometry=gpd.points_from_xy(mines.lon, mines.lat),
                                  crs="EPSG:4326").to_crs(crs)
            dist = np.array([subm.geometry.distance(p).values for p in mp.geometry]).T  # n_poly x n_mine
            subm["d_ind_km"] = dist.min(axis=1) / 1000.0
            subm["nearest_ind"] = mp.name.values[dist.argmin(axis=1)]
        else:
            subm["d_ind_km"] = np.inf
            subm["nearest_ind"] = ""

        rec = {"roi": list(b), "maus_v2_polygons_in_box": int(len(sub)),
               "maus_v2_area_km2": float(subm.area_km2.sum()),
               "named_industrial_mines": int(len(mines))}

        if k in AMAZON:
            a = amw.cx[b[0]:b[2], b[1]:b[3]]
            rec["amw_features_in_box"] = int(len(a))
            if len(a):
                au = unary_union(a.geometry.values)
                hits = sub.geometry.intersects(au).values
            else:
                hits = np.zeros(len(sub), bool)
            subm["amw_hit"] = hits
            subm["far_from_industrial"] = subm.d_ind_km >= BUF_KM
            subm["asgm"] = subm.amw_hit & subm.far_from_industrial
            subm["proposed_label"] = np.where(subm.asgm, "ASGM",
                                     np.where(~subm.amw_hit, "no_AMW_support", "near_industrial"))
            rec["amw_intersecting"] = int(hits.sum())
            rec["excluded_within_5km_industrial"] = int((subm.amw_hit & ~subm.far_from_industrial).sum())
            rec["ASGM_positives"] = int(subm.asgm.sum())
            rec["ASGM_area_km2"] = float(subm.loc[subm.asgm, "area_km2"].sum())
            subm["source"] = "MausV2 x AMW2019-20"
        else:
            subm["industrial_flag"] = subm.d_ind_km < BUF_KM
            subm["proposed_label"] = np.where(subm.industrial_flag, "industrial", "mining, unclassified")
            subm["source"] = "MausV2 (GHA box)"
            rec["industrial_flagged"] = int(subm.industrial_flag.sum())
            rec["unclassified"] = int((~subm.industrial_flag).sum())
            rec["industrial_area_km2"] = float(subm.loc[subm.industrial_flag, "area_km2"].sum())
            rec["unclassified_area_km2"] = float(subm.loc[~subm.industrial_flag, "area_km2"].sum())

        # --- P1 DEVIATION from PLAN 1.3 (tightening, logged in RESEARCH_LOG) ---
        # The pre-registered rule accepts a whole Maus polygon that *intersects* AMW.
        # In MDD Maus v2 stores the entire ASGM belt as ONE 2,536 km2 polygon, of which
        # only 814 km2 is AMW-confirmed, so polygon-level acceptance would admit a large
        # amount of non-mining interior. We therefore sample positives from the PIXEL-LEVEL
        # intersection (Maus v2 AND AMW), minus a 5 km buffer around named industrial mines.
        # This can only raise reference purity; it never adds a positive.
        if k in AMAZON and len(a):
            au_m = unary_union(a.to_crs(crs).geometry.values)
            pos = subm[subm.asgm].geometry.intersection(au_m)
            pos = pos[~pos.is_empty]
            pos_geom = unary_union(pos.values)
            if len(mines):
                pos_geom = pos_geom.difference(unary_union(mp.geometry.buffer(BUF_KM * 1000).values))
            rec["positive_frame_km2"] = float(pos_geom.area / 1e6)
            gpd.GeoDataFrame({"roi": [k], "kind": ["ASGM_MausV2_x_AMW"]},
                             geometry=[pos_geom], crs=crs).to_crs("EPSG:4326").to_file(
                os.path.join(D, "refs", f"pos_{k}.geojson"), driver="GeoJSON")
        elif k == "GHA":
            for flag, nm in [(True, "industrial"), (False, "unclassified")]:
                gg = unary_union(subm[subm.industrial_flag == flag].geometry.values)
                gpd.GeoDataFrame({"roi": [k], "kind": [nm]}, geometry=[gg], crs=crs).to_crs(
                    "EPSG:4326").to_file(os.path.join(D, "refs", f"pos_GHA_{nm}.geojson"),
                                         driver="GeoJSON")
            rec["positive_frame_km2"] = float(subm.area_km2.sum())

        out = subm.to_crs("EPSG:4326")
        out["lon"] = out.geometry.centroid.x
        out["lat"] = out.geometry.centroid.y
        out.to_file(os.path.join(D, "refs", f"ref_{k}.geojson"), driver="GeoJSON")
        summary[k] = rec
        print(k, json.dumps(rec, indent=1), flush=True)

    json.dump(summary, open(os.path.join(ROOT, "results", "P1", "ref_summary.json"), "w"), indent=1)
    print("wrote results/P1/ref_summary.json", flush=True)

if __name__ == "__main__":
    main()
