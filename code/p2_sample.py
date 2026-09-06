"""TA04-P2 -- sample AEF64 + the Stage-4 G2 74 features at the Arm-E positive points.
Reuses the P1 sampler's stack definitions verbatim so Arm U and Arm E differ ONLY in where
the points are, never in how the features are built.   usage: python code/p2_sample.py TAP
"""
import sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import pandas as pd, ee
import p1_sample as ps            # ee.Initialize() happens there

def main():
    k = sys.argv[1]
    CH = int(os.environ.get("CHUNK", 150))
    roi = ee.Geometry.Rectangle(ps.ROIS[k])
    pts = pd.read_csv(f"data/p2_points_{k}.csv")
    outf = f"data/p2_samples_{k}.csv"
    done = set()
    if os.path.exists(outf):
        done = set(pd.read_csv(outf).id)
        print(f"{k} resuming, {len(done)} already sampled", flush=True)
    todo = pts[~pts.id.isin(done)].reset_index(drop=True)
    print(f"{k} arm-E points {len(pts)} todo {len(todo)}", flush=True)

    stack = ps.aef(ps.Y, roi).addBands(ps.rich(ps.Y, roi))
    if k == "TAP":                # MapBiomas is Brazil-only (P1 gotcha)
        stack = stack.addBands(
            ee.Image(ps.MB).select("classification_2019").reproject(crs="EPSG:4326", scale=30)
            .rename("mb_cid").unmask(0))
    t0, rows, nw = time.time(), [], 0
    for i in range(0, len(todo), CH):
        ch = todo.iloc[i:i + CH]
        fcs = ee.FeatureCollection([
            ee.Feature(ee.Geometry.Point([r.lon, r.lat]),
                       {"id": r.id, "cls": int(r.cls), "sub": r.sub, "blk": r.blk})
            for r in ch.itertuples()])
        r = ps.rt(lambda: stack.sampleRegions(collection=fcs, scale=10, geometries=False,
                                              tileScale=8).getInfo(), f"ch{i}")
        if r is None: continue
        rows += [dict(f["properties"]) for f in r["features"]]
        if (i // CH) % 5 == 0 or i + CH >= len(todo):
            el = time.time() - t0
            print(f"{k} {i+len(ch)}/{len(todo)} rows={len(rows)} {el:.0f}s "
                  f"({el/max(1,i+len(ch))*1000:.1f} s/1000pt)", flush=True)
        if len(rows) >= 1500 or i + CH >= len(todo):
            pd.DataFrame(rows).to_csv(outf, mode="a", header=not os.path.exists(outf), index=False)
            nw += len(rows); rows = []
    print(f"{k} DONE appended {nw}; file rows {len(pd.read_csv(outf))}; "
          f"wall {time.time()-t0:.0f}s", flush=True)

if __name__ == "__main__":
    main()
