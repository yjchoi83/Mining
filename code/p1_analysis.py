"""TA04-P1 steps 3 & 4 -- label-efficiency re-test.

Step 3  Amazon ASGM-only (TAP + MDD pooled): AEF-64 vs the Stage-4 G2 74-feature
        classical baseline, label budgets {10,20,40,80,160,320,640,1000}, 20 draws,
        5-fold GroupKFold on 0.5-degree spatial blocks, metric ROC-AUC.
        Label-parity ratio = (baseline labels to reach the AEF AUC at k=40) / 40,
        with a BLOCK bootstrap CI (1,000 draws, blocks resampled with replacement).
        PRE-REGISTERED: survives iff ratio >= 3 AND CI lower >= 2; ratio < 3 => KILLED.
Step 4  Ghana mixed, transfer-only framing: same protocol, reported separately for
        industrial-flagged and unclassified positives.
"""
import os, sys, json, itertools
import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
import lightgbm as lgb
from scipy.stats import rankdata

AEF = [f"A{i:02d}" for i in range(64)]
NS = [10, 20, 40, 80, 160, 320, 640, 1000]
DRAWS = 20
FOLDS = 5
BOOT = 1000
BOOT_DRAWS = 8          # draws reused inside each bootstrap iteration (CI width is
                        # driven by block resampling, not by the number of subsample draws)
K_REF = 40                      # the AEF budget the baseline has to match
SEED = 20260906
NONFEAT = {"id", "cls", "sub", "blk", "lon", "lat", "roi", "mb_cid"}

def fast_auc(y, s):
    """Rank-based ROC-AUC (Mann-Whitney U). Vectorised: the bootstrap calls this ~1e6
    times, so a Python-level tie loop is not affordable -- scipy.rankdata is C."""
    n1 = int(y.sum()); n0 = len(y) - n1
    if n1 == 0 or n0 == 0: return np.nan
    r = rankdata(s)
    return (r[y == 1].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0)

def model(kind):
    if kind == "log":
        return make_pipeline(StandardScaler(),
                             LogisticRegression(max_iter=3000, C=1.0, class_weight="balanced"))
    return lgb.LGBMClassifier(n_estimators=150, num_leaves=7, min_child_samples=5,
                              learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                              reg_lambda=1.0, is_unbalance=True, verbosity=-1, random_state=0)

def fit_pred(kind, Xtr, ytr, Xte):
    if len(np.unique(ytr)) < 2: return None
    m = model(kind); m.fit(Xtr, ytr)
    return m.predict_proba(Xte)[:, 1]

def load(rois, pos_sub=None):
    d = pd.concat([pd.read_csv(f"data/samples_{k}.csv") for k in rois], ignore_index=True)
    feats = [c for c in d.columns if c not in NONFEAT]
    base = [c for c in feats if c not in AEF]
    d = d.dropna(subset=AEF + base).reset_index(drop=True)
    if pos_sub is not None:
        d = d[(d.cls == 0) | (d["sub"] == pos_sub)].reset_index(drop=True)
    d["pos"] = d.cls.astype(int)
    return d, base

def run(d, base, tag):
    """One CV pass storing every prediction so the block bootstrap can reuse them."""
    gk = GroupKFold(n_splits=FOLDS)
    folds = list(gk.split(d, d.pos, d.blk))
    store = {}                                  # (fs, mdl, k or 'full', draw, fold) -> preds
    tidx = {}                                   # fold -> test row indices
    for fi, (tr, te) in enumerate(folds):
        tidx[fi] = te
        dtr, dte = d.iloc[tr], d.iloc[te]
        for fs_name, fs in (("AEF64", AEF), ("BASE74", base)):
            Xtr_all, Xte = dtr[fs].values, dte[fs].values
            ytr_all = dtr.pos.values
            for mdl in ("log", "lgbm"):
                p = fit_pred(mdl, Xtr_all, ytr_all, Xte)
                if p is not None: store[(fs_name, mdl, "full", 0, fi)] = p.astype(np.float32)
                pi = np.where(ytr_all == 1)[0]; qi = np.where(ytr_all == 0)[0]
                for n in NS:
                    if n > len(dtr): continue
                    for s in range(DRAWS):
                        rs = np.random.RandomState(SEED % 9999 + 1000 * s + n)
                        npz = max(4, int(round(n * ytr_all.mean()))); nnz = n - npz
                        if npz > len(pi) or nnz > len(qi) or nnz < 4: continue
                        idx = np.concatenate([rs.choice(pi, npz, False), rs.choice(qi, nnz, False)])
                        pp = fit_pred(mdl, Xtr_all[idx], ytr_all[idx], Xte)
                        if pp is not None:
                            store[(fs_name, mdl, n, s, fi)] = pp.astype(np.float32)
        print(f"  [{tag}] fold {fi+1}/{FOLDS} done, {len(store)} prediction vectors", flush=True)
    return store, tidx, folds

def curve_means(store, tidx, y, rep=None, keys=None, max_draw=None):
    """Mean AUC per (fs, mdl, budget).

    `rep` is a per-fold array of row positions (into the fold's test set) already
    expanded by block multiplicity -- that is what makes this a genuine BLOCK bootstrap
    rather than a block subsample: a block drawn twice contributes twice.
    """
    out = {}
    for (fs, mdl, n, s, fi), p in store.items():
        if keys is not None and (fs, mdl) not in keys: continue
        if max_draw is not None and n != "full" and s >= max_draw: continue
        te = tidx[fi]
        if rep is not None:
            sel = rep[fi]
            if len(sel) < 20: continue
            a = fast_auc(y[te][sel], p[sel])
        else:
            a = fast_auc(y[te], p)
        if not np.isnan(a): out.setdefault((fs, mdl, n), []).append(a)
    return {k: float(np.mean(v)) for k, v in out.items()}, {k: len(v) for k, v in out.items()}

