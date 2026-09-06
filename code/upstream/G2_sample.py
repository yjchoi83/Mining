# G2: rich classical baseline sampling at the SAME stratified points as Stage-2 TA04 (seed=7)
import ee,time,random,sys,pandas as pd,numpy as np
for a in range(60):
    try: ee.Initialize(); break
    except Exception: time.sleep(10+random.random()*15)
def rt(f,tag='',n=30):
    for a in range(n):
        try: return f()
        except Exception as e:
            s=str(e)
            if any(t in s for t in ('429','Too Many','imed out','Internal error','503')):
                time.sleep(12+random.random()*20); continue
            print(tag,'ERR',s[:150],flush=True); return None
    print(tag,'GIVEUP',flush=True); return None
AEF=ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
def aef(y,r): return AEF.filterDate(f"{y}-01-01",f"{y+1}-01-01").filterBounds(r).mosaic()
B=['B2','B3','B4','B8','B11','B12']
def s2col(y,r):
    def m(i):
        q=i.select('QA60'); c=1<<10|1<<11
        return i.updateMask(q.bitwiseAnd(c).eq(0)).divide(10000)
    return (ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterDate(f"{y}-01-01",f"{y+1}-01-01")
            .filterBounds(r).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',60)).map(m))
def idx(i):
    return (i.addBands(i.normalizedDifference(['B8','B4']).rename('NDVI'))
             .addBands(i.normalizedDifference(['B8','B12']).rename('NBR'))
             .addBands(i.normalizedDifference(['B3','B8']).rename('NDWI'))
             .addBands(i.normalizedDifference(['B11','B8']).rename('NDMI'))
             .addBands(i.expression('(b.B4-b.B2)/(b.B4+b.B2)',{'b':i}).rename('IOR')))
def rich(y,r):
    col=s2col(y,r).map(lambda i: idx(i.select(B)))
    bs=B+['NDVI','NBR','NDWI','NDMI','IOR']
    pc=col.select(bs).reduce(ee.Reducer.percentile([10,25,50,75,90]))          # 55
    sd=col.select(['NDVI','NBR','B8','B11']).reduce(ee.Reducer.stdDev())        # 4  (intra-annual)
    md=col.select(bs).median()
    # focal texture on annual median NIR + NDVI
    tx=ee.Image.cat(
        md.select('B8').reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.square(3,'pixels')).rename('B8_sd3'),
        md.select('B8').reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.square(7,'pixels')).rename('B8_sd7'),
        md.select('NDVI').reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.square(3,'pixels')).rename('NDVI_sd3'),
        md.select('NDVI').reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.square(7,'pixels')).rename('NDVI_sd7'),
        md.select('B8').subtract(md.select('B8').reduceNeighborhood(ee.Reducer.mean(), ee.Kernel.square(7,'pixels'))).rename('B8_dev7'))
    s1=(ee.ImageCollection("COPERNICUS/S1_GRD").filterDate(f"{y}-01-01",f"{y+1}-01-01").filterBounds(r)
        .filter(ee.Filter.eq('instrumentMode','IW'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation','VV'))
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation','VH')).select(['VV','VH']))
    sp=s1.reduce(ee.Reducer.percentile([10,50,90]))                             # 6
    ss=s1.reduce(ee.Reducer.stdDev())                                           # 2
    rat=sp.select('VV_p50').subtract(sp.select('VH_p50')).rename('VVVH_p50')
    st=sp.select('VV_p50').reduceNeighborhood(ee.Reducer.stdDev(), ee.Kernel.square(3,'pixels')).rename('VV_sd3')
    return ee.Image.cat(pc,sd,tx,sp,ss,rat,st)
MINE=ee.FeatureCollection("projects/sat-io/open-datasets/global-mining/global_mining_polygons")
H=ee.Image("UMD/hansen/global_forest_change_2025_v1_13")
Y=2019; PC=int(sys.argv[2]) if len(sys.argv)>2 else 900
ROIS={"AMZ":[-58.0,-8.0,-54.0,-4.0],"GHA":[-3.2,4.9,-0.9,7.2]}
k=sys.argv[1]; roi=ee.Geometry.Rectangle(ROIS[k])
fc=MINE.filterBounds(roi); mine=ee.Image(0).paint(fc,1)
buf=ee.Image(0).paint(fc.map(lambda f: f.buffer(1000)),1)
ly=H.select('lossyear').unmask(0); tc=H.select('treecover2000').unmask(0)
hard=ly.gte(15).And(ly.lte(19)).And(buf.eq(0)).And(tc.gt(30))
stable=ly.eq(0).And(buf.eq(0)).And(tc.gt(50))
lab=ee.Image(255).where(stable,0).where(hard,1).where(mine.eq(1),2).rename('y').toInt()
lab=lab.updateMask(lab.neq(255))
import os,json
capfile=f'scratch/G2_{k}_pts.json'
if os.path.exists(capfile) and PC==900:
    lst=json.load(open(capfile)); print(k,'n(cached)',len(lst),flush=True)
else:
    pts=rt(lambda: lab.stratifiedSample(numPoints=PC,classBand='y',region=roi,scale=20,seed=7,
            classValues=[0,1,2],classPoints=[PC]*3,geometries=True,dropNulls=True,tileScale=4),'strat')
    n=rt(lambda: pts.size().getInfo(),'sz'); print(k,'n',n,flush=True)
    lst=rt(lambda: pts.toList(n).getInfo(),'lst')
    json.dump(lst,open(capfile,'w'))
feats=[(f['geometry']['coordinates'][0],f['geometry']['coordinates'][1],f['properties']['y']) for f in lst]
stack=aef(Y,roi).addBands(rich(Y,roi))
rows=[];CH=150
for i in range(0,len(feats),CH):
    ch=feats[i:i+CH]
    fcs=ee.FeatureCollection([ee.Feature(ee.Geometry.Point([x,yy]),{'y':lb}) for x,yy,lb in ch])
    r=rt(lambda: stack.sampleRegions(collection=fcs,scale=10,geometries=True,tileScale=8).getInfo(),'ch%d'%i)
    if r is None: continue
    for ft in r['features']:
        d=dict(ft['properties']); cc=ft['geometry']['coordinates']
        d['lon'],d['lat']=cc[0],cc[1]; rows.append(d)
    if i%600==0: print(k,'chunk',i,'tot',len(rows),flush=True)
pd.DataFrame(rows).to_csv(f'scratch/G2_{k}.csv',index=False)
print(k,'DONE',len(rows),flush=True)
