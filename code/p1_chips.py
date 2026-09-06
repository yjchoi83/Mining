"""TA04-P1 step 2 -- reference purity QC chips.

Sentinel-2 2019 annual-median RGB, 1 x 1 km at 10 m (100 x 100 px), with the reference
polygon outline burnt in, one PNG per id under results/P1/qc_chips/.
Thumbnails only (getThumbURL) -- no image exports.

Chip inventory (160):
  50  Amazon ASGM positives   (stratified across TAP / MDD by positive-frame area)
  30  Ghana positives         (15 industrial-flagged + 15 unclassified)
  <=50 DPRK polygons          (all, capped at 50, largest first)
  30  hard negatives          (WorldCover-stratified, >= 1 km from any mining polygon)
"""
import os, io, json, time, random, sys
import numpy as np, pandas as pd, geopandas as gpd, requests
import ee
from shapely.ops import unary_union
from shapely.geometry import mapping

for _ in range(30):
    try: ee.Initialize(); break
    except Exception: time.sleep(8 + random.random() * 10)

OUT = "results/P1/qc_chips"
os.makedirs(OUT, exist_ok=True)
HALF_DEG = 500.0 / 111320.0          # ~500 m in degrees latitude -> 1 x 1 km chip
SEED = 20260906
VIS = {"bands": ["B4", "B3", "B2"], "min": 200, "max": 2500}

def s2_median(year, region):
    def msk(i):
        q = i.select("QA60"); c = (1 << 10) | (1 << 11)
        return i.updateMask(q.bitwiseAnd(c).eq(0))
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterDate(f"{year}-01-01", f"{year+1}-01-01").filterBounds(region)
           .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)).map(msk))
    return col.select(["B4", "B3", "B2"]).median()

def chip(lon, lat, geom_ll, path, retries=6):
    dlat = HALF_DEG
    dlon = HALF_DEG / max(0.2, np.cos(np.radians(lat)))
    reg = ee.Geometry.Rectangle([lon - dlon, lat - dlat, lon + dlon, lat + dlat], None, False)
    img = s2_median(2019, reg).visualize(**VIS)
    if geom_ll is not None:
        fc = ee.FeatureCollection([ee.Feature(ee.Geometry(mapping(geom_ll)), {})])
        outline = ee.Image().byte().paint(fc, 1, 2)            # 2 px yellow outline
        img = img.blend(outline.visualize(palette=["FFFF00"]).updateMask(outline))
    url = img.getThumbURL({"region": reg, "dimensions": "100x100", "format": "png"})
    for a in range(retries):
        try:
            r = requests.get(url, timeout=120)
            if r.status_code == 200 and r.content[:4] == b"\x89PNG":
                open(path, "wb").write(r.content); return True
        except Exception:
            pass
        time.sleep(5 + random.random() * 10)
    return False

def parts(geom):
    return list(geom.geoms) if geom.geom_type.startswith("Multi") else [geom]

