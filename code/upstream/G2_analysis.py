import numpy as np, pandas as pd, sys, json
from sklearn.model_selection import GroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score
import lightgbm as lgb

AEF=[f"A{i:02d}" for i in range(64)]
S2OLD=['B2','B3','B4','B8','B11','B12','NDVI','NBR']
S2OLD_P50=[b+'_p50' for b in S2OLD]  # old-baseline-equivalent reconstructed from G2's own points (tileScale fix)
NS=[25,50,100,250,500,1000]
SEEDS=30
BOOT=3000

def blk(d):
    return (np.floor(d.lon/0.1).astype(int).astype(str)+'_'+np.floor(d.lat/0.1).astype(int).astype(str))

def load_old_reported(k):
    """Stage-2's ORIGINAL TA04 csv/points (tileScale=8) -- kept only for reference to the
    originally reported numbers; NOT used in the restated ratio because its point set does not
    exactly match G2's (GEE stratifiedSample point identity depends weakly on tileScale)."""
    d=pd.read_csv(f'scratch/TA04_{k}.csv').dropna(subset=AEF+S2OLD)
    d['pos']=(d.y==2).astype(int); d['blk']=blk(d)
    return d.reset_index(drop=True)

def load_rich(k):
    d=pd.read_csv(f'scratch/G2_{k}.csv')
    rich_cols=[c for c in d.columns if c not in AEF+['y','lon','lat']]
    d=d.dropna(subset=AEF+rich_cols)
    d['pos']=(d.y==2).astype(int); d['blk']=blk(d)
    return d.reset_index(drop=True), rich_cols

def make_model(kind):
    if kind=='log':
        return make_pipeline(StandardScaler(),
            LogisticRegression(max_iter=3000,C=1.0,class_weight='balanced'))
    else:
        return lgb.LGBMClassifier(n_estimators=150,num_leaves=7,min_child_samples=5,
            learning_rate=0.05,subsample=0.8,colsample_bytree=0.8,reg_lambda=1.0,
            is_unbalance=True,verbosity=-1,random_state=0)

def fit_pred(kind,Xtr,ytr,Xte):
    m=make_model(kind)
    if len(np.unique(ytr))<2: return None
    m.fit(Xtr,ytr)
    return m.predict_proba(Xte)[:,1]

def curve(d,feats,kind,seeds=SEEDS):
    gk=GroupKFold(n_splits=5); out={n:[] for n in NS}; full=[]
    for tr,te in gk.split(d,d.pos,d.blk):
        dtr,dte=d.iloc[tr],d.iloc[te]
        if dte.pos.nunique()<2: continue
        Xte,yte=dte[feats].values,dte.pos.values
        p=fit_pred(kind,dtr[feats].values,dtr.pos.values,Xte)
        if p is not None: full.append(roc_auc_score(yte,p))
        p_idx=dtr.index[dtr.pos==1]; q_idx=dtr.index[dtr.pos==0]
        for n in NS:
            if n>len(dtr): continue
            for s in range(seeds):
                rs=np.random.RandomState(10000*s+n)
                npz=max(4,int(round(n*dtr.pos.mean()))); nnz=n-npz
                if npz>len(p_idx) or nnz>len(q_idx): continue
                idx=np.concatenate([rs.choice(p_idx,npz,False),rs.choice(q_idx,nnz,False)])
                sub=dtr.loc[idx]
                pp=fit_pred(kind,sub[feats].values,sub.pos.values,Xte)
                if pp is not None: out[n].append(roc_auc_score(yte,pp))
    stat={n:(float(np.mean(v)),float(np.std(v)),len(v)) for n,v in out.items() if v}
    fullstat=(float(np.mean(full)),float(np.std(full)),len(full)) if full else (np.nan,np.nan,0)
    return {n:out[n] for n in NS if out[n]}, out, full, stat, fullstat

def interp_labels(ns_sorted, means, target):
    # log-linear interpolation of AUC vs log(n); return n at which mean AUC first reaches target
    if means[0]>=target: return ns_sorted[0]  # already reached at smallest budget
    for i in range(1,len(ns_sorted)):
        if means[i]>=target:
            x0,x1=np.log(ns_sorted[i-1]),np.log(ns_sorted[i])
            y0,y1=means[i-1],means[i]
            if y1==y0: return ns_sorted[i]
            frac=(target-y0)/(y1-y0)
            return float(np.exp(x0+frac*(x1-x0)))
    return None  # never reached within tested budgets

