"""TA04-P2 step 4 -- classifier-dependence grid.

4 classifiers x 2 feature sets x arms U/E, label budgets {10..2000}, 20 draws,
5-fold GroupKFold on 0.5-degree blocks, ROC-AUC, block bootstrap (1,000 draws, blocks
resampled WITH multiplicity).

usage: python code/p2_analysis.py <task> <arm> [tag] [--excl-uncertain] [--landscape-neg]
       task in {amazon, gha_ind, gha_unc}   arm in {U, E}
"""
import os, sys, json, itertools, time
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from scipy.stats import rankdata
import lightgbm as lgb

AEF = [f"A{i:02d}" for i in range(64)]
NS = [10, 20, 40, 80, 160, 320, 640, 1000, 2000]
DRAWS, FOLDS, BOOT, BOOT_DRAWS, K_REF = 20, 5, 1000, 8, 40
SEED = 20260906
NONFEAT = {"id", "cls", "sub", "blk", "lon", "lat", "roi", "mb_cid",
           "ndvi_med", "wc", "patch_km2", "sub_new", "poly", "industrial_new",
           # `wc_name` is a scratch column built by the landscape-negative reweighting (S2).
           # It exists on the negatives only, so if it is left in the feature list every
           # POSITIVE row is NaN there and dropna() silently deletes the entire positive
           # class (observed: pos=0 on the first S2 run). Must stay excluded.
           "wc_name"}
CLFS = ("log", "lgbm", "knn", "mlp")

def fast_auc(y, s):
    n1 = int(y.sum()); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return np.nan
    r = rankdata(s)
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)

def model(kind, fs):
    if kind == "log":
        return make_pipeline(StandardScaler(),
                             LogisticRegression(max_iter=3000, C=1.0, class_weight="balanced"))
    if kind == "lgbm":
        return lgb.LGBMClassifier(n_estimators=150, num_leaves=7, min_child_samples=5,
                                  learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                                  reg_lambda=1.0, is_unbalance=True, verbosity=-1, random_state=0)
    if kind == "knn":
        # PLAN_P2 §1.5: cosine kNN k=15 on RAW AEF64, on STANDARDISED BASE74
        knn = KNeighborsClassifier(n_neighbors=15, metric="cosine", weights="distance")
        return knn if fs == "AEF64" else make_pipeline(StandardScaler(), knn)
    return make_pipeline(StandardScaler(),
                         MLPClassifier(hidden_layer_sizes=(128, 128), max_iter=400,
                                       early_stopping=True, n_iter_no_change=15,
                                       random_state=0))

def fit_pred(kind, fs, Xtr, ytr, Xte):
    if len(np.unique(ytr)) < 2: return None
    k = min(15, int(np.bincount(ytr).min()))
    if kind == "knn" and k < 1: return None
    m = model(kind, fs)
    if kind == "knn" and k < 15:                      # tiny budgets: shrink k, never crash
        (m if not hasattr(m, "steps") else m.steps[-1][1]).set_params(n_neighbors=k)
    try:
        m.fit(Xtr, ytr)
        return m.predict_proba(Xte)[:, 1]
    except Exception:
        return None

