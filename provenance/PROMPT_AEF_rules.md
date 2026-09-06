# AlphaEarth (AEF) Research-Topic Exploration — Claude Code Prompt (final, 2026-09)

Usage: save this file as `PROMPT.md` in the project folder, edit §0, then tell Claude Code:
"Read ./PROMPT.md and execute it end-to-end." If this text was pasted instead of saved, first
write it verbatim to `WORKDIR/PROMPT.md` so subagents can read it by section.

## 0. CONFIG (edit before running)

```yaml
GEE_PROJECT: ""            # GCP project id for Earth Engine. Empty -> DESK_ONLY mode (no pilots; F scored conservatively)
REPORT_LANGUAGE: ko        # ko = Korean prose with English technical terms/titles. en cuts output tokens ~30%
AUTOPILOT: true            # false -> pause once after the Stage 1 ranking for my review
WORKDIR: ./aef_explore
LOCAL_DATA_DIR: ./aef_explore/data   # optional: ROK land-cover / forest-type files under data/rok/ (see §6 D1)
MUST_EVALUATE: [D1]        # carried into Stage 2 regardless of Stage-1 rank; may be killed only by Stage-2 evidence
PRIORITY_REGIONS: [Amazon basin, Congo basin, West & East African cities, Sahel/Miombo,
                   Korean Peninsula (DPRK, DMZ/CCZ), SE Asia (secondary)]
PRIORITY_PROBLEMS: [deforestation & degradation, agricultural frontier (soy/cattle/cocoa/oil palm),
                    artisanal mining, informal urban expansion, data-denied-territory monitoring,
                    conflict & humanitarian land change, other verifiable real-world land problems]
TARGET: ">=5 GO topics after Stage 3; ultimate venues IEEE TGRS and RSE; MDPI excluded"
BUDGETS:
  stage1_landscape_queries: 8          # main agent, shared novelty baseline
  stage1_queries_per_subagent: 4       # per bucket, NOT per candidate (shallow by design)
  stage2_queries_per_topic: 6
  stage2_gee_checks_per_topic: 3
  stage2_pilot_runs_per_topic: 3       # each <=10 min, <=10k samples, <=80-line throwaway script
  stage3_queries_per_topic: 4
  max_parallel_gee_pilots: 4
  stage2_wallclock_cap_hours: 2
```

## 1. MISSION

You are a remote-sensing research strategist and hands-on RS/ML engineer. Discover, screen, and
validate research topics built on Google DeepMind's AlphaEarth Foundations (AEF) Satellite
Embeddings that (a) address a real-world environmental, development, humanitarian, or security
problem at strategic scale, (b) can be verified against existing independent reference data, and
(c) are plausibly publishable in IEEE TGRS or Remote Sensing of Environment (RSE), with fallbacks
per §10. Run three stages, each stricter than the last, and deliver >=5 GO topics with one-page
proposals and target journals. Exploration speed and token economy beat polish; scientific rigor
(§3) is non-negotiable. The "apply AEF to X" space is already crowded (§4.3): every candidate must
state what it adds beyond the known work.

## 2. OPERATING RULES (speed and token discipline)

1. No engineering ceremony. Do NOT: init git, write tests/linters/type hints/docstrings/READMEs/CI,
   verify checksums or SHAs, audit licenses (one line max), pin dependencies, package anything,
   add retries beyond one, or refactor. Pilot scripts: single file, <=80 lines, throwaway, in `scratch/`.
2. Print little. Never dump >30 lines of any file or API response; filter with `jq`, `head`,
   `select=` fields, `per-page=5`. No plots before Stage 3 (numbers only). Save results to files;
   chat summaries <=15 lines per stage. Never re-read files you wrote this session; never restate
   these instructions or announce what you are about to do.
3. Literature lookups: prefer compact structured APIs via `curl` + `jq`:
   - OpenAlex: `https://api.openalex.org/works?search=<q>&per-page=5&filter=from_publication_date:2025-01-01&select=title,publication_year,doi,primary_location,cited_by_count`
   - Semantic Scholar: `https://api.semanticscholar.org/graph/v1/paper/search?query=<q>&limit=5&fields=title,year,venue,externalIds,citationCount`
   - arXiv API: `http://export.arxiv.org/api/query?search_query=all:<q>&max_results=10` (grep `<title>`, `<id>`)
   Use WebSearch/WebFetch only for gray literature (Google/GEE blogs and catalog, TESSERA site,
   38 North / Beyond Parallel construction dates) or when the APIs fail.
4. Fan out with subagents (Task/Agent tool). Each subagent reads only the sections of PROMPT.md it
   needs (§2-§3, §7, its stage in §8, plus §5-§6 for its bucket; use line ranges), writes its own
   file under WORKDIR, and returns <=10 lines to you. You (main agent) only merge, score, decide.
   Never paste this whole prompt into a subagent prompt. Cap concurrent GEE pilots at
   `max_parallel_gee_pilots`. Subagent-to-main communication is always English regardless of
   REPORT_LANGUAGE.
