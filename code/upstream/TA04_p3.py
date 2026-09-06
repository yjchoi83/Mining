import numpy as np, pandas as pd
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
AEF=[f"A{i:02d}" for i in range(64)]; S2=['B2','B3','B4','B8','B11','B12','NDVI','NBR']
def load(k):
    d=pd.read_csv(f'scratch/TA04_{k}.csv').dropna(subset=AEF+S2)
    d['pos']=(d.y==2).astype(int)
    d['blk']=(np.floor(d.lon/0.1).astype(int).astype(str)+'_'+np.floor(d.lat/0.1).astype(int).astype(str))
    return d.reset_index(drop=True)
A=load('AMZ'); G=load('GHA')
def fit(X,y): return make_pipeline(StandardScaler(),LogisticRegression(max_iter=3000,class_weight='balanced')).fit(X,y)
def z(d,fs):
    X=d[fs].values; return (X-X.mean(0))/(X.std(0)+1e-9)
print('=== per-region z-score (moment matching) transfer AMZ->GHA ===')
for nm,fs in [('AEF64',AEF),('S2_8',S2)]:
    Xa,Xg=z(A,fs),z(G,fs); sc=[]
    for tr,te in GroupKFold(5).split(A,A.pos,A.blk):
        m=fit(Xa[tr],A.pos.values[tr]); sc.append(roc_auc_score(G.pos.values,m.predict_proba(Xg)[:,1]))
    print(nm,'z-scored AMZ->GHA',round(float(np.mean(sc)),3),'sd',round(float(np.std(sc)),3))
print('\n=== few-shot Ghana adaptation: AMZ pool + k GHA labels, test on held-out GHA blocks ===')
KS=[0,10,25,50,100,250]
for nm,fs in [('AEF64',AEF),('S2_8',S2)]:
    row={}
    for tr,te in GroupKFold(5).split(G,G.pos,G.blk):
        gtr,gte=G.iloc[tr],G.iloc[te]
        Xte,yte=gte[fs].values,gte.pos.values
        for k in KS:
            for s in range(5):
                rs=np.random.RandomState(7*s+k)
                if k==0: Xt,yt=A[fs].values,A.pos.values
                else:
                    p=gtr.index[gtr.pos==1]; q=gtr.index[gtr.pos==0]
                    npz=max(2,k//3); nnz=k-npz
                    if npz>len(p) or nnz>len(q): continue
                    idx=np.concatenate([rs.choice(p,npz,False),rs.choice(q,nnz,False)])
                    sub=G.loc[idx]
                    Xt=np.vstack([A[fs].values,sub[fs].values]); yt=np.concatenate([A.pos.values,sub.pos.values])
                row.setdefault(k,[]).append(roc_auc_score(yte,fit(Xt,yt).predict_proba(Xte)[:,1]))
                if k==0: break
    print(nm,{k:(round(float(np.mean(v)),3),round(float(np.std(v)),3)) for k,v in row.items()})
print('\n=== GHA-only few-shot (no AMZ pretraining) for comparison ===')
for nm,fs in [('AEF64',AEF),('S2_8',S2)]:
    row={}
    for tr,te in GroupKFold(5).split(G,G.pos,G.blk):
        gtr,gte=G.iloc[tr],G.iloc[te]; Xte,yte=gte[fs].values,gte.pos.values
        for k in [10,25,50,100,250]:
            for s in range(5):
                rs=np.random.RandomState(7*s+k)
                p=gtr.index[gtr.pos==1]; q=gtr.index[gtr.pos==0]
                npz=max(2,k//3); nnz=k-npz
                if npz>len(p) or nnz>len(q): continue
                idx=np.concatenate([rs.choice(p,npz,False),rs.choice(q,nnz,False)]); sub=G.loc[idx]
                row.setdefault(k,[]).append(roc_auc_score(yte,fit(sub[fs].values,sub.pos.values).predict_proba(Xte)[:,1]))
    print(nm,{k:round(float(np.mean(v)),3) for k,v in row.items()})
