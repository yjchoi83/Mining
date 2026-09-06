"""TA04-P2 step 1 -- Arm E: erode the positive frame and draw the Arm-E positive points.

Non-forest rule (PLAN_P2 §1.1):  NDVI(S2-2019 annual median) < 0.5  OR  WorldCover 2020 != 10.
NDVI is taken from the annual-median bands so Arm E uses the identical composite as Arm U.

Rejection sampling doubles as the area estimator: acceptance rate x un-eroded frame area,
Wilson 95%.  Cheap 3-band screen only; the full 138-band stack is sampled later by p2_sample.py.
"""
import os, json, time, random, math, sys
import numpy as np, pandas as pd, geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Point

ROIS = {"TAP": (-58.0, -8.0, -54.0, -4.0),
        "MDD": (-71.0, -13.4, -69.4, -12.0),
        "GHA": (-3.2, 4.9, -0.9, 7.2)}
N_CAND = 16000
N_KEEP = 4000
SEED = 20260906

def aeqd(b):
    return (f"+proj=aeqd +lat_0={(b[1]+b[3])/2} +lon_0={(b[0]+b[2])/2} "
            f"+datum=WGS84 +units=m +no_defs")

def wilson(k, n, z=1.96):
    if n == 0: return (0.0, 0.0)
    p, d = k / n, 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (max(0.0, c - h), min(1.0, c + h))

def frame_parts(k):
    """(multi)polygon parts of the un-eroded positive frame, in the ROI's metric CRS."""
    crs = aeqd(ROIS[k])
    if k == "GHA":
        g = pd.concat([gpd.read_file(f"data/refs/pos_GHA_{n}.geojson") for n in
                       ("industrial", "unclassified")], ignore_index=True)
        g = gpd.GeoDataFrame(g, geometry="geometry", crs="EPSG:4326")
    else:
        g = gpd.read_file(f"data/refs/pos_{k}.geojson")
    u = unary_union(g.to_crs(crs).geometry.values)
    return crs, (list(u.geoms) if u.geom_type.startswith("Multi") else [u])

def screen(pts, chunk=4000):
    """EE 3-band screen: WorldCover Map + S2-2019 annual-median B4/B8 -> keep/drop + patch info."""
    import ee
    for _ in range(30):
        try: ee.Initialize(); break
        except Exception: time.sleep(8 + random.random() * 10)
    def msk(i):
        q = i.select("QA60"); c = 1 << 10 | 1 << 11
        return i.updateMask(q.bitwiseAnd(c).eq(0)).divide(10000)
    reg = ee.Geometry.Rectangle([-180, -60, 180, 60])
    s2 = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
          .filterDate("2019-01-01", "2020-01-01")
          .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)).map(msk))
    med = s2.select(["B4", "B8"]).median()
    img = med.addBands(ee.Image("ESA/WorldCover/v100/2020").select("Map").rename("wc").unmask(0))
    out = []
    for i in range(0, len(pts), chunk):
        ch = pts[i:i + chunk]
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry.Point([x, y]), {"j": i + n})
                                   for n, (x, y) in enumerate(ch)])
        for a in range(10):
            try:
                r = img.sampleRegions(collection=fc, scale=10, tileScale=8,
                                      geometries=False).getInfo(); break
            except Exception as e:
                if a == 9: raise
                time.sleep(12 + random.random() * 20)
        d = {f["properties"]["j"]: f["properties"] for f in r["features"]}
        for n in range(len(ch)):
            p = d.get(i + n)
            out.append(None if p is None else
                       (p.get("B4"), p.get("B8"), p.get("wc")))
        print(f"    screened {min(i+chunk, len(pts))}/{len(pts)}", flush=True)
    return out

def main():
    rng = np.random.default_rng(SEED)
    ref = json.load(open("results/P1/ref_summary.json"))
    summary = {}
    for k, b in ROIS.items():
        crs, parts = frame_parts(k)
        areas = np.array([p.area for p in parts])
        tot = areas.sum()
        print(f"{k}: un-eroded frame {tot/1e6:,.1f} km2 in {len(parts)} parts", flush=True)
        # area-weighted part choice, then uniform point inside that part
        w = areas / tot
        pts, pidx = [], []
        while len(pts) < N_CAND:
            need = N_CAND - len(pts)
            sel = rng.choice(len(parts), size=need, p=w)
            for si in sel:
                g = parts[si]; x0, y0, x1, y1 = g.bounds
                for _ in range(60):
                    p = Point(rng.uniform(x0, x1), rng.uniform(y0, y1))
                    if g.contains(p):
                        pts.append(p); pidx.append(si); break
        ll = gpd.GeoSeries(pts, crs=crs).to_crs("EPSG:4326")
        lonlat = [(p.x, p.y) for p in ll]
        print(f"{k}: screening {len(lonlat)} candidates...", flush=True)
        sc = screen(lonlat)
        rows = []
        for n, (s, (lo, la)) in enumerate(zip(sc, lonlat)):
            if s is None or s[0] is None or s[1] is None: continue
            b4, b8, wc = s
            ndvi = (b8 - b4) / (b8 + b4) if (b8 + b4) else np.nan
            rows.append({"lon": lo, "lat": la, "ndvi_med": ndvi, "wc": int(wc or 0),
                         "part": pidx[n], "patch_km2": areas[pidx[n]] / 1e6})
        c = pd.DataFrame(rows)
        c["nonforest"] = (c.ndvi_med < 0.5) | (c.wc != 10)
        nk, nn = int(c.nonforest.sum()), len(c)
        lo_, hi_ = wilson(nk, nn)
        er = nk / nn * tot / 1e6
        rec = {"uneroded_km2": tot / 1e6, "n_screened": nn, "n_nonforest": nk,
               "acceptance": nk / nn, "acceptance_ci": [lo_, hi_],
               "eroded_km2": er, "eroded_km2_ci": [lo_ * tot / 1e6, hi_ * tot / 1e6],
               "removed_km2": tot / 1e6 - er, "removed_share": 1 - nk / nn,
               "n_parts": len(parts)}
        print(f"{k}: eroded {er:,.1f} km2 of {tot/1e6:,.1f} "
              f"(keep {100*nk/nn:.1f}% [{100*lo_:.1f}-{100*hi_:.1f}], "
              f"REMOVED {100*(1-nk/nn):.1f}%)", flush=True)
        summary[k] = rec
        c.to_csv(f"data/p2_cand_{k}.csv", index=False)
        keep = c[c.nonforest].sample(min(N_KEEP, nk), random_state=SEED).reset_index(drop=True)
        keep["blk"] = (np.floor(keep.lon / 0.5).astype(int).astype(str) + "_"
                       + np.floor(keep.lat / 0.5).astype(int).astype(str))
        keep["id"] = [f"{k}_E{i:05d}" for i in range(len(keep))]
        keep["cls"] = 1
        keep["sub"] = "ASGM_eroded" if k != "GHA" else "eroded"
        keep["roi"] = k
        keep[["roi", "cls", "sub", "lon", "lat", "blk", "id", "ndvi_med", "wc", "patch_km2"]] \
            .to_csv(f"data/p2_points_{k}.csv", index=False)
        print(f"{k}: WROTE data/p2_points_{k}.csv n={len(keep)} blocks={keep.blk.nunique()}\n",
              flush=True)
    json.dump(summary, open("results/P2/frame_erosion.json", "w"), indent=1)
    pd.DataFrame(summary).T.to_csv("results/P2/frame_erosion.csv")
    print("wrote results/P2/frame_erosion.json/.csv")

if __name__ == "__main__":
    main()
