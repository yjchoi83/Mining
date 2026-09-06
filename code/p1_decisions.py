"""TA04-P1 Step A -- apply the human QC adjudications to results/P1/qc_table.csv.

Decisions were made by the human reviewer against results/P1/qc_sheets/*.png.
This script only WRITES them into the table; it makes no judgement of its own.
Vocabulary (one per chip, `decision` column):
  ASGM_confirmed          Amazon positive, visible artisanal workings inside the outline
  industrial_confirmed    Ghana flagged positive, visible large-scale mine
  ASM_like_flag_error     Ghana flagged industrial but reads as artisanal -> proximity rule wrong
  ASM_confirmed           Ghana unclassified positive, visible artisanal workings
  PRK_VISIBLE             DPRK polygon with a surface mining footprint at 10 m annual median
  PRK_NOT_VISIBLE         DPRK polygon with no surface footprint at 10 m annual median
  non_mining_confirmed    hard negative, no mining visible
  uncertain               cannot be adjudicated from a 1 km S2 annual-median chip
"""
import pandas as pd

def ids(pfx, *spans):
    out = []
    for s in spans:
        if isinstance(s, tuple): out += [f"{pfx}{i:03d}" for i in range(s[0], s[1] + 1)]
        else: out.append(f"{pfx}{s:03d}")
    return out

DEC, NOTE = {}, {}

# ---- TAP (35) -------------------------------------------------------------------------
for i in ids("TAP_ASGM_", (0, 16), (18, 21), (23, 33)): DEC[i] = "ASGM_confirmed"
for i, r in {"TAP_ASGM_017": "river-bend sandbar vs dredging — cannot separate",
             "TAP_ASGM_022": "polygon mostly forest in 2019",
             "TAP_ASGM_034": "polygon offset from visible mining"}.items():
    DEC[i], NOTE[i] = "uncertain", r
# ---- MDD (15) -------------------------------------------------------------------------
for i in ids("MDD_ASGM_", (0, 9), 11, 12, 14): DEC[i] = "ASGM_confirmed"
for i in ("MDD_ASGM_010", "MDD_ASGM_013"):
    DEC[i], NOTE[i] = "uncertain", "natural river sandbar possible"
# ---- GHA industrial-flagged (15) ------------------------------------------------------
for i in ids("GHA_IND_", 2, 4, 5, 6, 7, 8, 14): DEC[i] = "industrial_confirmed"
for i in ids("GHA_IND_", 0, 1, 3):
    DEC[i], NOTE[i] = "ASM_like_flag_error", "reads as artisanal; 5 km proximity flag is wrong here"
for i in ids("GHA_IND_", 9, 10, 11, 12, 13):
    DEC[i], NOTE[i] = "uncertain", "industrial vs artisanal not separable from this chip"
# ---- GHA unclassified (15) ------------------------------------------------------------
for i in ids("GHA_UNC_", (0, 10), 13, 14): DEC[i] = "ASM_confirmed"
DEC["GHA_UNC_011"], NOTE["GHA_UNC_011"] = "uncertain", "settlement"
DEC["GHA_UNC_012"], NOTE["GHA_UNC_012"] = "uncertain", "rectangular bare patch — quarry?"
# ---- DPRK (50) ------------------------------------------------------------------------
PRK_VIS = [0, 1, 2, 3, 4, 5, 7, 8, 10, 11, 15, 18, 20, 24, 27, 30, 31, 32, 35, 37, 38]
for k in range(50):
    i = f"PRK_{k:03d}"
    DEC[i] = "PRK_VISIBLE" if k in PRK_VIS else "PRK_NOT_VISIBLE"
    if k not in PRK_VIS: NOTE[i] = "no surface footprint at 10 m annual median"

q = pd.read_csv("results/P1/qc_table.csv")
q["decision"] = q.id.map(DEC).fillna("")
neg = q.id.str.startswith("NEG_")
q.loc[neg, "decision"] = "non_mining_confirmed"
q["notes"] = [f"{n}; adj: {NOTE[i]}" if i in NOTE else n for i, n in zip(q.id, q.notes)]
assert (q.decision != "").all(), q[q.decision == ""].id.tolist()
q.to_csv("results/P1/qc_table.csv", index=False)

print(q.groupby(["region", "proposed_label", "decision"]).size().to_string())
print(f"\n{len(q)} rows, all adjudicated")
for r, conf, tot in (("TAP", (q.id.str.startswith("TAP_ASGM_") & (q.decision == "ASGM_confirmed")).sum(), 35),
                     ("MDD", (q.id.str.startswith("MDD_ASGM_") & (q.decision == "ASGM_confirmed")).sum(), 15),
                     ("GHA_UNC", (q.id.str.startswith("GHA_UNC_") & (q.decision == "ASM_confirmed")).sum(), 15)):
    print(f"  {r} purity {conf}/{tot} = {100*conf/tot:.1f}%")
print(f"  PRK visible {len(PRK_VIS)}/50 = {100*len(PRK_VIS)/50:.0f}%")