def main():
    rng = np.random.default_rng(SEED)
    rows = []

    # ---------- 50 Amazon ASGM positives, stratified by ROI ----------
    frames = {}
    for k in ("TAP", "MDD"):
        g = gpd.read_file(f"data/refs/pos_{k}.geojson")
        frames[k] = parts(unary_union(g.geometry.values))
    aream = {k: sum(p.area for p in v) for k, v in frames.items()}
    tot = sum(aream.values())
    quota = {k: max(5, int(round(50 * aream[k] / tot))) for k in frames}
    # keep the total at 50
    ks = sorted(quota, key=lambda z: -quota[z]); quota[ks[0]] += 50 - sum(quota.values())
    for k, q in quota.items():
        ps = sorted(frames[k], key=lambda p: -p.area)
        idx = np.unique(np.linspace(0, len(ps) - 1, min(q, len(ps))).round().astype(int))
        if len(idx) < q:      # MDD: one big part -> take q random interior points of it
            big = ps[0]
            x0, y0, x1, y1 = big.bounds
            pts, tries = [], 0
            while len(pts) < q and tries < 500:
                from shapely.geometry import Point
                p = Point(rng.uniform(x0, x1), rng.uniform(y0, y1))
                if big.contains(p): pts.append(p)
                tries += 1
            for j, p in enumerate(pts):
                rows.append({"id": f"{k}_ASGM_{j:03d}", "region": k,
                             "source": "MausV2 x AMW2019-20", "proposed_label": "ASGM",
                             "lon": p.x, "lat": p.y, "geom": big})
        else:
            for j, i in enumerate(idx):
                c = ps[i].representative_point()
                rows.append({"id": f"{k}_ASGM_{j:03d}", "region": k,
                             "source": "MausV2 x AMW2019-20", "proposed_label": "ASGM",
                             "lon": c.x, "lat": c.y, "geom": ps[i]})

    # ---------- 30 Ghana positives: 15 industrial + 15 unclassified ----------
    gref = gpd.read_file("data/refs/ref_GHA.geojson")
    for lab, n in (("industrial", 15), ("mining, unclassified", 15)):
        sub = gref[gref.proposed_label == lab].sort_values("area_km2", ascending=False)
        idx = np.unique(np.linspace(0, len(sub) - 1, min(n, len(sub))).round().astype(int))
        for j, i in enumerate(idx):
            r = sub.iloc[i]
            c = r.geometry.representative_point()
            rows.append({"id": f"GHA_{'IND' if lab=='industrial' else 'UNC'}_{j:03d}",
                         "region": "GHA", "source": "MausV2 (GHA box)",
                         "proposed_label": lab, "lon": c.x, "lat": c.y, "geom": r.geometry})

    # ---------- DPRK: all polygons, cap 50 ----------
    dp = pd.read_csv("results/P1/dprk_polygons.csv")
    dp = dp.drop_duplicates(subset=["lon", "lat"]).sort_values("area_km2", ascending=False).head(50)
    maus = gpd.read_file("data/maus_v2.gpkg"); mk = maus[maus.ISO3_CODE == "PRK"]
    for j, r in enumerate(dp.itertuples()):
        hit = mk[mk.geometry.intersects(gpd.points_from_xy([r.lon], [r.lat])[0])]
        rows.append({"id": f"PRK_{j:03d}", "region": "PRK", "source": r.source,
                     "proposed_label": "mining, unclassified (data-denied)",
                     "lon": r.lon, "lat": r.lat,
                     "geom": hit.geometry.iloc[0] if len(hit) else None})

    # ---------- 30 hard negatives ----------
    neg = []
    for k in ("TAP", "MDD", "GHA"):
        d = pd.read_csv(f"data/points_{k}.csv")
        neg.append(d[d.cls == 0])
    neg = pd.concat(neg, ignore_index=True)
    take = pd.concat([g.sample(min(len(g), 6), random_state=SEED)
                      for _, g in neg.groupby("sub")], ignore_index=True)
    take = take.sample(min(30, len(take)), random_state=SEED).reset_index(drop=True)
    for j, r in enumerate(take.itertuples()):
        rows.append({"id": f"NEG_{j:03d}", "region": r.roi, "source": f"background/{r.sub}",
                     "proposed_label": "not mining", "lon": r.lon, "lat": r.lat, "geom": None})

    print(f"chip inventory: {len(rows)}", flush=True)
    ok = 0
    for i, r in enumerate(rows):
        p = os.path.join(OUT, f"{r['id']}.png")
        if os.path.exists(p) and os.path.getsize(p) > 200:
            ok += 1; r["chip"] = True; continue
        r["chip"] = chip(r["lon"], r["lat"], r.get("geom"), p)
        ok += bool(r["chip"])
        if i % 10 == 0: print(f"  {i}/{len(rows)} ok={ok}", flush=True)
    print(f"chips written {ok}/{len(rows)}", flush=True)

    tab = pd.DataFrame([{"id": r["id"], "region": r["region"], "source": r["source"],
                         "proposed_label": r["proposed_label"], "decision": "",
                         "notes": (f"lon={r['lon']:.5f} lat={r['lat']:.5f}; "
                                   f"chip={'yes' if r['chip'] else 'FAILED'}; "
                                   f"outline={'yes' if r.get('geom') is not None else 'no polygon'}")}
                        for r in rows])
    tab.to_csv("results/P1/qc_table.csv", index=False)
    sz = sum(os.path.getsize(os.path.join(OUT, f)) for f in os.listdir(OUT))
    print(f"wrote results/P1/qc_table.csv ({len(tab)} rows); chip dir {sz/1e6:.2f} MB", flush=True)
    json.dump({"n_chips": ok, "n_rows": len(tab), "chip_dir_bytes": sz},
              open("results/P1/qc_chip_inventory.json", "w"), indent=1)

if __name__ == "__main__":
    main()