def labels_to_reach(means, fs, mdl, target):
    """Log-linear interpolation: baseline labels needed to reach `target` AUC."""
    ns = [n for n in NS if (fs, mdl, n) in means]
    if not ns: return None, "no curve"
    ys = [means[(fs, mdl, n)] for n in ns]
    if ys[0] >= target: return float(ns[0]), "reached at smallest budget"
    for i in range(1, len(ns)):
        if ys[i] >= target:
            x0, x1 = np.log(ns[i - 1]), np.log(ns[i])
            y0, y1 = ys[i - 1], ys[i]
            f = (target - y0) / (y1 - y0) if y1 != y0 else 1.0
            return float(np.exp(x0 + f * (x1 - x0))), "interpolated"
    return None, "censored"          # never reached within k <= 1000

def ratio_from(means, mdl):
    tgt = means.get(("AEF64", mdl, K_REF))
    if tgt is None: return None, None, "no AEF@40"
    n_base, how = labels_to_reach(means, "BASE74", mdl, tgt)
    if n_base is None:
        return float(NS[-1] / K_REF), tgt, "censored_at_%d" % NS[-1]
    return float(n_base / K_REF), tgt, how

def analyse(rois, tag, pos_sub=None):
    d, base = load(rois, pos_sub)
    print(f"[{tag}] n={len(d)} pos={int(d.pos.sum())} neg={int((1-d.pos).sum())} "
          f"blocks={d.blk.nunique()} base_features={len(base)}", flush=True)
    store, tidx, folds = run(d, base, tag)
    y = d.pos.values
    means, nd = curve_means(store, tidx, y)

    res = {"tag": tag, "rois": rois, "n": int(len(d)), "n_pos": int(d.pos.sum()),
           "n_neg": int((1 - d.pos).sum()), "n_blocks": int(d.blk.nunique()),
           "n_base_features": len(base), "positives_subset": pos_sub,
           "curves": {}, "full": {}, "ratio": {}}
    for fs, mdl in itertools.product(("AEF64", "BASE74"), ("log", "lgbm")):
        res["curves"][f"{fs}_{mdl}"] = {str(n): round(means[(fs, mdl, n)], 4)
                                        for n in NS if (fs, mdl, n) in means}
        if (fs, mdl, "full") in means:
            res["full"][f"{fs}_{mdl}"] = round(means[(fs, mdl, "full")], 4)

    # ---- block bootstrap over 0.5-degree blocks --------------------------------
    blocks = d.blk.values
    ub = np.unique(blocks)
    rng = np.random.default_rng(SEED)
    boots = {"log": [], "lgbm": []}
    bcode = pd.Categorical(blocks, categories=ub).codes
    fold_bcode = {fi: bcode[tidx[fi]] for fi in tidx}
    keys = {("AEF64", "log"), ("AEF64", "lgbm"), ("BASE74", "log"), ("BASE74", "lgbm")}
    for b in range(BOOT):
        cnt = np.bincount(rng.integers(0, len(ub), len(ub)), minlength=len(ub))
        rep = {fi: np.repeat(np.arange(len(fb)), cnt[fb]) for fi, fb in fold_bcode.items()}
        bm, _ = curve_means(store, tidx, y, rep=rep, keys=keys, max_draw=BOOT_DRAWS)
        for mdl in ("log", "lgbm"):
            r, _, _ = ratio_from(bm, mdl)
            if r is not None: boots[mdl].append(r)
        if (b + 1) % 200 == 0: print(f"  [{tag}] bootstrap {b+1}/{BOOT}", flush=True)

    for mdl in ("log", "lgbm"):
        r, tgt, how = ratio_from(means, mdl)
        arr = np.array(boots[mdl])
        res["ratio"][mdl] = {
            "ratio": None if r is None else round(r, 3),
            "aef_auc_at_40": None if tgt is None else round(tgt, 4),
            "how": how,
            "ci_lo": round(float(np.percentile(arr, 2.5)), 3) if len(arr) else None,
            "ci_hi": round(float(np.percentile(arr, 97.5)), 3) if len(arr) else None,
            "n_boot": int(len(arr))}
        print(f"  [{tag}] {mdl}: ratio={res['ratio'][mdl]['ratio']} "
              f"CI[{res['ratio'][mdl]['ci_lo']}, {res['ratio'][mdl]['ci_hi']}] ({how})", flush=True)
    return res

if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "all"
    out = {}
    if which in ("all", "amazon"):
        out["AMAZON_ASGM"] = analyse(["TAP", "MDD"], "AMAZON_ASGM")
    if which in ("all", "ghana"):
        out["GHANA_industrial"] = analyse(["GHA"], "GHANA_industrial", pos_sub="industrial")
        out["GHANA_unclassified"] = analyse(["GHA"], "GHANA_unclassified", pos_sub="unclassified")
    os.makedirs("results/P1", exist_ok=True)
    f = f"results/P1/labeleff_{which}.json"
    json.dump(out, open(f, "w"), indent=1)
    print("wrote", f, flush=True)
