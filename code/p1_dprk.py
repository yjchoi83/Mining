"""TA04-P1 step 1d / step 5 -- DPRK feasibility (counts only, NO training in this package)."""
import ee, json, os, time, random
import numpy as np, pandas as pd, geopandas as gpd
for _ in range(30):
    try: ee.Initialize(); break
    except Exception: time.sleep(8 + random.random() * 10)

NK_BOX = [124.0, 37.5, 131.2, 43.1]
nk = ee.Geometry.Rectangle(NK_BOX)
# authoritative national boundary rather than a bbox
lsib = ee.FeatureCollection("USDOS/LSIB_SIMPLE/2017").filter(ee.Filter.eq("country_na", "Korea, North"))
nk_geom = lsib.geometry()

T = ee.FeatureCollection("projects/sat-io/open-datasets/global-mining/global_mining_footprints")
t_nk = T.filterBounds(nk_geom)
n_t = t_nk.size().getInfo()
print("Tang & Werner global_mining_footprints inside DPRK:", n_t, flush=True)

def enrich(f):
    c = f.geometry().centroid(50)
    return f.set("lon", c.coordinates().get(0), "lat", c.coordinates().get(1),
                 "area_km2", f.geometry().area(50).divide(1e6))

t_top = t_nk.map(enrich).sort("area_km2", False).limit(60)
tl = t_top.select(["Name", "lon", "lat", "area_km2"], None, False).getInfo()
tw = [{"source": "TangWerner", "name": str(f["properties"].get("Name")),
       "lon": round(f["properties"]["lon"], 5), "lat": round(f["properties"]["lat"], 5),
       "area_km2": round(f["properties"]["area_km2"], 4)} for f in tl["features"]]

# Maus v2 from the local PANGAEA copy (the GEE asset is v1)
maus = gpd.read_file("data/maus_v2.gpkg")
mk = maus[maus.ISO3_CODE == "PRK"].copy()
crs = "+proj=aeqd +lat_0=40 +lon_0=127 +datum=WGS84 +units=m +no_defs"
mkm = mk.to_crs(crs)
mk["area_km2"] = mkm.geometry.area / 1e6
cen = mkm.geometry.centroid.to_crs("EPSG:4326")
mk["lon"], mk["lat"] = cen.x.values, cen.y.values
mk = mk.sort_values("area_km2", ascending=False)
print("Maus v2 polygons in DPRK:", len(mk), "total km2", round(mk.area_km2.sum(), 2), flush=True)
mv = [{"source": "MausV2", "name": "", "lon": round(r.lon, 5), "lat": round(r.lat, 5),
       "area_km2": round(r.area_km2, 4)} for r in mk.itertuples()]

allp = sorted(tw + mv, key=lambda z: -z["area_km2"])
top20 = allp[:20]
print("\nTop 20 largest DPRK mining polygons (either source):")
for i, p in enumerate(top20, 1):
    print(f" {i:2d}. {p['source']:11s} {p['area_km2']:9.3f} km2  lon {p['lon']:9.4f} lat {p['lat']:8.4f}")

def dist(v):
    v = np.array(v)
    return {"n": int(len(v)), "min": float(v.min()), "p25": float(np.percentile(v, 25)),
            "median": float(np.median(v)), "p75": float(np.percentile(v, 75)),
            "p95": float(np.percentile(v, 95)), "max": float(v.max()), "sum": float(v.sum())}

out = {"boundary": "USDOS/LSIB_SIMPLE/2017 country_na='Korea, North'",
       "tang_werner_n": n_t,
       "maus_v2_n": int(len(mk)), "maus_v2_total_km2": float(mk.area_km2.sum()),
       "maus_v2_size_km2": dist(mk.area_km2.values) if len(mk) else None,
       "tang_werner_size_km2_top60": dist([p["area_km2"] for p in tw]) if tw else None,
       "tang_werner_names_are_informative": sorted({p["name"] for p in tw})[:12],
       "top20": top20}
os.makedirs("results/P1", exist_ok=True)
json.dump(out, open("results/P1/dprk_summary.json", "w"), indent=1)
pd.DataFrame(allp).to_csv("results/P1/dprk_polygons.csv", index=False)
print("\nwrote results/P1/dprk_summary.json and dprk_polygons.csv")
