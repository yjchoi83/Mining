"""TA04-P1 step 1e -- Amazon source agreement between the three references at the
sampled points: Maus v2 x AMW (our ASGM label) vs MapBiomas garimpo (class_id 2xx).

MapBiomas covers Brazil only, so this is reported for TAP; MDD (Peru) is out of its
footprint and is shown separately as a coverage check.
"""
import json, os
import numpy as np, pandas as pd

GARIMPO = set(range(214, 226))
INDUSTRIAL = set(range(101, 131))

def label(c):
    c = int(c)
    if c in GARIMPO: return "MB_garimpo"
    if c in INDUSTRIAL: return "MB_industrial"
    return "MB_none"

out = {}
for k in ("TAP", "MDD"):
    f = f"data/samples_{k}.csv"
    if not os.path.exists(f): continue
    d = pd.read_csv(f)
    if "mb_cid" not in d.columns:
        out[k] = {"note": "mb_cid absent"}; continue
    d["mb"] = d.mb_cid.fillna(0).map(label)
    d["ours"] = np.where(d.cls == 1, "ASGM_positive", "background_negative")
    ct = pd.crosstab(d.ours, d.mb)
    print(f"--- {k} ---"); print(ct.to_string())
    pos = d[d.cls == 1]
    neg = d[d.cls == 0]
    rec = {"crosstab": {r: {c: int(ct.loc[r, c]) for c in ct.columns} for r in ct.index},
           "pos_n": int(len(pos)), "neg_n": int(len(neg)),
           "frac_our_positives_that_MapBiomas_calls_garimpo":
               round(float((pos.mb == "MB_garimpo").mean()), 4),
           "frac_our_positives_MapBiomas_calls_industrial":
               round(float((pos.mb == "MB_industrial").mean()), 4),
           "frac_our_negatives_MapBiomas_calls_mining":
               round(float((neg.mb != "MB_none").mean()), 4)}
    print(json.dumps(rec, indent=1)[:400])
    out[k] = rec

json.dump(out, open("results/P1/source_agreement.json", "w"), indent=1)
print("wrote results/P1/source_agreement.json")
