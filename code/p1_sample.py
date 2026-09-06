"""TA04-P1 step 3/4 -- sample AEF-2019 (64) and the Stage-4 G2 74-feature classical
baseline at the SAME points, for one ROI.

The `rich()` stack below is copied from code/upstream/G2_sample.py (Stage-4 G2) so the
baseline is byte-for-byte the same 74 features:
  55 = 11 vars (B2 B3 B4 B8 B11 B12 NDVI NBR NDWI NDMI IOR) x 5 percentiles
   4 = intra-annual stdDev of NDVI NBR B8 B11
   5 = focal texture (B8_sd3 B8_sd7 NDVI_sd3 NDVI_sd7 B8_dev7)
   6 = S1 VV/VH x 3 percentiles
   2 = S1 VV/VH stdDev
   1 = VV_p50 - VH_p50
   1 = VV_p50 focal sd3
usage: python code/p1_sample.py TAP
"""
import ee, time, random, sys, os, json
import pandas as pd, numpy as np

for _ in range(60):
    try: ee.Initialize(); break
    except Exception: time.sleep(10 + random.random() * 15)

def rt(f, tag="", n=30):
    for a in range(n):
        try: return f()
        except Exception as e:
            s = str(e)
            if any(t in s for t in ("429", "Too Many", "imed out", "Internal error", "503",
                                    "Computation timed", "temporarily unavailable")):
                time.sleep(12 + random.random() * 20); continue
            print(tag, "ERR", s[:180], flush=True); return None
    print(tag, "GIVEUP", flush=True); return None

ROIS = {"TAP": [-58.0, -8.0, -54.0, -4.0],
        "MDD": [-71.0, -13.4, -69.4, -12.0],
        "GHA": [-3.2, 4.9, -0.9, 7.2]}
Y = 2019
AEFC = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")

def aef(y, r):
    return AEFC.filterDate(f"{y}-01-01", f"{y+1}-01-01").filterBounds(r).mosaic()

B = ["B2", "B3", "B4", "B8", "B11", "B12"]

def s2col(y, r):
    def m(i):
        q = i.select("QA60"); c = 1 << 10 | 1 << 11
        return i.updateMask(q.bitwiseAnd(c).eq(0)).divide(10000)
    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterDate(f"{y}-01-01", f"{y+1}-01-01").filterBounds(r)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 60)).map(m))

def idx(i):
    return (i.addBands(i.normalizedDifference(["B8", "B4"]).rename("NDVI"))
             .addBands(i.normalizedDifference(["B8", "B12"]).rename("NBR"))
             .addBands(i.normalizedDifference(["B3", "B8"]).rename("NDWI"))
             .addBands(i.normalizedDifference(["B11", "B8"]).rename("NDMI"))
             .addBands(i.expression("(b.B4-b.B2)/(b.B4+b.B2)", {"b": i}).rename("IOR")))

def rich(y, r):
    col = s2col(y, r).map(lambda i: idx(i.select(B)))
    bs = B + ["NDVI", "NBR", "NDWI", "NDMI", "IOR"]
    pc = col.select(bs).reduce(ee.Reducer.percentile([10, 25, 50, 75, 90]))
    sd = col.select(["NDVI", "NBR", "B8", "B11"]).reduce(ee.Reducer.stdDev())
    md = col.select(bs).median()
    tx = ee.Image.cat(
        md.select("B8").reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.square(3, "pixels")).rename("B8_sd3"),
        md.select("B8").reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.square(7, "pixels")).rename("B8_sd7"),
        md.select("NDVI").reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.square(3, "pixels")).rename("NDVI_sd3"),
        md.select("NDVI").reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.square(7, "pixels")).rename("NDVI_sd7"),
        md.select("B8").subtract(md.select("B8").reduceNeighborhood(
            ee.Reducer.mean(), ee.Kernel.square(7, "pixels"))).rename("B8_dev7"))
    s1 = (ee.ImageCollection("COPERNICUS/S1_GRD").filterDate(f"{y}-01-01", f"{y+1}-01-01")
          .filterBounds(r).filter(ee.Filter.eq("instrumentMode", "IW"))
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
          .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")).select(["VV", "VH"]))
    sp = s1.reduce(ee.Reducer.percentile([10, 50, 90]))
    ss = s1.reduce(ee.Reducer.stdDev())
    rat = sp.select("VV_p50").subtract(sp.select("VH_p50")).rename("VVVH_p50")
    st = sp.select("VV_p50").reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.square(3, "pixels")).rename("VV_sd3")
    return ee.Image.cat(pc, sd, tx, sp, ss, rat, st)

# MapBiomas garimpo/industrial agreement band (Amazon only; native 30 m)
MB = ("projects/mapbiomas-public/assets/brazil/lulc/collection10/"
      "mapbiomas_brazil_collection10_mining_substances_v3")

def main():
    k = sys.argv[1]
    CH = int(os.environ.get("CHUNK", 150))
    roi = ee.Geometry.Rectangle(ROIS[k])
    pts = pd.read_csv(f"data/points_{k}.csv")
    outf = f"data/samples_{k}.csv"
    done = set()
    if os.path.exists(outf):
        prev = pd.read_csv(outf); done = set(prev.id)
        print(f"{k} resuming, {len(done)} already sampled", flush=True)
    todo = pts[~pts.id.isin(done)].reset_index(drop=True)
    print(f"{k} points {len(pts)} todo {len(todo)}", flush=True)

    stack = aef(Y, roi).addBands(rich(Y, roi))
    if k == "TAP":
        # MapBiomas is Brazil-only. GOTCHA: .unmask(0) AFTER .reproject() does NOT extend the
        # asset footprint, so attaching this band outside Brazil silently drops points in
        # sampleRegions (measured: 21/60 returned in the Madre de Dios box, while AEF and all
        # 74 baseline features returned 60/60). Attached for TAP only -- which is also the only
        # ROI where the MapBiomas source-agreement comparison is meaningful.
        stack = stack.addBands(
            ee.Image(MB).select("classification_2019").reproject(crs="EPSG:4326", scale=30)
            .rename("mb_cid").unmask(0))

    t0 = time.time(); rows = []; nwritten = 0
    for i in range(0, len(todo), CH):
        ch = todo.iloc[i:i + CH]
        fcs = ee.FeatureCollection([
            ee.Feature(ee.Geometry.Point([r.lon, r.lat]),
                       {"id": r.id, "cls": int(r.cls), "sub": r.sub, "blk": r.blk})
            for r in ch.itertuples()])
        r = rt(lambda: stack.sampleRegions(collection=fcs, scale=10, geometries=False,
                                           tileScale=8).getInfo(), f"ch{i}")
        if r is None: continue
        for ft in r["features"]:
            rows.append(dict(ft["properties"]))
        if (i // CH) % 5 == 0 or i + CH >= len(todo):
            el = time.time() - t0
            print(f"{k} {i+len(ch)}/{len(todo)} rows={len(rows)} {el:.0f}s "
                  f"({el/max(1,i+len(ch))*1000:.1f} s/1000pt)", flush=True)
        if len(rows) >= 1500 or i + CH >= len(todo):
            df = pd.DataFrame(rows)
            df.to_csv(outf, mode="a", header=not os.path.exists(outf), index=False)
            nwritten += len(rows); rows = []
    print(f"{k} DONE appended {nwritten}; total file rows "
          f"{len(pd.read_csv(outf))}; wall {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
