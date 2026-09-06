import ee,time,random,sys,pandas as pd
sys.path.insert(0,'scratch')
for a in range(60):
    try: ee.Initialize(); break
    except Exception: time.sleep(15+random.random()*20)
import numpy as np
def rt(f,tag='',n=40):
    for a in range(n):
        try: return f()
        except Exception as e:
            s=str(e)
            if '429' in s or 'Too Many' in s or 'Timed out' in s or 'timed out' in s:
                time.sleep(15+random.random()*25); continue
            print(tag,'ERR',s[:160],flush=True); return None
    print(tag,'GIVEUP',flush=True); return None
AEF=ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
def aef(y,r): return AEF.filterDate(f"{y}-01-01",f"{y+1}-01-01").filterBounds(r).mosaic()
def s2(y,r):
    def m(i):
        q=i.select('QA60'); c=1<<10|1<<11
        return i.updateMask(q.bitwiseAnd(c).eq(0)).divide(10000)
    col=(ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterDate(f"{y}-01-01",f"{y+1}-01-01")
         .filterBounds(r).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',60)).map(m))
    md=col.select(['B2','B3','B4','B8','B11','B12']).median()
    return md.addBands(md.normalizedDifference(['B8','B4']).rename('NDVI')) \
             .addBands(md.normalizedDifference(['B8','B12']).rename('NBR'))
MINE=ee.FeatureCollection("projects/sat-io/open-datasets/global-mining/global_mining_polygons")
H=ee.Image("UMD/hansen/global_forest_change_2025_v1_13")
Y=2019; PC=int(sys.argv[2]) if len(sys.argv)>2 else 900
ROIS={"AMZ":[-58.0,-8.0,-54.0,-4.0],"GHA":[-3.2,4.9,-0.9,7.2]}
k=sys.argv[1]; b=ROIS[k]; roi=ee.Geometry.Rectangle(b)
fc=MINE.filterBounds(roi)
mine=ee.Image(0).paint(fc,1)
buf=ee.Image(0).paint(fc.map(lambda f: f.buffer(1000)),1)
ly=H.select('lossyear').unmask(0); tc=H.select('treecover2000').unmask(0)
loss=ly.gte(15).And(ly.lte(19))
hard=loss.And(buf.eq(0)).And(tc.gt(30))
stable=ly.eq(0).And(buf.eq(0)).And(tc.gt(50))
lab=ee.Image(255).where(stable,0).where(hard,1).where(mine.eq(1),2).rename('y').toInt()
lab=lab.updateMask(lab.neq(255))
pts=rt(lambda: lab.stratifiedSample(numPoints=PC,classBand='y',region=roi,scale=20,seed=7,
        classValues=[0,1,2],classPoints=[PC]*3,geometries=True,dropNulls=True,tileScale=8),'strat')
if pts is None: sys.exit(1)
n=rt(lambda: pts.size().getInfo(),'sz'); print(k,'strat n',n,flush=True)
lst=rt(lambda: pts.toList(n).getInfo(),'lst')
feats=[]
for f in lst:
    c=f['geometry']['coordinates']; feats.append((c[0],c[1],f['properties']['y']))
stack=aef(Y,roi).addBands(s2(Y,roi))
rows=[]; CH=300
for i in range(0,len(feats),CH):
    ch=feats[i:i+CH]
    fcs=ee.FeatureCollection([ee.Feature(ee.Geometry.Point([x,yy]),{'y':lb}) for x,yy,lb in ch])
    r=rt(lambda: stack.sampleRegions(collection=fcs,scale=10,geometries=True,tileScale=8).getInfo(),'ch%d'%i)
    if r is None: continue
    for ft in r['features']:
        d=dict(ft['properties']); cc=ft['geometry']['coordinates']
        d['lon'],d['lat']=cc[0],cc[1]; rows.append(d)
    print(k,'chunk',i,'tot',len(rows),flush=True)
df=pd.DataFrame(rows); df.to_csv(f'scratch/TA04_{k}.csv',index=False)
print(k,'SAVED',df.shape,df['y'].value_counts().to_dict(),flush=True)
