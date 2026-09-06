"""Shared Stage-2 pilot helpers (throwaway). ee.Initialize() already handled here."""
import ee, numpy as np, pandas as pd
ee.Initialize()
AEF = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")

def aef(y, roi):
    return AEF.filterDate(f"{y}-01-01", f"{y+1}-01-01").filterBounds(roi).mosaic()

def s2(y, roi):
    def msk(i):
        s = i.select('QA60'); c = 1 << 10 | 1 << 11
        return i.updateMask(s.bitwiseAnd(c).eq(0)).divide(10000)
    col = (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
           .filterDate(f"{y}-01-01", f"{y+1}-01-01").filterBounds(roi)
           .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 60)).map(msk))
    m = col.select(['B2','B3','B4','B8','B11','B12']).median()
    ndvi = m.normalizedDifference(['B8','B4']).rename('NDVI')
    nbr = m.normalizedDifference(['B8','B12']).rename('NBR')
    return m.addBands(ndvi).addBands(nbr)

def angle(y1, y2, roi):
    d = aef(y1, roi).multiply(aef(y2, roi)).reduce(ee.Reducer.sum())
    return d.clamp(-1, 1).acos().multiply(180/np.pi).rename('angle_deg')

def samp(img, roi, n=3000, scale=10, seed=1, strata=None, classes=None, per_class=500):
    """DataFrame of lon/lat + band columns. randomPoints+sampleRegions (mosaics have no
    fixed projection, so img.sample(numPixels=) silently under-returns). Keep n<=5000."""
    if strata is not None:
        f = img.addBands(strata.rename('strat')).stratifiedSample(
            numPoints=per_class, classBand='strat', region=roi, scale=scale, seed=seed,
            classValues=classes, classPoints=[per_class]*len(classes),
            geometries=True, dropNulls=True, tileScale=4)
    else:
        pts = ee.FeatureCollection.randomPoints(region=roi, points=n, seed=seed)
        f = img.sampleRegions(collection=pts, scale=scale, geometries=True, tileScale=4)
    rows = f.getInfo()['features']
    out = []
    for r in rows:
        d = dict(r['properties']); c = r['geometry']['coordinates']
        d['lon'], d['lat'] = c[0], c[1]; out.append(d)
    return pd.DataFrame(out)

def blocks(df, size=0.1):
    return (np.floor(df.lon/size).astype(int).astype(str) + '_' +
            np.floor(df.lat/size).astype(int).astype(str))

def probe(df, feats, target, groups, task='clf', C=1.0, folds=5):
    """GroupKFold linear probe. Returns (mean, sd, per-fold list, n)."""
    from sklearn.model_selection import GroupKFold
    from sklearn.linear_model import LogisticRegression, Ridge
    from sklearn.metrics import balanced_accuracy_score, r2_score, roc_auc_score
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    d = df.dropna(subset=feats+[target]).copy()
    X, y, g = d[feats].values, d[target].values, groups.loc[d.index].values
    k = min(folds, len(np.unique(g)))
    sc = []
    for tr, te in GroupKFold(n_splits=k).split(X, y, g):
        if task == 'clf':
            if len(np.unique(y[tr])) < 2 or len(np.unique(y[te])) < 2: continue
            m = make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, C=C,
                              class_weight='balanced')).fit(X[tr], y[tr])
            if len(np.unique(y)) == 2:
                sc.append(roc_auc_score(y[te], m.predict_proba(X[te])[:, 1]))
            else:
                sc.append(balanced_accuracy_score(y[te], m.predict(X[te])))
        else:
            m = make_pipeline(StandardScaler(), Ridge(alpha=1.0)).fit(X[tr], y[tr])
            sc.append(r2_score(y[te], m.predict(X[te])))
    return (float(np.mean(sc)), float(np.std(sc)), [round(s, 3) for s in sc], len(d))

# GOTCHA: label rasters (Hansen lossyear, TMF, etc.) are masked outside their positive
# class -> sampleRegions silently drops those points. ALWAYS .unmask(0) a label band.
# Latest Hansen: UMD/hansen/global_forest_change_2025_v1_13 (v1_12 is superseded).
AEF_BANDS = [f"A{i:02d}" for i in range(64)]
S2_BANDS = ['B2','B3','B4','B8','B11','B12','NDVI','NBR']
