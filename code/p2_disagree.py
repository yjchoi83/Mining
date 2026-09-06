"""TA04-P2 step 2 -- reference disagreement, TAP and MDD (PLAN_P2 §1.3), and criterion K3.

Three-way pixel table Maus x AMW / MapBiomas garimpo / MapBiomas industrial, then characterise
the positives that fall OUTSIDE MapBiomas mining by NDVI class, patch size and distance to
MapBiomas mining.

K3: >= 60% of outside-MapBiomas positives are non-forest/water OR in patches < 1 ha
    -> disagreement attributed to frame dilation; otherwise flag reference uncertainty.
"""
import json, math, time, random
import numpy as np, pandas as pd

GARIMPO, INDUSTRIAL = set(range(214, 226)), set(range(101, 131))
ROI_KM2 = {"TAP": 195928.0, "MDD": 26918.0}   # aeqd box areas (MDD 1.6 x 1.4 deg at ~12.7S)

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

def mbclass(c):
    c = int(c)
    return "garimpo" if c in GARIMPO else ("industrial" if c in INDUSTRIAL else "none")

def mb_distance(pts, chunk=4000):
    """Metres to the nearest MapBiomas 2019 mining pixel (1xx or 2xx), 30 m distance transform."""
    import ee
    for _ in range(30):
        try: ee.Initialize(); break
        except Exception: time.sleep(8 + random.random() * 10)
    MB = ("projects/mapbiomas-public/assets/brazil/lulc/collection10/"
          "mapbiomas_brazil_collection10_mining_substances_v3")
    cid = ee.Image(MB).select("classification_2019").reproject(crs="EPSG:4326", scale=30)
    mining = cid.gte(101).And(cid.lte(225)).unmask(0)
    # fastDistanceTransform returns SQUARED pixel distance
    dist = mining.fastDistanceTransform(256).sqrt().multiply(30).rename("d_mb")
    out = []
    for i in range(0, len(pts), chunk):
        ch = pts[i:i + chunk]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([x, y]), {"j": i + n})
                                   for n, (x, y) in enumerate(ch)])
        for a in range(10):
            try:
                r = dist.sampleRegions(collection=fc, scale=30, tileScale=8,
                                       geometries=False).getInfo(); break
            except Exception:
                if a == 9: raise
                time.sleep(12 + random.random() * 20)
        d = {f["properties"]["j"]: f["properties"].get("d_mb") for f in r["features"]}
        out += [d.get(i + n) for n in range(len(ch))]
        print(f"    dist {min(i+chunk, len(pts))}/{len(pts)}", flush=True)
    return out

