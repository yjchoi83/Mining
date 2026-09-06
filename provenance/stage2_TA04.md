# TA04 (seed S8, TC05 병합) — ASGM label efficiency와 Amazon→Ghana transfer

## 1. Literature
- ELDOR, arXiv:2605.15397 [V, in-session]: **UAV orthomosaic** 2,500 ha pixel-level segmentation benchmark (Peru Amazon), 4 task(semantic seg / seg-derived recognition / multi-label clf / VLM presence). 위성 해상도가 아니고 GEE에도 없으며 label efficiency·cross-region transfer를 다루지 않는다. **최강 경쟁자.**
- Earth Genome AEF mining tech note, 2025 (gray, [V per PROMPT §4.3]): Tapajos/Roraima에서 tile-level embedding statistics로 mining 탐지 — Amazon 단일 대륙, tile 단위, baseline 대비 label-efficiency 곡선 없음.
- Ecuador unregulated gold mining spatio-temporal detection, 10.5194/egusphere-2026-1854 [V]: 단일 지역 시계열 탐지, embedding·transfer 무관.
- Maus et al., "An update on global mining land use", 10.1038/s41597-022-01547-4 [V]: 본 연구의 reference label 원전(global mining polygons, ~2019 epoch).
- 보조: Lehmann et al. arXiv:2608.16614 [V] (GFM calibration/distribution shift — 원인 귀속 없음), 10.1016/j.jclepro.2025.147437 [V] (commodity-specific mining land-use, 2025).
- **Gap (2문장)**: ASGM 탐지에서 AEF embedding이 S2 composite baseline 대비 *몇 개의 label로* 동등 정확도에 도달하는지, 그리고 Amazon-trained probe가 서아프리카로 전이될 때 손실이 얼마이고 *로컬 label 몇 개면 전이가 무용해지는지* 아무도 측정하지 않았다. 기존 3편은 모두 단일 지역·단일 label 예산 설정이며, ELDOR는 UAV 해상도라 10 m 위성 운영 모드와 접점이 없다.

## 2. Data — 실제로 쓴 reference label
- `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL` 2019 존재 확인 [V] (AMZ box 2 tiles, GHA box 1 tile). calendar-year semantics.
- **[핵심 발견] `projects/sat-io/open-datasets/global-mining/global_mining_polygons` (Maus et al.)는 이 credential로 읽힌다** [V]: props AREA/COUNTRY_NA/ISO3_CODE. AMZ box(58–54°W, 8–4°S) 42 polygon / 240.0 km²; GHA box(3.2–0.9°W, 4.9–7.2°N) 245 polygon / 652.5 km². → **proxy label을 쓰지 않았다.** positives = Maus polygon 내부(30 m 침식).
- Hard negative는 **Maus polygon 주변 1.5–12 km annulus**로 공간 정합: `UMD/hansen/global_forest_change_2025_v1_13` lossyear 2015–2019 & treecover2000>30 = "mining 인접 비광산 forest loss(농업 개간)"; easy negative = lossyear 0 & treecover>50 안정 forest. Hansen/label raster는 `.unmask(0)` 필수(kit gotcha 1).
- Label-year 정합: Maus는 ~2019 누적 footprint(연도 속성 없음) → AEF 2019 · S2 2019로 맞췄다. 한계: (i) ASGM과 large-scale mine이 섞여 있고 Ghana box는 Tarkwa/Obuasi 산업광산을 포함, (ii) 소형 ASGM omission이 문서화되어 있어 hard negative 안에 미매핑 ASGM이 섞일 수 있다 → 보고 AUC는 **하한**. JRC GSW turbid-water proxy는 결국 불필요했다(GSW occurrence≥20% 면적비 AMZ 0.0024 / GHA 0.0002로 너무 희소).

