# Stage 4 SUMMARY (2026-09-04)
실행: N(문헌 재검증) → D1-D5(desk) → G1-G2(GEE). 산출물 8개 파일. Stage 1-3은 재실행하지 않았다.

## 개정된 GO 리스트 (N + G1 반영)
| ID | Stage 3 | **Stage 4 판정** | 변경 이유 |
|---|---|---|---|
| TB01 | **GO** | **CONDITIONAL-GO** ↓ | G1: 독립 월(S2 breakpoint) 적용 시 CG(DRC) headline 붕괴 — in-year 탐지 98.7%→**93.6%**, Q4 81.7%→**75.4%**. BR은 재현(a,b CI 겹침, ~99%). 관측밀도 tercile에서 a·b가 최대 2배 흔들려 confound가 실재. Dec-shift는 BR n=40→**n=9**로 정밀값 신뢰 불가 |
| TA04 | C-GO | **C-GO 유지** (수치 개정) | G2: 강한 baseline(74-feature classical + LightGBM, AEF-64와 차원 정합)에서 multiple이 "≥25-40배"→**AMZ 19.9배(CI 17.3-22.4) / GHA 15.7배(12.8-19.5)**로 하락. 그래도 사전등록 반증선 3배를 크게 상회. full-data AUC도 여전히 +0.108/+0.047 우세 → 이득이 low-label regime 한정이 아님 |
| TB02 | C-GO | C-GO (병합 spine) | N: SURVIVES. D2: TE02를 companion 섹션으로 흡수 |
| TD01 | C-GO | C-GO | N: SURVIVES (14개 mechanism 쿼리 OVERLAP 0) |
| TH01 | C-GO | C-GO + **조건 추가** | D3: DMZ(±2 km)·CCZ 제외로 flagship 수치(cosine 0.504→0.967) **폐기** — 근접 stratum은 access restriction이었음. RQ2·RQ3는 무관하게 생존. 신규 조건 C3 = 5-30 km band trend가 null이 아닐 것 |
| TE02 | C-GO | C-GO (TB02에 흡수) | D2: 단독 서사 약, TB02 spine의 2번째 pathway로 |
| TC01 | C-GO | C-GO (병합 spine) | D2: TE06를 흡수해 구제 |
| TA02 | C-GO | C-GO | N: SURVIVES. 단 D1: MapBiomas age label이 Landsat 파생 → headline R² 일부 인플레이트, ALS/ATL08 게이트 통과 전 발표 불가 |
| **TE06** | C-GO | **NARROWED → 단독 폐기** ↓ | N: **arXiv:2609.03480**(Denmark tree-species, matched spectral-temporal baseline vs AEF/TESSERA)가 RQ1을 이미 답했다 — baseline이 전반적 우세, embedding은 low-label에서만. RQ2(relief-conditioned absorption)만 novelty로 남아 TC01에 병합 |
**무조건 GO = 0개** (Stage 3의 1개에서 감소). 병합 후 실질 논문 단위는 **7개**:
TB01, TA04, TB02(+TE02), TD01, TH01, TC01(+TE06), TA02. KILLED-BY-LITERATURE는 0건이다.

## 첫 프로젝트 권고 (변경)
**TB01을 유지하되 범위를 재조정한다**: BR(Pará/MT)을 primary로, CG는 replication으로 강등하고
unresolved 28.3%·관측밀도 confound를 본문에 명시. 외부 데이터 게이트가 없다는 장점은 그대로다.
**병행은 TA04** — multiple이 20배 수준으로 내려갔어도 효과는 견고하고, W1의 ASGM-only reference 확보만
선행하면 된다. 부수 성과: G1이 RADD latency를 수동 판독 없이 얻었다(BR median 0개월/15.4%가 ≥2개월 지연,
CG median 2개월/**52.6%**가 ≥2개월 지연) — Stage-3가 n≈600 수동 판독으로 계획했던 항목을 대체한다.

## 각 item 핵심 발견
- **N**: kill 0, narrow 1(TE06). Semantic Scholar가 세션 대부분 429 → TB01/TB02/TC01은 **arXiv 단독 커버리지**이고, 429 쿼리는 어느 방향으로도 증거로 쓰지 않았다. 투고 전 재조회 권고. 신규 필수 인용 12건.
- **D1**: reference 39행 감사. HIGH = TC01의 WorldCover 단독 primary label(S1+S2+DEM 흡수), TA02의 MapBiomas age. 현재 contaminated reference로 headline을 세운 곳 5건(TC01, TA02, TE02, TB01, TA04).
- **D2**: TB02+TE02 = **MERGE ASYMMETRICALLY**(TB02 spine). TC01+TE06 = **MERGE**(TC01 spine) — TE06 구제.
- **D3**: TH01 redesign. flagship 수치 폐기, RQ2·RQ3 생존, 신규 기여 2건(DMZ 재자연화 정량화, 강원 고랭지 analog transfer), VHR 판독 30→50-55 person-hours.
- **D4**: metric 약 90개 정의. 최악의 ambiguity: TD01 "3-class bal-acc"는 실제 4-class 결과, TH01 0.750 vs 0.674는 model-vs-label과 label-vs-label의 apples-to-oranges, "p90/5%-calibrated threshold"가 세 토픽에서 서로 다른 정의, TE02 SNR 0.23은 서로 다른 두 실험의 비율, "SE의 20배"류는 fold sd가 아닌 별도 SE, **block-bootstrap CI는 어디에서도 실행되지 않았다**(Stage-3 계획일 뿐).
- **D5**: 즉시 착수 가능 = ORNL ALS(117 GB), DETER-B WFS, Maus v2(PANGAEA), TESSERA(CC0). 부분 차단 = 환경부 토지피복(로그인), KFS 임상도(**자료신청 심사** + KOGL 3 변경금지). **ELDOR는 브리핑 설명과 불일치** — 실제로는 UAV 초고해상도 segmentation 데이터셋이므로 용도 재정의 필요. Critical path: TH01 두 게이트 + TD01 ALS가 W1-2에 동시 병목.
- **G1/G2**: 위 표 참조. 두 GEE item 모두 <=10k samples/call, ROI <=1x1도, export 없음으로 예산 내 수행.

## 다음 결정 3개
1. TB01을 BR-primary로 재작성할지, CG 붕괴를 별도 negative-result 절로 살릴지. 2. `data/rok/` 확보(KFS 심사 대기)를 지금 착수할지 — TH01의 분기점. 3. 모든 headline에 block-bootstrap CI를 실제 계산할지(현재 전부 fold sd).
