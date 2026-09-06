"""TA04-P1 -- build the point sets (positives + WorldCover-stratified hard negatives).

Points are drawn LOCALLY with shapely so that no large geometry has to be pushed to
Earth Engine; EE is then used only for cheap point sampling. Negatives are >= 1 km from
ANY mining polygon in the ROI (Maus v2 union, plus the AMW union in the Amazon) and are
stratified by ESA WorldCover 2020 class so that bare soil, sandbars and built-up appear.
"""
import os, sys, json, time, random
import numpy as np, pandas as pd, geopandas as gpd
from shapely.ops import unary_union
from shapely.geometry import Point, box

ROIS = {"TAP": (-58.0, -8.0, -54.0, -4.0),
        "MDD": (-71.0, -13.4, -69.4, -12.0),
        "GHA": (-3.2, 4.9, -0.9, 7.2)}
AMAZON = ["TAP", "MDD"]
N_POS = int(os.environ.get("N_POS", 4000))
N_NEG = int(os.environ.get("N_NEG", 4000))
NEG_BUF_M = 1000.0
POS_ERODE_M = 30.0          # Stage-2 convention: 30 m inward erosion of positives
SEED = 20260906

# ESA WorldCover v100 classes; the hard negatives we insist on are 50/60/40/30/20/80.
WC = {10: "tree", 20: "shrub", 30: "grass", 40: "crop", 50: "built", 60: "bare",
      70: "snow", 80: "water", 90: "wetland", 95: "mangrove", 100: "moss"}
# Hard negatives we require: 60 bare soil, 50 built-up, 80 water (river sandbars),
# 40 cropland, 30 grassland, 20 shrubland, 90 wetland -- alongside 10 tree cover.

def aeqd(b):
    return (f"+proj=aeqd +lat_0={(b[1]+b[3])/2} +lon_0={(b[0]+b[2])/2} "
            f"+datum=WGS84 +units=m +no_defs")

def rand_in(geom, n, rng):
    """Uniform random points inside a (multi)polygon, area-weighted by rejection."""
    x0, y0, x1, y1 = geom.bounds
    out = []
    tries = 0
    while len(out) < n and tries < 400:
        m = max(4096, int((n - len(out)) * 3))
        xs = rng.uniform(x0, x1, m); ys = rng.uniform(y0, y1, m)
        cand = gpd.GeoSeries([Point(a, b) for a, b in zip(xs, ys)])
        keep = cand[cand.within(geom)]
        out.extend(list(keep))
        tries += 1
    return out[:n]

def wc_strat(box_ll, per_class=900, scale=30):
    """ESA WorldCover-stratified candidate points over the ROI RECTANGLE (server side).

    Sampling stratified by land cover has to happen in Earth Engine: bare soil, built-up
    and sandbars are ~0.1% of the Tapajos box, so uniform local sampling never reaches the
    hard-negative classes (a 16k-point uniform draw yielded 10 bare / 2 built). The >= 1 km
    exclusion from mining is then applied locally, because the Maus v2 + AMW union is not
    an Earth Engine asset.
    """
    import ee
    for _ in range(30):
        try: ee.Initialize(); break
        except Exception: time.sleep(8 + random.random() * 10)
    roi = ee.Geometry.Rectangle(list(box_ll))
    wc = ee.Image("ESA/WorldCover/v100/2020").select("Map").rename("wc")
    cls = [10, 20, 30, 40, 50, 60, 70, 80, 90, 95]
    # one call per class: getInfo() aborts a collection query above 5,000 elements
    out = []
    for c in cls:
        for att in range(10):
            try:
                d = wc.stratifiedSample(numPoints=0, classBand="wc", region=roi,
                                        scale=scale, seed=SEED % 100000, classValues=[c],
                                        classPoints=[per_class], geometries=True,
                                        dropNulls=True, tileScale=8).getInfo()
                break
            except Exception as e:
                if att == 9: raise
                time.sleep(12 + random.random() * 20)
        for f in d["features"]:
            xy = f["geometry"]["coordinates"]
            out.append({"lon": xy[0], "lat": xy[1], "wc": int(f["properties"]["wc"])})
    return pd.DataFrame(out)