## 3. Smoke test (T1 label-efficiency + T3 transfer + T5 retrieval)
n=2,700/region, class balance mining 900 / hard-neg 900 / stable 900 → binary pos_frac **0.333**, metric **ROC-AUC**, 5-fold GroupKFold on 0.1°(~11 km) block (AMZ 82 / GHA 158 block), subsample 5 seed 평균. Baseline = S2 annual median 8 band(B2,B3,B4,B8,B11,B12,NDVI,NBR) + 동일 logistic probe.
| labels | 25 | 50 | 100 | 250 | 500 | 1000 | full(2160) |
|---|---|---|---|---|---|---|---|
| AMZ AEF-64 | 0.621 | 0.686 | 0.780 | 0.810 | 0.828 | 0.850 | **0.855** (sd .027) |
| AMZ S2-8 | 0.535 | 0.534 | 0.573 | 0.596 | 0.622 | 0.635 | 0.638 (sd .052) |
| GHA AEF-64 | 0.892 | 0.921 | 0.940 | 0.958 | 0.967 | 0.974 | **0.977** (sd .008) |
| GHA S2-8 | 0.799 | 0.831 | 0.851 | 0.859 | 0.861 | 0.865 | 0.867 (sd .037) |
- **Label-efficiency crossover: AEF-64는 약 40 label(25→0.621, 50→0.686 사이 보간)에서 S2-8의 1,000 label 성능(0.635)에 도달 → ≥25배 label 절감.** S2는 label 1,000에서도 AEF의 100-label 성능(0.780)에 못 미친다. Ghana에서는 AEF 25 label(0.892)이 S2 1,000 label(0.865)을 이미 상회(>40배).
- **Transfer drop**: AMZ→GHA AEF 0.810(sd .024) vs GHA in-region 0.977 → **−0.167**; S2 0.702(sd .025) vs 0.867 → **−0.165**. 절대 낙폭은 사실상 동일하나 전이 후에도 AEF > S2. 역방향 GHA→AMZ는 비대칭: AEF 0.557(−0.298, 거의 chance) vs S2 0.586(−0.052) → TC01이 측정한 "AEF가 S2보다 cross-region에서 더 많이 잃는다"와 정합.
- **Few-shot 적응(핵심 부산물)**: AMZ pool + k Ghana label(테스트는 held-out GHA block) AEF 0:0.813 / 10:0.871 / 25:0.875 / 100:0.892 / 250:0.918 vs **Ghana-only** k label AEF 10:0.831 / 25:0.895 / 100:0.937 / 250:0.957 → **k≥25에서 negative transfer**(Amazon label이 오히려 방해). S2는 양쪽 모두 0.72–0.86에 정체.
- **T5 retrieval 실패**: AMZ mining 10 seed의 dot-product(=cosine, unit-norm) 검색 P@100은 base rate 0.333 대비 AEF AMZ 0.376(sd .096, 사실상 lift 없음) / **AEF GHA 0.001** / S2 AMZ 0.304 / S2 GHA 0.162. 유사도 상위는 mining 서명이 아니라 지역 배경 구조가 지배 → label-free 검색 모드는 성립하지 않는다. TC01의 per-region z-score 완화도 AEF 전이를 회복시키지 못했다(0.810→0.794; S2는 0.702→0.751로 개선).
- Confounder: proxy 아닌 대신 Maus의 mining-type 혼재(Ghana는 LSM 포함 → GHA 과제가 더 쉬움: 0.977 vs 0.855), hard negative 내 미매핑 ASGM, Maus 단일 epoch·연도 속성 부재, turbid-water 계절성, Amazon/Ghana는 geology뿐 아니라 mining style·배경 land cover가 동시에 달라 낙폭을 geology로 귀속 불가, 그리고 AEF 64 dim vs S2 8 dim의 feature 수 비대칭.

## 4. Scoring / decision
N 3 | R 3 | F 3 | A 3 | V 2 | J 3 = **17/18** → **PASS**. 근거: reference label이 GEE에서 실제로 읽히고(F↑), AEF-S2 격차가 fold sd(0.027/0.052) 대비 0.217로 압도적이며(A↑), label-efficiency 25배·negative transfer·retrieval 실패라는 세 개의 미보고 결과가 한 세션 pilot에서 이미 재현됐다. V는 Maus가 mining-type 혼재 누적 단일 epoch이고 field validation이 없어 2로 유지.
Top-3 risks: (1) Maus label의 ASGM/LSM 혼재와 소형 ASGM omission이 label-efficiency 우위와 지역 간 난이도 차이를 동시에 만들 수 있다 → Amazon Mining Watch·ELDOR(UAV) 다운로드 후 독립 검증 + Maus polygon을 면적/형상으로 ASGM/LSM 층화, Ghana에 galamsey 전용 VHR 판독 검증 세트. (2) GEE project가 **restricted mode**(noncommercial compute quota 초과)라 4°×4° stratifiedSample이 타임아웃 → mining polygon 주변 annulus로 region을 축소해 우회했고, 규모 확장 시 export/asset 사전계산 필요. (3) negative transfer 결과가 단일 region pair·2,700 sample·단일 연도에 기반 → Madre de Dios·Roraima·Cote d'Ivoire·Guyana로 다중 pair 확장과 연도 반복 없이는 일반화 불가.
Reviewer 2: "**label-efficiency 25배는 AEF 우수성이 아니라 64 dim vs 8 dim이라는 feature 수 차이의 산물이다**. S2 baseline이 부당하게 약하고(annual median 8 band), retrieval P@100이 base rate 수준이라는 당신들의 결과가 오히려 embedding이 mining을 실제로 인코딩하지 않는다는 증거다." 선제 대응: (a) S2 baseline을 monthly percentile/harmonic + S1 backscatter로 60여 feature까지 확장해 dimensionality-matched 비교, 동시에 AEF를 PCA 8 dim으로 축소한 대칭 실험을 제시; (b) AEF@100(0.780)이 S2 full 2,160 label(0.638)을 이미 넘으므로 sample-per-parameter 효과로 설명되지 않음을 명시; (c) retrieval 실패는 "mining을 인코딩하지 않음"이 아니라 "supervised 방향 없이는 지역 배경 축이 지배함"임을 TC01의 static-decodable subspace 결과와 결합해 dim-level로 분해; (d) negative transfer는 label 예산을 통제한 동일 테스트 세트 비교이므로 baseline 강도와 무관하게 성립.