5. No questions unless truly blocked (no network at all). If GEE auth fails, print the one-line
   fix once and continue in DESK_ONLY mode. If `data/rok/` is empty, run D1 with fallback labels
   (§6) and flag `LABELS=FALLBACK`. Otherwise state assumptions in one `ASSUMPTIONS:` line and
   proceed.
6. Wall clock: if Stage 2 pilots exceed `stage2_wallclock_cap_hours`, run remaining pilots in
   Stage-1-score order and mark the rest `PILOT=PENDING`.

## 3. SCIENTIFIC RIGOR (non-negotiable)

1. Never fabricate or "recall" references. Every cited work must be verified in-session via
   API/DOI/arXiv id and tagged [V]; otherwise tag [U] and never build an argument on it.
2. Novelty = a specific unanswered research question with a plausible, testable answer. "AEF has
   not been applied to region X" is NOT novelty. An existing paper kills a topic only if it answers
   the same RQ with comparable data and convincing validation.
3. Separate convenience value (no GPU, fast) from scientific value (better accuracy, transfer,
   label efficiency, a new measurand, or new insight about the model/sensor/environment). Only
   scientific value justifies TGRS/RSE. Score A (§7) accordingly.
4. Every pilot: spatial block split (>=10 km blocks or separate tiles; GroupKFold), never random
   pixel split; one mandatory baseline (cloud-masked annual Sentinel-2 median composite + same
   classifier, or a strong published product); report n, class balance, metric, fold spread.
   Name confounders: label-year vs embedding-year mismatch, resolution mismatch, label noise,
   spatial autocorrelation.
5. Temporal semantics: the AEF year-Y layer summarizes observations within calendar year Y (verify
   the exact wording in the GEE catalog once). Align reference labels to that window. PRODES uses
   an Aug-Jul year; MapBiomas and TMF are calendar-year.
6. Real-world verifiability: every surviving topic must name (i) the problem, (ii) the decision
   or stakeholder it informs, (iii) the independent data that could prove the approach wrong.
7. Kills with reasons are a deliverable. Never soften kills to hit the quota; if too few survive,
   generate more candidates (Stage 1.5) rather than lowering the bar. MUST_EVALUATE topics are
   exempt from Stage-1 kills only, not from Stage-2 evidence.
8. Predict "Reviewer 2": for each survivor, write the most damaging plausible objection and how the
   design preempts it.
9. Bucket H ethics: keep every security/humanitarian topic at strategic scale, on public data,
   with a stated civilian-protection or transparency rationale; never propose anything listed as
   out of scope in §5-H. Add one line on ethical/data-provenance risk to each H card.

## 4. BACKGROUND FACTS (pre-verified as of 2026-09; do not re-research, only extend)

### 4.1 Model and dataset
- AlphaEarth Foundations, Google DeepMind (Brown et al., 2025, arXiv:2507.22291). "Embedding
  field" model: Space-Time-Precision encoder, von Mises-Fisher bottleneck on the unit sphere, 64-D
  unit-norm pixel embeddings at 10 m, annual summaries. Confirmed inputs: Sentinel-1 C-band SAR,
  Sentinel-2, Landsat 8/9 (multispectral, pan, thermal), GEDI canopy-height rasters, GLO-30 DEM,
  ERA5-Land monthly aggregates, ALOS PALSAR-2 ScanSAR, GRACE monthly mass grids, geocoded text
  (Wikipedia/GBIF-type). DEM and climate are DIRECT inputs, not leakage: frame E-bucket questions
  as "static/climate-input dependence". Training uses teacher-student consistency under random
  source/timestep dropout, i.e. designed insensitivity to missing sources; whether that holds for
  the 2022-2024 Sentinel-1 gap is an empirical question. Official evaluations: thematic mapping,
  biophysical regression, change detection (binary change from LCMAP-style labels). Check the
  evaluation suite once and list absent problem-specific Global-South / data-denied tasks.
- Dataset "Satellite Embedding V1": GEE ImageCollection `GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL`,
  bands A00-A63 (float), one image per year per tile -> `filterDate(year)` + `mosaic()`. Years
  2017-2025 inclusive (9 layers; 2025 added early 2026). Public GCS bucket
  `gs://alphaearth_foundations` (COGs, int8 quantized, -128 = masked, dequantization documented;
  provider-pays since Jul 2026 -> free egress); community mirror on Source Cooperative
  (`tge-labs/aef`; bottom-up COG quirk). CC-BY 4.0. Google commits to continued annual production
  with >=1 year notice of changes.
- Documented uses: supervised classification, regression, clustering, change detection, similarity
  search. Similarity = dot product (= cosine on unit vectors); angular change = arccos(dot).