def load(task, arm, excl_uncertain=False, landscape_neg=False):
    """Arm U = P1 points as is. Arm E = P1 NEGATIVES + Arm-E positives (positives swapped only)."""
    rois = ["TAP", "MDD"] if task == "amazon" else ["GHA"]
    base = pd.concat([pd.read_csv(f"data/samples_{k}.csv") for k in rois], ignore_index=True)
    xy = pd.concat([pd.read_csv(f"data/points_{k}.csv")[["id", "lon", "lat"]] for k in rois],
                   ignore_index=True)
    base = base.merge(xy, on="id", how="left")
    neg = base[base.cls == 0].copy()
    if arm == "U":
        pos = base[base.cls == 1].copy()
    else:
        pos = pd.concat([pd.read_csv(f"data/p2_samples_{k}.csv") for k in rois], ignore_index=True)
        pxy = pd.concat([pd.read_csv(f"data/p2_points_{k}.csv")[["id", "lon", "lat"]]
                         for k in rois], ignore_index=True)
        pos = pos.merge(pxy, on="id", how="left")
    if task.startswith("gha"):
        rl = pd.read_csv("data/p2_gha_relabel.csv")[["id", "sub_new"]]
        if arm == "U":
            pos = pos.merge(rl, on="id", how="left")
            want = "industrial" if task == "gha_ind" else "unclassified"
            pos = pos[pos.sub_new.fillna("unclassified") == want]
        # arm E Ghana positives are drawn from the whole Ghana frame; split them by the same
        # polygon rule via nearest flagged polygon is not available, so arm E Ghana is
        # reported UNSPLIT and the split is an arm-U-only sensitivity (logged).
    if excl_uncertain:
        ex = json.load(open("results/P2/uncertain_exclusion.json"))
        pos = pos[~pos.id.isin(ex.get(task, {}).get(arm, []))]
    if landscape_neg:
        w = json.load(open("results/P2/landscape_weights.json"))
        neg["wc_name"] = neg["sub"].str.replace("neg_", "", regex=False)
        pr = pd.Series({k: v for k, v in w.items()})
        keep = []
        rng = np.random.default_rng(SEED)
        n_tot = len(neg)
        for c, g in neg.groupby("wc_name"):
            n_want = int(round(pr.get(c, 0) * n_tot))
            if n_want == 0: continue
            keep.append(g.sample(min(n_want, len(g)), random_state=SEED) if n_want <= len(g)
                        else g.sample(n_want, replace=True, random_state=SEED))
        neg = pd.concat(keep, ignore_index=True) if keep else neg
    d = pd.concat([pos, neg], ignore_index=True)
    feats = [c for c in d.columns if c not in NONFEAT]
    basef = [c for c in feats if c not in AEF]
    d = d.dropna(subset=AEF + basef).reset_index(drop=True)
    d["pos"] = d.cls.astype(int)
    return d, basef

def run(d, basef, tag, clfs):
    gk = GroupKFold(n_splits=FOLDS)
    folds = list(gk.split(d, d.pos, d.blk))
    store, tidx = {}, {}
    for fi, (tr, te) in enumerate(folds):
        tidx[fi] = te
        dtr, dte = d.iloc[tr], d.iloc[te]
        for fs_name, fs in (("AEF64", AEF), ("BASE74", basef)):
            Xtr, Xte, ytr = dtr[fs].values, dte[fs].values, dtr.pos.values
            pi, qi = np.where(ytr == 1)[0], np.where(ytr == 0)[0]
            for mdl in clfs:
                p = fit_pred(mdl, fs_name, Xtr, ytr, Xte)
                if p is not None: store[(fs_name, mdl, "full", 0, fi)] = p.astype(np.float32)
                for n in NS:
                    if n > len(dtr): continue
                    for s in range(DRAWS):
                        rs = np.random.RandomState(SEED % 9999 + 1000 * s + n)
                        npz = max(4, int(round(n * ytr.mean()))); nnz = n - npz
                        if npz > len(pi) or nnz > len(qi) or nnz < 4: continue
                        idx = np.concatenate([rs.choice(pi, npz, False), rs.choice(qi, nnz, False)])
                        pp = fit_pred(mdl, fs_name, Xtr[idx], ytr[idx], Xte)
                        if pp is not None: store[(fs_name, mdl, n, s, fi)] = pp.astype(np.float32)
        print(f"  [{tag}] fold {fi+1}/{FOLDS}, {len(store)} vectors", flush=True)
    return store, tidx

def curve_means(store, tidx, y, rep=None, max_draw=None):
    out = {}
    for (fs, mdl, n, s, fi), p in store.items():
        if max_draw is not None and n != "full" and s >= max_draw: continue
        te = tidx[fi]
        if rep is not None:
            sel = rep[fi]
            if len(sel) < 20: continue
            a = fast_auc(y[te][sel], p[sel])
        else:
            a = fast_auc(y[te], p)
        if not np.isnan(a): out.setdefault((fs, mdl, n), []).append(a)
    return {k: float(np.mean(v)) for k, v in out.items()}

def ratio_from(means, mdl):
    tgt = means.get(("AEF64", mdl, K_REF))
    if tgt is None: return None, None, "no AEF@40"
    ns = [n for n in NS if ("BASE74", mdl, n) in means]
    ys = [means[("BASE74", mdl, n)] for n in ns]
    if not ns: return None, tgt, "no baseline"
    if ys[0] >= tgt: return float(ns[0] / K_REF), tgt, "reached at smallest budget"
    for i in range(1, len(ns)):
        if ys[i] >= tgt:
            x0, x1 = np.log(ns[i - 1]), np.log(ns[i])
            f = (tgt - ys[i - 1]) / (ys[i] - ys[i - 1]) if ys[i] != ys[i - 1] else 1.0
            return float(np.exp(x0 + f * (x1 - x0)) / K_REF), tgt, "interpolated"
    return float(NS[-1] / K_REF), tgt, f"censored_at_{NS[-1]}"

