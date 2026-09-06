import ee,time,random,sys,pandas as pd,numpy as np
for a in range(60):
    try: ee.Initialize(); break
    except Exception: time.sleep(15+random.random()*20)
def rt(f,tag='',n=30):
    for a in range(n):
        try: return f()
        except Exception as e:
            s=str(e)
            if any(t in s for t in ('429','Too Many','imed out','Computation timed')):
                time.sleep(12+random.random()*20); continue
            print(tag,'ERR',s[:150],flush=True); return None
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
Y=2019
ROIS={"AMZ":[-58.0,-8.0,-54.0,-4.0],"GHA":[-3.2,4.9,-0.9,7.2]}
k=sys.argv[1]; PC=int(sys.argv[2]); roi=ee.Geometry.Rectangle(ROIS[k])
fc=MINE.filterBounds(roi)
gin=fc.geometry().buffer(-30)
ann=fc.geometry().buffer(12000).difference(fc.geometry().buffer(1500),100)
p_pos=rt(lambda: ee.FeatureCollection.randomPoints(region=gin,points=PC,seed=11).getInfo(),'pos')
ly=H.select('lossyear').unmask(0); tc=H.select('treecover2000').unmask(0)
lab2=ee.Image(255).where(ly.eq(0).And(tc.gt(50)),0).where(ly.gte(15).And(ly.lte(19)).And(tc.gt(30)),1).rename('y').toInt()
lab2=lab2.updateMask(lab2.neq(255))
p_neg=rt(lambda: lab2.stratifiedSample(numPoints=PC,classBand='y',region=ann,scale=30,seed=11,
        classValues=[0,1],classPoints=[PC]*2,geometries=True,dropNulls=True,tileScale=8).getInfo(),'neg')
feats=[]
if p_pos:
    for f in p_pos['features']:
        c=f['geometry']['coordinates']; feats.append((c[0],c[1],2))
if p_neg:
    for f in p_neg['features']:
        c=f['geometry']['coordinates']; feats.append((c[0],c[1],f['properties']['y']))
print(k,'points',len(feats),flush=True)
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