- Sub-annual "Custom Satellite Embeddings" exist only as a Google Maps Platform private preview
  (Jul 2026): not usable for open research. The public product is annual-only; that constraint is
  itself a research theme (short-lived / late-year events, detection lag).

### 4.2 Competitors and baselines
- TESSERA (Feng et al., 2025): 128-D, 10 m, Sentinel-1+2 only, Barlow Twins, pixel-level; 2024
  global, expanding toward 2017-2025. No climate/DEM inputs -> natural contrast for static-input
  hypotheses.
- Other GFM baselines: Prithvi-EO-2.0, Clay, DOFA, Copernicus-FM, TerraMind, SatMAE++.
  Classical baseline: S2/S1 annual composites + RF/LightGBM.

### 4.3 Known AEF work (verified 2026-09; verify details and expand in Stage 1)
Taken -> plain application is dead; only the stated gaps remain:
- Commodities/forest: Google Forest Data Partnership annual pan-tropical 10 m cocoa/coffee/rubber
  maps powered by AEF (2025b, CC-BY, in GEE; May 2026); GEM-Forest global embedding-based
  forest / tree-crop map for 2020 (EUDR). Gap: independent validation / failure analysis only.
- Urban: slum detection and density mapping with AEF across 12 cities, 69 city-year pairs
  2017-2024, spatial-block CV, GRAM pseudo-mask labels; finds city-scale representational drift
  (arXiv:2605.10029). Gap: field-validated labels, growth dynamics.
- Mining: ELDOR illegal-gold-mining dataset/benchmark, Amazon (arXiv:2605.15397); Earth Genome
  tech note (Oct 2025) already runs AEF mining detection (Tapajos, Roraima) with tile-level
  embedding statistics. Gap: label-efficiency/transfer using ELDOR as reference.
