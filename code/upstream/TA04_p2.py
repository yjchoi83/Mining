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
for k,d in [('AMZ',A),('GHA',G)]:
    print(k,'n',len(d),'y',d.y.value_counts().to_dict(),'pos_frac',round(d.pos.mean(),3),'blocks',d.blk.nunique())
def fit(X,y):
    return make_pipeline(StandardScaler(),LogisticRegression(max_iter=3000,C=1.0,class_weight='balanced')).fit(X,y)
NS=[25,50,100,250,500,1000]
def curve(d,feats,seeds=5):
    gk=GroupKFold(n_splits=5); out={n:[] for n in NS}; full=[]
    for tr,te in gk.split(d,d.pos,d.blk):
        dtr,dte=d.iloc[tr],d.iloc[te]
        if dte.pos.nunique()<2: continue
        Xte,yte=dte[feats].values,dte.pos.values
        full.append(roc_auc_score(yte,fit(dtr[feats].values,dtr.pos.values).predict_proba(Xte)[:,1]))
        for n in NS:
            if n>len(dtr): continue
            for s in range(seeds):
                rs=np.random.RandomState(1000*s+n)
                # stratified subsample preserving pool class ratio, >=4 per class
                p=dtr.index[dtr.pos==1]; q=dtr.index[dtr.pos==0]
                npz=max(4,int(round(n*dtr.pos.mean()))); nnz=n-npz
                if npz>len(p) or nnz>len(q): continue
                idx=np.concatenate([rs.choice(p,npz,False),rs.choice(q,nnz,False)])
                sub=dtr.loc[idx]
                out[n].append(roc_auc_score(yte,fit(sub[feats].values,sub.pos.values).predict_proba(Xte)[:,1]))
    return {n:(round(float(np.mean(v)),3),round(float(np.std(v)),3),len(v)) for n,v in out.items() if v}, \
           (round(float(np.mean(full)),3),round(float(np.std(full)),3),[round(x,3) for x in full])
print('\n=== label-efficiency (AMZ, in-region, 5-fold GroupKFold 0.1deg blocks, metric AUC) ===')
res={}
for nm,fs in [('AEF64',AEF),('S2_8',S2)]:
    c,f=curve(A,fs); res[nm]=(c,f)
    print(nm,'full',f[0],'sd',f[1],'folds',f[2])
    print(nm,'curve',{n:v[0] for n,v in c.items()},'sd',{n:v[1] for n,v in c.items()})
print('\n=== GHA in-region ===')
resg={}
for nm,fs in [('AEF64',AEF),('S2_8',S2)]:
    c,f=curve(G,fs); resg[nm]=(c,f)
    print(nm,'full',f[0],'sd',f[1],'folds',f[2])
    print(nm,'curve',{n:v[0] for n,v in c.items()})
print('\n=== transfer AMZ->GHA (train on AMZ folds, test all GHA) ===')
gk=GroupKFold(n_splits=5)
for nm,fs in [('AEF64',AEF),('S2_8',S2)]:
    sc=[]
    for tr,te in gk.split(A,A.pos,A.blk):
        m=fit(A.iloc[tr][fs].values,A.iloc[tr].pos.values)
        sc.append(roc_auc_score(G.pos.values,m.predict_proba(G[fs].values)[:,1]))
    print(nm,'AMZ->GHA',round(float(np.mean(sc)),3),'sd',round(float(np.std(sc)),3),[round(x,3) for x in sc])
    sc2=[]
    for tr,te in gk.split(G,G.pos,G.blk):
        m=fit(G.iloc[tr][fs].values,G.iloc[tr].pos.values)
        sc2.append(roc_auc_score(A.pos.values,m.predict_proba(A[fs].values)[:,1]))
    print(nm,'GHA->AMZ',round(float(np.mean(sc2)),3),'sd',round(float(np.std(sc2)),3))
print('\n=== T5 retrieval: k seeds from AMZ mining, dot-product search ===')
for nm,fs in [('AEF64',AEF),('S2_8',S2)]:
    for tgt,td in [('AMZ',A),('GHA',G)]:
        pk=[]
        for s in range(10):
            rs=np.random.RandomState(s)
            seed_idx=rs.choice(A.index[A.pos==1],10,False)
            Q=A.loc[seed_idx,fs].values
            pool=td.drop(index=[i for i in seed_idx if i in td.index]) if tgt=='AMZ' else td
            X=pool[fs].values
            Xn=X/np.linalg.norm(X,axis=1,keepdims=True); Qn=Q/np.linalg.norm(Q,axis=1,keepdims=True)
            sim=(Xn@Qn.T).mean(1)
            top=np.argsort(-sim)[:100]
            pk.append(pool.pos.values[top].mean())
        print(nm,'seeds=10 P@100 ->',tgt,round(float(np.mean(pk)),3),'sd',round(float(np.std(pk)),3),
              'base',round(float(td.pos.mean()),3))