def main():
    task, arm = sys.argv[1], sys.argv[2]
    tag = sys.argv[3] if len(sys.argv) > 3 and not sys.argv[3].startswith("--") else f"{task}_{arm}"
    excl = "--excl-uncertain" in sys.argv
    land = "--landscape-neg" in sys.argv
    clfs = ("log", "lgbm") if (excl or land) else CLFS     # §1.7 pre-registered restriction
    d, basef = load(task, arm, excl, land)
    print(f"[{tag}] n={len(d)} pos={int(d.pos.sum())} neg={int((1-d.pos).sum())} "
          f"blocks={d.blk.nunique()} basefeats={len(basef)} clfs={clfs}", flush=True)
    store, tidx = run(d, basef, tag, clfs)
    y = d.pos.values
    means = curve_means(store, tidx, y)

    res = {"tag": tag, "task": task, "arm": arm, "n": int(len(d)), "n_pos": int(d.pos.sum()),
           "n_neg": int((1 - d.pos).sum()), "n_blocks": int(d.blk.nunique()),
           "excl_uncertain": excl, "landscape_neg": land,
           "curves": {}, "full": {}, "ratio": {}, "gap_lgbm_full": None}
    for fs, mdl in itertools.product(("AEF64", "BASE74"), clfs):
        res["curves"][f"{fs}_{mdl}"] = {str(n): round(means[(fs, mdl, n)], 4)
                                        for n in NS if (fs, mdl, n) in means}
        if (fs, mdl, "full") in means: res["full"][f"{fs}_{mdl}"] = round(means[(fs, mdl, "full")], 4)

    blocks = d.blk.values
    ub = np.unique(blocks)
    bcode = pd.Categorical(blocks, categories=ub).codes
    fb = {fi: bcode[tidx[fi]] for fi in tidx}
    rng = np.random.default_rng(SEED)
    boots = {m: [] for m in clfs}
    gaps = []
    for b in range(BOOT):
        cnt = np.bincount(rng.integers(0, len(ub), len(ub)), minlength=len(ub))
        rep = {fi: np.repeat(np.arange(len(f)), cnt[f]) for fi, f in fb.items()}
        bm = curve_means(store, tidx, y, rep=rep, max_draw=BOOT_DRAWS)
        for m in clfs:
            r, _, _ = ratio_from(bm, m)
            if r is not None: boots[m].append(r)
        a, bb = bm.get(("AEF64", "lgbm", "full")), bm.get(("BASE74", "lgbm", "full"))
        if a is not None and bb is not None: gaps.append(a - bb)
        if (b + 1) % 250 == 0: print(f"  [{tag}] bootstrap {b+1}/{BOOT}", flush=True)

    for m in clfs:
        r, tgt, how = ratio_from(means, m)
        arr = np.array(boots[m])
        res["ratio"][m] = {"ratio": None if r is None else round(r, 3),
                           "aef_auc_at_40": None if tgt is None else round(tgt, 4), "how": how,
                           "ci_lo": round(float(np.percentile(arr, 2.5)), 3) if len(arr) else None,
                           "ci_hi": round(float(np.percentile(arr, 97.5)), 3) if len(arr) else None,
                           "n_boot": int(len(arr))}
        print(f"  [{tag}] {m}: ratio={res['ratio'][m]['ratio']} "
              f"CI[{res['ratio'][m]['ci_lo']}, {res['ratio'][m]['ci_hi']}] ({how})", flush=True)
    if gaps and "lgbm" in clfs:
        g = np.array(gaps)
        res["gap_lgbm_full"] = {
            "gap": round(res["full"].get("AEF64_lgbm", np.nan) - res["full"].get("BASE74_lgbm", np.nan), 4),
            "ci_lo": round(float(np.percentile(g, 2.5)), 4),
            "ci_hi": round(float(np.percentile(g, 97.5)), 4), "n_boot": int(len(g))}
        print(f"  [{tag}] full-data AEF-BASE74 gap (lgbm) = {res['gap_lgbm_full']['gap']} "
              f"CI[{res['gap_lgbm_full']['ci_lo']}, {res['gap_lgbm_full']['ci_hi']}]", flush=True)
    os.makedirs("results/P2", exist_ok=True)
    json.dump(res, open(f"results/P2/le_{tag}.json", "w"), indent=1)
    print(f"wrote results/P2/le_{tag}.json", flush=True)

if __name__ == "__main__":
    main()