def main():
    ref = json.load(open("results/P1/ref_summary.json"))
    mbtot = json.load(open("results/P1/mapbiomas_classids.json"))["areas_km2"]
    out = {}
    allrows = []
    for k in ("TAP", "MDD"):
        d = pd.read_csv(f"data/samples_{k}.csv")
        xy = pd.read_csv(f"data/points_{k}.csv")[["id", "lon", "lat"]]
        d = d.merge(xy, on="id", how="left")
        pos = d[d.cls == 1].copy()
        F = ref[k]["positive_frame_km2"]
        if "mb_cid" not in pos.columns:
            out[k] = {"note": "MapBiomas does not cover this ROI (Brazil-only); "
                              "no three-way table is possible", "frame_km2": F}
            print(f"\n=== {k} === MapBiomas is Brazil-only -> no coverage; frame {F:,.1f} km2")
            continue
        pos["mb"] = pos.mb_cid.fillna(0).map(mbclass)
        n = len(pos)
        cnt = {c: int((pos.mb == c).sum()) for c in ("garimpo", "industrial", "none")}
        est = {c: cnt[c] / n * F for c in cnt}
        ci = {c: tuple(x * F for x in wilson(cnt[c], n)) for c in cnt}
        G, I = mbtot["garimpo_all_km2"], mbtot["industrial_all_km2"]
        print(f"\n=== {k} — three-way pixel table (design-based, n={n:,} in-frame points) ===")
        print(f"{'':30s}{'MB garimpo':>16s}{'MB industrial':>16s}{'MB none':>14s}{'total':>13s}")
        print(f"{'inside Maus x AMW frame':30s}{est['garimpo']:>13,.1f}km2"
              f"{est['industrial']:>13,.1f}km2{est['none']:>11,.1f}km2{F:>10,.1f}km2")
        print(f"{'  share of frame':30s}{100*cnt['garimpo']/n:>15.1f}%"
              f"{100*cnt['industrial']/n:>15.1f}%{100*cnt['none']/n:>13.1f}%{100.0:>12.1f}%")
        print(f"{'outside frame':30s}{G-est['garimpo']:>13,.1f}km2{I-est['industrial']:>13,.1f}km2"
              f"{ROI_KM2[k]-F-(G-est['garimpo'])-(I-est['industrial']):>11,.0f}km2"
              f"{ROI_KM2[k]-F:>10,.0f}km2")

        nm = pos[pos.mb == "none"].copy()
        nm["ndvi_ann"] = (nm.B8_p50 - nm.B4_p50) / (nm.B8_p50 + nm.B4_p50)
        nm["cls_ndvi"] = np.where(nm.NDWI_p50 > 0, "water",
                         np.where(nm.ndvi_ann < 0.5, "bare/non-forest", "forest"))
        print(f"    querying distance-to-MapBiomas-mining for {len(nm)} points...", flush=True)
        nm["d_mb_m"] = mb_distance(list(zip(nm.lon, nm.lat)))
        # patch size: connected component of the positive frame containing the point
        import geopandas as gpd
        from shapely.ops import unary_union
        b = {"TAP": (-58.0, -8.0, -54.0, -4.0), "MDD": (-71.0, -13.4, -69.4, -12.0)}[k]
        crs = (f"+proj=aeqd +lat_0={(b[1]+b[3])/2} +lon_0={(b[0]+b[2])/2} "
               f"+datum=WGS84 +units=m +no_defs")
        fr = gpd.read_file(f"data/refs/pos_{k}.geojson").to_crs(crs)
        u = unary_union(fr.geometry.values)
        parts = gpd.GeoDataFrame(geometry=list(u.geoms) if u.geom_type.startswith("Multi") else [u],
                                 crs=crs)
        parts["patch_ha"] = parts.geometry.area / 1e4
        gp = gpd.GeoDataFrame(nm, geometry=gpd.points_from_xy(nm.lon, nm.lat),
                              crs="EPSG:4326").to_crs(crs)
        nm["patch_ha"] = gpd.sjoin(gp, parts, how="left", predicate="within")["patch_ha"].values

        nm["explained"] = (nm.cls_ndvi != "forest") | (nm.patch_ha < 1.0)
        expl = float(nm.explained.mean())
        lo, hi = wilson(int(nm.explained.sum()), len(nm))
        print(f"\n  positives OUTSIDE MapBiomas mining: n={len(nm)} ({100*len(nm)/n:.1f}% of frame)")
        for c, g in nm.groupby("cls_ndvi"):
            print(f"    {c:16s} {len(g):5d} {100*len(g)/len(nm):5.1f}%  "
                  f"median patch {g.patch_ha.median():9,.1f} ha  "
                  f"median dist to MB mining {g.d_mb_m.median():7,.0f} m")
        print(f"    patches < 1 ha  : {int((nm.patch_ha < 1).sum())} "
              f"({100*(nm.patch_ha < 1).mean():.1f}%)")
        print(f"    within 100 m of MapBiomas mining: {int((nm.d_mb_m < 100).sum())} "
              f"({100*(nm.d_mb_m < 100).mean():.1f}%)")
        print(f"  K3 explained (non-forest/water OR patch<1ha) = {100*expl:.1f}% "
              f"[{100*lo:.1f}-{100*hi:.1f}]  -> "
              f"{'PASS' if expl >= 0.60 else 'FAIL (flag reference uncertainty)'}")
        nm["roi"] = k
        allrows.append(nm[["roi", "id", "lon", "lat", "cls_ndvi", "ndvi_ann", "NDWI_p50",
                           "patch_ha", "d_mb_m", "explained"]])
        out[k] = {"n_frame_points": n, "frame_km2": F,
                  "counts": cnt, "area_est_km2": {a: round(v, 2) for a, v in est.items()},
                  "wilson95_km2": {a: [round(x, 1), round(y, 1)] for a, (x, y) in ci.items()},
                  "mapbiomas_total_km2": {"garimpo": G, "industrial": I},
                  "n_outside_mb": int(len(nm)),
                  "outside_by_ndvi": {a: int(len(g)) for a, g in nm.groupby("cls_ndvi")},
                  "median_patch_ha": float(nm.patch_ha.median()),
                  "median_dist_mb_m": float(nm.d_mb_m.median()),
                  "frac_patch_lt_1ha": float((nm.patch_ha < 1).mean()),
                  "frac_within_100m_mb": float((nm.d_mb_m < 100).mean()),
                  "K3_explained": expl, "K3_ci": [lo, hi],
                  "K3_verdict": "PASS" if expl >= 0.60 else "FAIL"}
    if allrows:
        pd.concat(allrows, ignore_index=True).to_csv(
            "results/P2/positives_outside_mapbiomas.csv", index=False)
    json.dump(out, open("results/P2/disagreement.json", "w"), indent=1)
    print("\nwrote results/P2/disagreement.json and positives_outside_mapbiomas.csv")

if __name__ == "__main__":
    main()