- Conflict: building-level damage mapping fusing AEF embedding change (Earth Mover's Distance) with
  Sentinel-1 PWTT over 75,825 footprints in 7 Ukrainian cities (AEF alone AUC ~0.59, fusion
  ~0.68, degrades leave-one-city-out); Scientific Reports 2026 Ukraine change detection uses AEF as
  a validation product; AEF land-cover priors for SAR flood segmentation (arXiv:2606.29134).
  Gap: annual-scale damage density, reconstruction, displacement, DPRK monitoring (no AEF work
  on DPRK found).
- Forest/biophysical: national canopy cover with AEF+Landsat, Nigeria (RSASE, 2026); height
  inference from AEF (arXiv:2602.17250); Biomazon Amazon 3D-structure/biomass dataset using AEF and
  TESSERA predictors (arXiv:2606.05368), citing Lucero et al.: spectral indices beat AEF for AGB
  in tropical Andean forest -> AEF is not uniformly dominant.
- Agriculture: "Harvesting AlphaEarth" benchmark (Ma et al.); tomato cropping systems, California
  (arXiv:2605.21804); Dutch NFI tree species (arXiv:2508.18829).
- Interpretability: Rahman 2026 (RSASE; physically interpretable dims, CONUS); "What on Earth is
  AlphaEarth?" (arXiv:2603.16911); embedding geometry for agentic reasoning (arXiv:2604.18715).
  Dimension-level decodability is done; change-detection consequences are listed as future work.
- Comparisons: AEF vs TESSERA for Local Climate Zones, Swiss cities (arXiv:2606.20034); "Better
  Together" complementarity of AEF/TESSERA/GeoCLIP/SatCLIP on 2024 data (arXiv:2605.18667).
- Other: landslide susceptibility (arXiv:2601.07268; notes label-year alignment effects); peatland
  carbon (Koch et al. 2025); hydrological models (Qu et al. 2026); climate-sensitive disease
  modelling (arXiv:2605.10949); lightweight global embedding database (arXiv:2601.11183).
- Practitioner change-detection reports (blogs, not journals): cosine drift vs MapBiomas with
  ~10-25 deg drift even for stable classes (Apr 2026); leave-one-out medoid + robust z-score
  anomaly scoring on the 2017-2025 series (Wherobots, Jun 2026); palm-oil mill retrieval from ~50
  labels (Sumatra). Temporal-fidelity questions are being probed informally with no journal
  treatment yet: move fast.

### 4.4 Reference and label data
GEE (verify asset IDs once before use): Hansen GFC (annual lossyear); JRC Tropical Moist Forest
(annual deforestation/degradation); RADD and GLAD alerts (dated); MapBiomas (Brazil/Amazon;
secondary-vegetation age); PRODES/DETER (INPE; DETER has dated degradation classes); Dynamic
World; ESA WorldCover; GHSL built-up/population (P2023A); WSF 2019 / WSF-Evolution; Google Open
Buildings and Open Buildings 2.5D Temporal (annual 2016-2023, Global South); GEDI L2A/L4A; ETH
and Meta canopy height; Global Mangrove Watch; JRC Global Surface Water; MODIS/VIIRS burned area;
WorldCereal; WorldPop; per-pixel observation counts computable from `COPERNICUS/S1_GRD`,
`COPERNICUS/S2_SR_HARMONIZED`, Landsat collections (for drift audits).
External (download once, keep small): LandCoverNet (Radiant Earth, 10 m, 2018, hand-labeled,
Africa/S. America); IDEAMAPS / SLUMAP deprived-area labels (Lagos, Nairobi, Accra); Maus et al.
mining polygons, Amazon Mining Watch, ELDOR; FDaP commodity maps and GEM-Forest (products to
validate, not ground truth); UNOSAT damage assessments (UNITAR), Copernicus EMS activations, ACLED
events, UNHCR Operational Data Portal / HDX camp footprints, HOT/OSM building and construction
dates, Wikidata infrastructure opening dates, UNODC opium surveys, Colombia SIMCI coca census
(municipal).
Korea (for D1/D5): ROK Ministry of Environment land-cover map (EGIS; 대분류 7 / 중분류 22 /
세분류 41 classes; manual download, needs account), Korea Forest Service forest-type map (임상도,
FGIS), MAFRA FarmMap (팜맵, parcel-level farmland), KFS wildfire records; KFS/NIFoS published DPRK
forest-degradation estimates (coarse cross-check only); FAO GIEWS / WFP DPRK crop reports;
38 North and CSIS Beyond Parallel dated imagery analyses (construction dates of state projects).
DPRK has no in-situ data: validation = stratified VHR visual interpretation (Google Earth
historical imagery) + cross-product agreement.

### 4.5 Input-stream events (hypotheses; verify)
Sentinel-1B failure (Dec 2021) reduced SAR coverage over Africa and South America during 2022-2024
until Sentinel-1C (Dec 2024); Landsat 9 from late 2021; Sentinel-2C from 2024; ERA5-Land/GRACE
inputs may inject drought/anomaly signal into apparent "change" on stable land.

## 5. EXPLORATION ANGLES (every bucket must yield candidates; >=25 candidates total)

A. Real-world land-change problems (Amazon/Congo/Africa first): deforestation vs degradation
   (selective logging, fire, edge effects); agricultural frontier (soy/cattle in Cerrado-Chaco,
   cocoa in West Africa, oil palm); artisanal and small-scale gold mining; informal urban
   expansion; infrastructure footprints (frontier roads, dams, refugee/IDP settlements); wetlands,
   mangroves, peatlands (Cuvette Centrale); woodland degradation and charcoal (Miombo/Sahel);
   conflict-linked cropland abandonment; secondary-forest regrowth and age.
B. Change-detection methodology on annual embeddings: null distribution of inter-annual angular
   change for stable land vs true change; biome-adaptive thresholds; 9-year trajectory models
   (segmentation, break detection); detectability of late-year or short-lived events vs alert
   timing; year-effect / temporal-stability audit tied to input availability.
C. Transfer and label efficiency: cross-region probe transfer (Brazil -> Congo, ROK -> DPRK);
   label-efficiency curves AEF vs TESSERA vs raw S2 vs other GFMs; domain-shift metrics;
   similarity search + active learning for rare targets (mines, clandestine airstrips, kilns,
   mills, small dams).
D. Fusion and biophysical retrieval: AEF + GEDI/ICESat-2 for canopy height/AGB and degradation
   intensity in tropical forest; AEF + SAR/optical residuals; smallholder crop type/yield.
E. Representation analysis and critique: dependence on static/climate inputs (DEM, ERA5, GRACE)
   and whether it inflates in-domain accuracy while contaminating change signals (drought-year
   false positives) and hurting transfer; patch-context effects at boundaries and in <1 ha
   smallholder fields; int8 quantization effects; embedding disagreement as uncertainty.
F. Rigorous evaluation and benchmarking: a Global-South benchmark of GFM embeddings with spatial
   CV and design-based area estimation; over-optimism from spatial autocorrelation in
   embedding-based classifiers; conditions under which AEF loses to simple spectral baselines.
G. Operational MRV and policy: uncertainty quantification / conformal prediction for REDD+ and
   national forest monitoring; design-based area estimation with CIs where no NFMS exists;
   plot-level commodity-compliance mapping (EUDR-style).
H. Defense, security and humanitarian applications (open data, transparency-oriented, strategic
   scale only). In scope: monitoring of data-denied territories for humanitarian/economic
   indicators (DPRK forest recovery, hillside farming, greenhouse complexes, housing districts,
   regional-development factories, flood damage and recovery; DMZ/CCZ ecology and wildfire);
   conflict-driven cropland abandonment and food security tied to ACLED event density;
   neighbourhood-scale conflict damage density and multi-year reconstruction (building-level AEF
   damage detection is published and weak, §4.3); displacement / IDP-camp emergence and growth;
   explosive-ordnance risk prioritisation from post-conflict land abandonment; environmental
   footprint of military land use (training-range fire scars, base construction); transparency
   monitoring of large civil-military infrastructure construction (airfields, ports, roads, dams)
   validated with OSM/Wikidata dates and VHR; illicit-crop extent (poppy, coca) vs UNODC/SIMCI
   aggregates; conflict-environment nexus (armed-group-linked deforestation and mining);
   GNSS-denied coarse localisation for disaster-response UAVs using AEF as a compact global
   reference map (dual-use, civil framing).
   Out of scope, never propose: targeting or weapon-employment support; tracking of forces,
   vehicles or individuals; real-time tactical use; detection of specific weapon systems or
   military facilities; aiding evasion of monitoring. AEF's annual 10 m nature makes such uses
   infeasible anyway. Mark dual-use explicitly in the card.

Diversity constraint for the final GO set: >=3 buckets and >=2 regions represented.

## 6. SEEDS (screen exactly like any other candidate; tiers reflect the §4.3 pre-screen)

### Tier 1 — temporal fidelity of annual embeddings (no journal treatment found)
- S1 Event timing inside the year: for a pixel cleared in month m, does the year-Y embedding lie
  near the geodesic between its pre- and post-clearing states with mixing weight ~(12-m)/12? Test
  timing recovery and detection lag against dated RADD/GLAD/DETER events (Amazon, Congo); control
  for wet-season optical gaps; propose a lag-aware change rule.
- S2 Decomposing inter-annual drift on stable land: attribute stable-pixel drift 2017-2025 to
  (a) per-pixel S1/S2/Landsat observation counts (Sentinel-1B gap 2022-2024 over Africa and South
  America), (b) ERA5-Land/GRACE anomalies (drought years), (c) residual; quantify change-detection
  false-positive risk; Europe/CONUS controls. A small effect is still a publishable robustness
  result (GRSL/JSTARS scale).

### Tier 2 — open, label-dependent
- S3 Degradation intensity: separability of DETER degradation classes / JRC-TMF degradation from
  intact forest at 10 m; relate angular change to GEDI-derived structure loss.
- S4 Static-input dependence vs transfer: do DEM/climate inputs raise in-domain accuracy but hurt
  cross-region transfer? Brazil -> Congo and ROK -> DPRK probes; AEF vs TESSERA as the natural
  contrast; LandCoverNet / MapBiomas / ROK labels. Tie to the Andean AGB counter-result.
- S5 Secondary-forest age encoding: age regression from a single-year embedding (MapBiomas age
  labels) vs trajectory dating; saturation age; carbon-accounting implications.
- S6 When does AEF underperform simple spectral baselines? Systematic failure-mode study across
  biophysical targets with diagnostics (saturation, static-input dominance, patch context).

### Tier 3 — pivots of taken topics (keep only if Stage 1 confirms a real gap)
- S7 Independent design-based validation of FDaP cocoa/coffee/rubber 2025b and GEM-Forest 2020 in
  Ghana / Cote d'Ivoire: shade-cocoa omission, EUDR-cutoff implications.
- S8 ASGM label-efficiency and Amazon -> Ghana transfer using ELDOR as reference: AEF vs TESSERA
  vs CNN baselines. Kill if ELDOR is unusable.
- S9 Informal-settlement growth in African cities 2017-2025 with field-validated labels
  (IDEAMAPS / SLUMAP) instead of pseudo-masks. Kill unless a clear gap vs arXiv:2605.10029 exists.
- S10 Design-based area estimation with embedding-derived strata where no map exists. Prefer to
  embed as the validation design inside other topics; standalone only if variance reduction vs
  conventional strata is large.

### Tier D — bucket H (D1 is MUST_EVALUATE)

D1 — DPRK annual land-use monitoring under zero ground truth (flagship; carry to Stage 2)
- Problem and stakeholders: DPRK land use is unobservable in situ but drives food security, flood
  risk, and forest cooperation planning (KFS inter-Korean forestry cooperation, Ministry of
  Unification, FAO/WFP assessments). The 2015-2024 "forest restoration campaign" and the 2024
  "20x10 regional development" policy are testable state programmes whose outcomes are disputed.
- Research questions:
  Q1 Net forest recovery vs hillside-farming expansion 2017-2025 and its spatial pattern relative
     to campaign priority zones; does the AEF trajectory support KFS/NIFoS degradation estimates?
  Q2 Detection timing of large dated state projects as natural validation events: Jungpyong
     greenhouse farm (2019), Ryonpho greenhouse farm on a former airfield (2022), Kangdong
     greenhouse farm (2024-2025), Pyongyang housing districts (Songhwa 2022, Hwasong 2022-2024),
     20x10 local factories (2024-): detection lag in annual embeddings (links to S1).
  Q3 2024 Yalu-river flood (Sinuiju/Uiju): annual damage signature and 2025 recovery.
  Q4 ROK -> DPRK transfer gap: probes trained on ROK Ministry of Environment land-cover and
     forest-type maps, applied across the DMZ (same biome and climate, different land management
     -> the border is a management discontinuity but not a climate/DEM discontinuity). Compare AEF
     vs TESSERA gaps to test S4's static-input hypothesis.
  Q5 Validation methodology for data-denied regions: stratified VHR interpretation design with
     design-based area estimates and CIs, plus cross-product agreement (Dynamic World, WorldCover,
     GHSL, Hansen); generalisable beyond DPRK.
- Data: AEF 2017-2025 (DPRK + ROK border provinces); ROK labels in `data/rok/` (EPSG:5186/5179 ->
  reproject to EPSG:4326, rasterize to 10 m, harmonise to 6-8 classes: forest, cropland-paddy,
  cropland-dry/hillside, built-up, grassland/bare, water, wetland). Fallback if `data/rok/` is
  empty: Dynamic World / WorldCover on the ROK side as noisy labels, flagged `LABELS=FALLBACK`.
  Event dates from 38 North / Beyond Parallel / KCNA-reported completions (record source and date
  for each; tag [V]/[U]).
- Stage-2 smoke test: T3 transfer (ROK-trained linear probe -> DPRK VHR-interpreted 300-point
  check set, 5 spatial folds on the ROK side) + T2 change signal at 3 dated project sites vs
  matched undisturbed controls. Report AEF vs S2-composite vs (if available) TESSERA.
- Baselines: S2 annual composite + same classifier; Dynamic World class probabilities; TESSERA
  where coverage exists.
- Threats: no in-situ truth (mitigate with design-based VHR sampling and inter-interpreter
  agreement); label-definition mismatch ROK vs DPRK (paddy/dry field, hillside plots <0.5 ha);
  political sensitivity of interpretation (report as land use only; no facility identification).
- Journals: RSE (validated measurement + campaign assessment), ISPRS JPRS (transfer method),
  fallbacks IJAEOG / GIScience & RS; policy variant Land Use Policy.
- Ethics: civilian land use only; no military-site identification; public data throughout.

Other Tier D seeds:
- D2 Conflict-driven cropland abandonment and recovery across several conflicts (Ukraine front line
  2022-2025, Sudan 2023-, Tigray 2020-22, central Sahel): AEF annual cropland status vs pre-war
  baseline as a function of ACLED event density and front-line distance; validate against
  WorldCereal / national statistics; label-efficiency vs S2-composite baselines.
- D3 Neighbourhood-scale conflict damage density and multi-year reconstruction trajectories
  (Mariupol, Gaza, Khartoum): grid-level damage fraction and recovery from annual embedding
  trajectories, validated against UNOSAT / Copernicus EMS aggregated to the grid. Differentiate
  from building-level EMD+SAR fusion (§4.3).
- D4 Displacement-settlement dynamics: emergence and growth of IDP/refugee sites (Sudan-Chad
  border, eastern DRC, Cox's Bazar) via embedding change plus similarity search seeded from known
  camps; validate with UNHCR / HDX / HOT footprints and dates.
- D5 Environmental footprint of military land use in Korea's border region: training-range fire
  scars and vegetation degradation, DMZ/CCZ wildfire recovery 2017-2025, validated with burned-area
  products, KFS wildfire records and VHR; low sensitivity, high domestic relevance.
- D6 (dual-use, conditional) Coarse GNSS-denied localisation for disaster-response UAVs by matching
  aerial imagery to AEF reference embeddings; methods paper on public cross-view datasets only.
  Keep only if a clear gap vs cross-view geo-localisation literature is confirmed.

## 7. SCORING AND KILL RULES

Score 0-3 each:
N novelty gap | R real-world relevance (named stakeholder/policy hook) | F feasibility (labels
exist, coverage, GEE free tier + laptop, <=3 months) | A AEF-specific scientific advantage
(convenience only -> <=1) | V verifiability (independent reference; falsifiable claim) |
J journal fit (TGRS/RSE plausibility).
Total = N+R+F+A+V+J (max 18). Hard kills: F=0 or V=0; A<=1 and N<=1; RQ already answered
convincingly (§4.3). MUST_EVALUATE topics bypass Stage-1 kills only. Stage 1 uses quick scores,
Stage 2 revises with evidence, Stage 3 finalizes. IDs: `T<bucket><nn>` (e.g., TA01, TH01); keep
seed labels (S1.., D1..) in the title for traceability.

## 8. STAGES

### Stage 1 — Landscape + wide shallow screen (no code)
Step 0 (main agent, <= `stage1_landscape_queries`): search "AlphaEarth", "AlphaEarth
Foundations", "Satellite Embedding dataset", "AEF embeddings" via OpenAlex / Semantic Scholar /
arXiv, restricted to 2025-2026. Write `00_landscape.md` (<=60 lines): verified works [V] beyond
§4.3, one-line gist, bucket(s) each occupies, and the gap list. This is the shared novelty baseline.
Step 1 (8 subagents in parallel, one per bucket A-H): each reads `00_landscape.md` and §4-§7,
produces 4-6 candidate cards (bucket H must include D1), spends <= `stage1_queries_per_subagent`
lookups in total, writes no code. Prior work from memory must be tagged [U]. Writes
`stage1/bucket_<X>.md`; returns <=10 lines.
Card = one table row:
`ID | Title (<=12 words) | Region | RQ (1 sentence) | Why AEF (1 sentence) | Reference data (named) | Closest prior work (title, year, [V]/[U]) | N R F A V J Total | PASS/KILL + reason (<=15 words)`
Main agent: merge into `01_stage1_screen.md` (table sorted by Total; kill list at bottom). Pass
the top ~35-45% (target 10-14) plus MUST_EVALUATE, ensuring >=4 buckets are represented. Chat:
<=15 lines. If AUTOPILOT=false, pause here.

### Stage 2 — Feasibility and smoke tests (one subagent per passed topic)
Per topic, <= `stage2_queries_per_topic` lookups, <= `stage2_gee_checks_per_topic` GEE checks,
<= `stage2_pilot_runs_per_topic` pilot runs:
1. Literature: 3-6 verified key papers; the gap in <=2 sentences; strongest competitor and how
   this topic differs.
2. Data: confirm the reference asset exists, covers region and years, and its label definition
   aligns with AEF annual semantics (§3.5).
3. Smoke test — pick 1-2 templates; each <=80-line script, <=10k samples, <=10 min; baseline
   mandatory; numbers only:
   - T1 Separability: linear probe / kNN on <=5k labeled pixels, 5 spatial folds, AEF vs S2
     composite.
   - T2 Change signal: ROC-AUC of angular change between two years vs binary reference change;
     false-positive rate on stable strata.
   - T3 Transfer: probe trained in region A, tested in region B; accuracy drop vs in-region.
   - T4 Decodability: ridge R^2 predicting a covariate (elevation, precipitation, canopy height).
   - T5 Retrieval: precision@k of dot-product search from <=50 seeds vs known target polygons.
   DESK_ONLY: skip, set `PILOT=PENDING`, score F conservatively.
4. Revise N R F A V J; PASS/KILL with reason; top-3 risks; Reviewer-2 objection; for H topics,
   the ethics line (§3.9).
Write `stage2/<ID>.md` (<=40 lines); return <=10 lines. Main agent -> `02_stage2_feasibility.md`
(table + one paragraph per PASS). Target 5-8 passes.
Stage 1.5 (only if <5 pass): spawn 2 subagents to generate 6 new candidates in the two strongest
buckets, run them through Stage 1 and 2 rules, no user question.

### Stage 3 — Go/No-Go proposals (one subagent per Stage-2 pass, <= `stage3_queries_per_topic`)
One-page proposal (<=60 lines) per topic in `stage3/<ID>.md`:
1. Working title; one-sentence contribution ("We show that ... which matters because ...").
2. 2-3 research questions with falsifiable hypotheses.
3. Real-world problem, stakeholder, and how the result would be used.
4. Data: AEF years, regions/tiles, reference and validation sets (independence argument),
   sampling design.
5. Method: pipeline; mandatory baselines (classical composite + >=1 other GFM or TESSERA where
   relevant); ablations; evaluation protocol (spatial CV; design-based area estimation with CIs
   whenever a map is produced; statistical tests).
6. Expected figures/tables (3-5).
7. Pilot evidence from Stage 2 and implied effect size; sample-size / power note.
8. Threats to validity and mitigations (label mismatch, spatial autocorrelation,
   input-availability artifacts, 10 m / annual limits; for H: ethics and provenance).
9. Compute plan (GEE + local hours) and a 12-week timeline.
10. Target journals: primary / secondary / stretch, each with a one-line fit statement (§10) and
    the preempted Reviewer-2 objection.
11. Verdict: GO / CONDITIONAL-GO (condition stated) / NO-GO.
Main agent -> `03_stage3_proposals.md` (concatenated) and `04_final_ranking.md`: ranked GO list
(>=5), diversity check, recommended first project (best novelty x feasibility), two pivot options
per topic, and a summary of the full kill log. If fewer than 5 GO, promote the best
CONDITIONAL-GO topics with conditions stated; report the shortfall honestly.

## 9. OUTPUT FILES (all under WORKDIR)

`PROMPT.md` | `00_landscape.md` | `stage1/bucket_*.md` | `01_stage1_screen.md` |
`stage2/<ID>.md` | `02_stage2_feasibility.md` | `stage3/<ID>.md` | `03_stage3_proposals.md` |
`04_final_ranking.md` | `data/` (user-provided labels) | `scratch/` (pilot scripts, small CSVs;
never printed). User-facing files follow REPORT_LANGUAGE; keep dataset names, method names, and
paper titles in English. Plain markdown tables; no emoji, no decorative headers.

## 10. JOURNAL TARGETING GUIDE (SCIE only; MDPI excluded)

Decide by primary contribution:
- New method / representation analysis / rigorous multi-region benchmark with methodological
  insight -> IEEE TGRS. Expects strong baselines including other GFMs, ablations, generality
  across regions, and clarity about what is new relative to the GFM literature.
- New environmental or societal measurement with rigorous validation (independent reference
  data, accuracy assessment and area estimation per Olofsson et al. 2014 / Stehman & Foody 2019,
  uncertainty discussion) -> RSE. Rejects "applied model X to region Y" without new science.
- Balanced method + application with strong engineering -> ISPRS Journal of Photogrammetry and
  Remote Sensing.
- Solid but regional or incremental -> IEEE JSTARS; International Journal of Applied Earth
  Observation and Geoinformation; GIScience & Remote Sensing; Science of Remote Sensing;
  International Journal of Remote Sensing.
- One sharp finding (quantization effect, year-effect artifact) -> IEEE GRSL.
- Policy-facing result -> Environmental Research Letters; Communications Earth & Environment;
  Land Use Policy; Global Environmental Change; (stretch) Nature Sustainability / Nature Food.
- Security/humanitarian topics (bucket H) -> same RS venues by contribution type; policy variants
  -> ERL, Nature Food (food security), International Journal of Disaster Risk Reduction, Land Use
  Policy, Political Geography (SSCI). Korean domestic defense journals are not SCIE: not targets.
- Validated map or dataset as the product -> Earth System Science Data; Scientific Data.
- Domain venues -> Global Change Biology; Forest Ecology and Management; Biological Conservation;
  Landscape and Urban Planning; Computers, Environment and Urban Systems; Habitat International.
Do not look up impact factors. Verify SCIE indexing only if unsure (1 query max). Excluded: all
MDPI titles (Remote Sensing, Land, Forests, Sustainability, etc.).

## 11. GEE PILOT SNIPPET (adapt; keep scripts <=80 lines)

```python
import ee; ee.Initialize(project=GEE_PROJECT)
AEF = ee.ImageCollection("GOOGLE/SATELLITE_EMBEDDING/V1/ANNUAL")
def aef_year(y, roi):  # one 64-band image for calendar year y
    return AEF.filterDate(f"{y}-01-01", f"{y+1}-01-01").filterBounds(roi).mosaic()
roi = ee.Geometry.Rectangle([lon0, lat0, lon1, lat1])            # ~50x50 km with known dynamics
e1, e2 = aef_year(2019, roi), aef_year(2023, roi)
dot = e1.multiply(e2).reduce(ee.Reducer.sum()).rename("dot")     # cosine similarity (unit vectors)
angle = dot.clamp(-1, 1).acos().multiply(180 / 3.141592653589793).rename("angle_deg")
stack = e2.addBands(angle).addBands(label_img)                   # label_img: reference raster, same years
samp = stack.sample(region=roi, scale=10, numPixels=5000, seed=1, geometries=True)
rows = samp.getInfo()["features"]                                # keep <= ~5k features per getInfo
# spatial blocks for GroupKFold: block = (floor(lon/0.1), floor(lat/0.1))
# baseline: cloud-masked Sentinel-2 SR annual median (B2-B8, B11, B12, + NDVI), same year, same samples
# D1: label_img from data/rok/ rasterized to 10 m on the ROK side; DPRK check set from VHR points (CSV)
```

Setup check (<=5 min): `pip show earthengine-api scikit-learn pandas rasterio geopandas` (install only
what is missing), then `ee.Initialize` + a 1-pixel AEF sample. On failure, print `earthengine
authenticate` guidance once and continue in DESK_ONLY mode. Check `data/rok/` for D1 labels. Do
not verify checksums, licenses, or versions beyond this.

## 12. EXECUTION PROTOCOL

1. Setup -> Stage 1 (Step 0, Step 1) -> [pause only if AUTOPILOT=false] -> Stage 2 -> [Stage 1.5
   if needed] -> Stage 3 -> final summary.
2. Resume: if WORKDIR already contains stage files, resume from the first incomplete stage; never
   redo completed work.
3. Failures: API 429 -> wait 20 s once, then skip and tag [U]; GEE timeout -> halve the sample
   size once, then `PILOT=PENDING`; never loop.
4. Final chat message <=25 lines: GO list with one-line contribution and primary journal each,
   D1 verdict with its Stage-2 numbers, diversity check, recommended first project, file paths.

Begin now with Setup and Stage 1 Step 0. Do not ask for confirmation.