def main():
    rng = np.random.default_rng(SEED)
    maus = gpd.read_file("data/maus_v2.gpkg")
    amw = pd.concat([gpd.read_file(f"data/amw_{y}.geojson") for y in (2019, 2020)],
                    ignore_index=True)
    amw = gpd.GeoDataFrame(amw, geometry="geometry", crs="EPSG:4326")

    for k, b in ROIS.items():
        crs = aeqd(b)
        roi_ll = box(*[b[0], b[1], b[2], b[3]])
        roi = gpd.GeoSeries([roi_ll], crs="EPSG:4326").to_crs(crs).iloc[0]

        # ---- positives -------------------------------------------------------
        if k in AMAZON:
            pf = gpd.read_file(f"data/refs/pos_{k}.geojson").to_crs(crs)
            frames = [("ASGM", unary_union(pf.geometry.values))]
        else:
            frames = []
            for nm in ("industrial", "unclassified"):
                g = gpd.read_file(f"data/refs/pos_GHA_{nm}.geojson").to_crs(crs)
                frames.append((nm, unary_union(g.geometry.values)))

        rows = []
        for nm, g in frames:
            ge = g.buffer(-POS_ERODE_M)
            if ge.is_empty: ge = g
            share = 1.0 if len(frames) == 1 else 0.5
            n = int(N_POS * share)
            pts = rand_in(ge, n, rng)
            ll = gpd.GeoSeries(pts, crs=crs).to_crs("EPSG:4326")
            for p in ll:
                rows.append({"roi": k, "cls": 1, "sub": nm, "lon": p.x, "lat": p.y})
            print(f"{k} positives[{nm}]: {len(pts)} (frame {g.area/1e6:.1f} km2)", flush=True)

        # ---- negative frame: >= 1 km from ANY mining polygon ------------------
        mm = maus.cx[b[0]:b[2], b[1]:b[3]].to_crs(crs)
        mine = [unary_union(mm.geometry.values)] if len(mm) else []
        if k in AMAZON:
            aa = amw.cx[b[0]:b[2], b[1]:b[3]].to_crs(crs)
            if len(aa): mine.append(unary_union(aa.geometry.values))
        excl = unary_union(mine).buffer(NEG_BUF_M) if mine else None
        negframe = roi.difference(excl) if excl is not None else roi
        print(f"{k} negative frame {negframe.area/1e6:.0f} km2 "
              f"({100*negframe.area/roi.area:.1f}% of ROI)", flush=True)

        cand = wc_strat(b)
        print(f"{k} WorldCover-stratified candidates {len(cand)}: "
              f"{ {WC.get(c,c): n for c, n in cand.wc.value_counts().items()} }", flush=True)
        cg = gpd.GeoDataFrame(cand, geometry=gpd.points_from_xy(cand.lon, cand.lat),
                              crs="EPSG:4326").to_crs(crs)
        keep = ~cg.geometry.intersects(excl) if excl is not None else np.ones(len(cg), bool)
        cdf = cand[np.asarray(keep)].reset_index(drop=True)
        print(f"{k} after >= 1 km mining exclusion: {len(cdf)} "
              f"({ {WC.get(c,c): n for c, n in cdf.wc.value_counts().items()} })", flush=True)

        # equal quota per available class; shortfall redistributed to the largest classes
        avail = cdf.wc.value_counts().to_dict()
        order = sorted(avail, key=lambda c: avail[c])          # scarcest first
        picks, left, remaining = [], N_NEG, len(order)
        for c in order:
            q = min(avail[c], int(np.ceil(left / remaining)))
            picks.append(cdf[cdf.wc == c].sample(q, random_state=SEED))
            left -= q; remaining -= 1
        neg = pd.concat(picks).head(N_NEG)
        for r in neg.itertuples():
            rows.append({"roi": k, "cls": 0, "sub": f"neg_{WC.get(r.wc, r.wc)}",
                         "lon": r.lon, "lat": r.lat})
        print(f"{k} negatives {len(neg)}: "
              f"{ {WC.get(c,c): n for c, n in neg.wc.value_counts().items()} }", flush=True)

        df = pd.DataFrame(rows)
        df["blk"] = (np.floor(df.lon / 0.5).astype(int).astype(str) + "_"
                     + np.floor(df.lat / 0.5).astype(int).astype(str))
        df["id"] = [f"{k}_{'P' if c else 'N'}{i:05d}" for i, c in enumerate(df.cls)]
        df.to_csv(f"data/points_{k}.csv", index=False)
        print(f"{k} WROTE data/points_{k}.csv n={len(df)} blocks={df.blk.nunique()}\n", flush=True)

if __name__ == "__main__":
    main()
