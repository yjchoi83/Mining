"""TA04-P1 step 1c -- MapBiomas mining module: does it separate garimpo from industrial?

Codebook (ATBD Collection 10, Mining Appendix, Table 3):
  1xx = "2. Industrial"  (102 Iron, 107 Titanium, 109 Copper, 110 Aluminum, 114 Tin,
                          115 Gold, 122 Limestone, 130 Zinc, ...)
  2xx = "1. Garimpo"     (214 Tin, 215 GOLD, 216/217 Non-metallics, 223/224/225 gems)
=> YES, garimpo is separated. 215 (garimpo gold) is the ASGM class for the Amazon.

GOTCHA: reduceRegion at a scale coarser than the asset's 30 m makes Earth Engine
MEAN-aggregate the class ids, which manufactures fake ids (53/107/161 = 1/4,1/2,3/4 of
215). Everything below is forced to native 30 m with .reproject().
"""
import ee, json, os, time, random
for _ in range(30):
    try: ee.Initialize(); break
    except Exception: time.sleep(8 + random.random() * 10)

ASSET = ("projects/mapbiomas-public/assets/brazil/lulc/collection10/"
         "mapbiomas_brazil_collection10_mining_substances_v3")
TAP = ee.Geometry.Rectangle([-58.0, -8.0, -54.0, -4.0])
base = ee.Image(ASSET).select("classification_2019").rename("cid")
img = base.reproject(crs="EPSG:4326", scale=30)

GARIMPO = [214, 215, 216, 217, 223, 224, 225]
INDUSTRIAL = list(range(101, 131))

def area_km2(mask):
    a = ee.Image.pixelArea().updateMask(mask).reduceRegion(
        reducer=ee.Reducer.sum(), geometry=TAP, scale=30, maxPixels=1e13, tileScale=16)
    return ee.Number(a.get("area")).divide(1e6)

cid = img
g = cid.remap(GARIMPO, [1] * len(GARIMPO), 0).selfMask()
i = cid.remap(INDUSTRIAL, [1] * len(INDUSTRIAL), 0).selfMask()
gold = cid.eq(215).selfMask()

res = ee.Dictionary({
    "garimpo_all_km2": area_km2(g),
    "garimpo_gold_215_km2": area_km2(gold),
    "industrial_all_km2": area_km2(i),
}).getInfo()
print("MapBiomas mining, TAP box, 2019, native 30 m:")
for k, v in res.items():
    print(f"  {k:26s} {v:9.1f}")

out = {"asset": ASSET, "band": "classification_2019", "roi_TAP": [-58, -8, -54, -4],
       "separates_garimpo": True,
       "codebook": "ATBD Collection 10 Mining Appendix Table 3: 1xx = Industrial, 2xx = Garimpo; 215 = Garimpo Gold",
       "areas_km2": {k: round(v, 2) for k, v in res.items()}}
os.makedirs("results/P1", exist_ok=True)
json.dump(out, open("results/P1/mapbiomas_classids.json", "w"), indent=1)
print("wrote results/P1/mapbiomas_classids.json")