def bootstrap_ratio(aef_draws_by_n, aef_full_draws, target_draws, target_is_full, n_target_labels, B=BOOT):
    ns_sorted=sorted(aef_draws_by_n.keys())
    ratios=[]
    rng=np.random.RandomState(0)
    for b in range(B):
        # resample target AUC
        tgt_s=rng.choice(target_draws,size=len(target_draws),replace=True)
        target=float(np.mean(tgt_s))
        means=[]
        for n in ns_sorted:
            v=aef_draws_by_n[n]
            s=rng.choice(v,size=len(v),replace=True)
            means.append(float(np.mean(s)))
        n_star=interp_labels(ns_sorted,means,target)
        if n_star is None or n_star<=0: continue
        ratios.append(n_target_labels/n_star)
    ratios=np.array(ratios)
    if len(ratios)==0: return (np.nan,np.nan,np.nan,0)
    return (float(np.mean(ratios)),float(np.percentile(ratios,2.5)),float(np.percentile(ratios,97.5)),len(ratios))

def run_region(k):
    dold_reported=load_old_reported(k)  # reference only, different point set (tileScale=8)
    drich, rich_cols=load_rich(k)
    print(k,'old(reported) n',len(dold_reported),'rich n',len(drich),'rich_feats',len(rich_cols),flush=True)
    arms={}
    arms['AEF64_log']=curve(drich,AEF,'log')
    arms['AEF64_lgbm']=curve(drich,AEF,'lgbm')
    arms['RICH_lgbm']=curve(drich,rich_cols,'lgbm')
    arms['RICH_log']=curve(drich,rich_cols,'log')
    arms['S2OLD_log']=curve(drich,S2OLD_P50,'log')          # self-consistent: same points as G2
    arms['S2OLD_log_reportedpts']=curve(dold_reported,S2OLD,'log')  # Stage-2's original point set
    return arms, rich_cols

def summarize(arms):
    out={}
    for nm,(bystat,out_,full,stat,fullstat) in arms.items():
        out[nm]={'curve':{n:round(v[0],4) for n,v in stat.items()},
                 'sd':{n:round(v[1],4) for n,v in stat.items()},
                 'ndraws':{n:v[2] for n,v in stat.items()},
                 'full_mean':round(fullstat[0],4),'full_sd':round(fullstat[1],4),'full_nfold':fullstat[2]}
    return out

if __name__=='__main__':
    results={}
    for k in ['AMZ','GHA']:
        arms, rich_cols=run_region(k)
        summ=summarize(arms)
        print(k,json.dumps(summ,indent=None),flush=True)
        # parity ratios vs RICH baseline (logistic, matches "baseline+same classifier" convention) and vs RICH_lgbm
        aef_by_n=arms['AEF64_log'][1]
        aef_full=arms['AEF64_log'][2]
        rich_log_by_n=arms['RICH_log'][1]; rich_log_full=arms['RICH_log'][2]
        rich_lgbm_by_n=arms['RICH_lgbm'][1]; rich_lgbm_full=arms['RICH_lgbm'][2]
        s2_by_n=arms['S2OLD_log'][1]; s2_full=arms['S2OLD_log'][2]
        # OLD multiple (restated with this run's methodology): AEF-log needed labels to match S2OLD@1000
        r_old_1000=bootstrap_ratio(aef_by_n,aef_full,s2_by_n[1000],False,1000)
        # NEW multiple vs RICH_log @1000 and @full
        r_new_1000=bootstrap_ratio(aef_by_n,aef_full,rich_log_by_n[1000],False,1000)
        # full: use mean training-pool size across folds as n_target for "full"
        n_full_avg=int(np.mean([len(pd.read_csv(f'scratch/G2_{k}.csv'))*0.8]))  # ~4/5 train fold size
        r_new_full=bootstrap_ratio(aef_by_n,aef_full,rich_log_full,True,n_full_avg)
        r_new_1000_lgbmbase=bootstrap_ratio(aef_by_n,aef_full,rich_lgbm_by_n[1000],False,1000)
        r_new_full_lgbmbase=bootstrap_ratio(aef_by_n,aef_full,rich_lgbm_full,True,n_full_avg)
        results[k]={'summary':summ,
                    'old_multiple_restated_vs_S2OLD@1000':r_old_1000,
                    'new_multiple_vs_RICHlog@1000':r_new_1000,
                    'new_multiple_vs_RICHlog@full':r_new_full,
                    'new_multiple_vs_RICHlgbm@1000':r_new_1000_lgbmbase,
                    'new_multiple_vs_RICHlgbm@full':r_new_full_lgbmbase,
                    'n_full_avg':n_full_avg}
        print(k,'RATIOS old1000',r_old_1000,'new1000',r_new_1000,'newfull',r_new_full,
              'new1000_lgbmbase',r_new_1000_lgbmbase,'new_full_lgbmbase',r_new_full_lgbmbase,flush=True)
    import pickle
    with open('scratch/G2_results.pkl','wb') as f: pickle.dump(results,f)
    print('SAVED scratch/G2_results.pkl',flush=True)
