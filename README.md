# SugarCode AI

A multi-omic bio-design platform organized as a network of specialized modules on the
**Omega OS v7.0** framework. Built line-by-line from the SugarCode AI spec doc
(`spec/` holds the full per-module spec corpus extracted from the source document).

## Architecture

```
src/omega/            Omega OS v7.0 framework
  registry.py         All 77 modules + 9 sub-networks + lifecycle status
  health.py           Per-module import/self-test health, global compute flux
  search.py           Unified BM25-style biological search over the module corpus
  api.py              FastAPI surface (/modules /subnetworks /health /search)
src/sugarcode/
  bio/                Shared scientific toolkit: sequence ops, FASTA, codon
                      usage/CAI, position weight matrices
  modules/<slug>/     One package per module
tests/                pytest suite - one named test per public behavior
spec/                 The spec doc split into 77 module spec files + index
```

## Sub-networks (9)

The source doc states "nine functional sub-networks" without naming them; these
assignments are derived from module themes:

| Sub-network | Modules |
|---|---|
| core-intelligence | 6 |
| genome-editing | 13 |
| protein-engineering | 5 |
| synthetic-biology | 12 |
| cellular-systems | 11 |
| therapeutics | 13 |
| microbiome-phage | 7 |
| fabrication-evolution | 6 |
| platform | 4 |

## Build status ledger (honest counts)

The spec's own counts are internally inconsistent: the intro says **78** modules,
Neuro-Hub's text says an "**84-node** neural stack". **77 modules are actually
specified** in the document; all 77 are registered and spec-filed. We build and
count against the 77 that exist, not the 78/84 claimed.

Status per module: **verified** = implemented with passing named tests;
**thin** = partial implementation; **specified** = spec captured, implementation pending.
**As of drop 3 every one of the 77 specified modules is verified - zero thin, zero pending.**

| Drop | Verified | Thin | Specified (pending) | Tests |
|---|---|---|---|---|
| 1 | 16 | 0 | 61 | 51 passing |
| 2 | 27 | 0 | 50 | 71 passing |
| 3 (current) | **77 (all)** | 0 | 0 | 160 passing |

### Verified in this drop (real implementations, named tests)

| Module | What is real |
|---|---|
| neuro_hub | dashboard aggregation over live health + unified search + project store |
| gene_explorer | full central dogma: transcription, translation, ORFs, MW, hydrophobicity, animation keyframes |
| crispr_opt | PAM enumeration both strands, GC 40-60% filter, position-weighted on-target score, seed-weighted off-target scan, hairpin check, browser-track payload |
| codon_opt | CAI optimization vs E. coli K12 / H. sapiens tables, GC-window repair, motif avoidance, CHI tRNA-strain index, TASEP ribosome-flow KMC simulation, FBA constraint export |
| prime_design | pegRNA design (PBS 10-17 nt by Tm, RTT 10-20 nt), PE2/PE3 nicking sgRNA finder, outcome distribution, off-target scan |
| deepsplice | donor (9 nt) / acceptor (15 nt) PWM log-odds scoring, variant delta, isoform consequence calls |
| str_scope | tandem-repeat detection 1-6 bp units, expansion classification, diagnostic potential index |
| rna_decoder | DRACH/m6A site prediction with regional priors + exposure proxy, modification map, mRNA optimization proposals |
| promoter_lib | sigma70 promoter scoring (-35/-10/spacer/UP element), strength-targeted design, library generation, motif heatmap |
| dark_genome | TF motif scan (IUPAC), enhancer clustering, CpG islands, lncRNA candidates, hypothesis generation |
| virtual_cell | stoichiometric FBA (scipy linprog/HiGHS), gene knockout lethality + flux rerouting, dynamic FBA growth simulation |
| synbio_studio | Hill-kinetics ODE circuit simulation (solve_ivp), toggle switch bistability, repressilator, truth-table verification |
| living_computer | boolean expression -> circuit compiler with fidelity scoring, parts registry, stochastic noise analysis (CV) |
| omega_stats | metric recording, per-metric aggregates, sub-network rollup |
| ecosystem | SDK snippet generation, plugin manifest contract, machine-readable API reference |
| dna_to_code | 6 biology->Python concept translations with executable analogies |
| gene_analysis | integrated gene profile: ORF/protein stats, regulatory landscape, variant interpretation, CRISPR targets, publication trends |
| crispr_cargo | LNP/AAV/VLP/PNP vehicle ranking per payload+tissue, one-compartment PK model, delivery blueprints with composition specs |
| crispr_muse | policy-gradient gRNA generator with GC/off-target rewards and simulated NGS feedback loop |
| epi_edit | CRISPRa/i guide placement (promoter windows), chromatin accessibility track, histone-mark map, fold-change prediction |
| openclinvar | ACMG-flavored evidence-weighted interpretation (BA1/PM2/PS3/PP1 rules), curated exemplars, patient-friendly reports, VCF parsing |
| genomegpt | k-mer z-score anomalies, TF/CTCF motif scan, convergent-CTCF chromatin loop prediction, motif-disruption variant reading |
| alpha_fold_ui | Chou-Fasman secondary prediction, pLDDT/PAE analogs, idealized C-alpha backbone, real PDB output, pocket candidates |
| docking_studio | SMILES feature parsing (atoms, LogP, RO5), complementarity energy terms (vdW/H-bond/electrostatic/desolvation), Kd estimate, virtual screening |
| evofold_4d | anisotropic network model normal modes (3Nx3N Hessian), hinge detection, open/closed transition traces with RMSD, PTM stiffening perturbation |
| mutdock | class-change ddG + docking rescore per mutation, resistance hotspots, cross-drug resistance forecast |
| protein_painter | intent->fold-template design, propensity-guided sampling with active-site placement, fold verification + stability ranking |
| metabodesigner | pathway gap-filling by BFS over reaction network, yield-first ranking, FBA-verified production flux |
| synthetic_life | essentiality priors by functional category, minimal-genome knockout sets with FBA growth check |
| bio_material | material gene-part catalogs (silk/curli/MCP), pathway-to-material design, property prediction |
| cell_free_opt | CFPS response-surface optimization over lysate/energy/additive space, yield-at-4h prediction |
| stability_ai | Arrhenius shelf-life, deamidation/oxidation site risk, thermal stability forecast per protein |
| syn_stab_ai | formulation search (buffer/excipient/stabilizer grid) maximizing predicted shelf-life |
| bio_switch | ligand-binding domain + effector fusion design, dose-response Hill curves, switching thresholds |
| biofactory_1_a | biofoundry workflow compiler: Golden Gate/assembly step plans, timing, reagent manifests |
| robotic_flow | liquid-class-calibrated pipetting plans, deck layout, error-checked transfer sequences |
| phageforge | phage genome feature map + CRISPR guide retargeting for phage engineering |
| cell_twin | cell-state ODE twin (growth/cycle/stress), perturbation response, state-space trajectories |
| fate_predictor | curated reprogramming factor maps, route scoring, efficiency/risk estimates |
| cellfatenet | lineage GRN attractor simulation, fate probabilities under perturbation |
| organoid_ai | organoid differentiation recipes, growth-factor schedules, maturation scoring |
| bioimage_ai | numpy/scipy image pipeline: segmentation, spot detection, morphology features |
| cellpainter | Cell Painting channel simulation, morphological profile extraction, perturbation fingerprints |
| cellpainter_4d | time-lapse event model (division/death/motility), 4D trajectory rendering data |
| syndroid | patient-cell digital twin: multi-compartment ODE with disease parameters, treatment response |
| tissue_eng | scaffold porosity/mechanics + cell-seeding model, vascularization limit, tissue growth forecast |
| infinite_diagnosis | cross-domain differential: symptom->systems mapping across module knowledge domains |
| car_t_designer | CAR architecture per antigen (scFv/hinge/costim), toxicity priors (CRS/ICANS), safety switches |
| living_tx | engineered-microbe therapeutics: chassis pick, payload circuits, kill-switch containment |
| neohunter | mutation-spanning peptide enumeration, HLA anchor-motif binding score, immunogenicity rank, vaccine payload |
| gene_tx_opt | tissue->vector/promoter matching, transgene capacity enforcement (honest refusal at 9kb), NAb risk |
| vector_opt | capsid variant library (NAb-escape surface mutations), tropism/escape scoring |
| organoid_screen | organoid drug panel with genotype-conditioned response priors, ranking + hit calling |
| neuroplan_ai | tumor segmentation volume, corridor optimization around eloquent regions, risk class + surgical plan |
| neodti_engine | drug-target-pathway-disease graph walk, therapeutic resilience index, disease alias resolution, docking hook |
| liquid_biopsy | error-rate-aware ctDNA calling (beta-binomial floor), denoise, serial-monitoring plan |
| rarenet_ai | phenotype-driven rare-disease matching + variant integration, ranked differentials |
| oncocircuit | two-input AND-gate tumor sensing circuits, promoter logic, payload delivery design |
| pdx_insight | PDX fidelity index (mutation retention, expression concordance, stroma, drift), verdict + CRISPR repair |
| microbiome_exp | 16S alpha diversity (Shannon/Simpson), functional potential, dysbiosis-disease flags |
| microbiome_rx | gLV community ODE with cross-feeding + antibiotic susceptibility kernels, intervention ranking |
| micro_tx | strain-prebiotic pairing per indication, community simulation, engraftment markers |
| microaiverse | cultivation solver: lifestyle classes, auxotrophy supplements, coculture partners, success estimate |
| riboswitch | aptamer + switching-stem design (on/off), stem energetics, dynamic-range prediction |
| phage_tx | phage-pathogen matching, receptor-based resistance routes, escape-suppressing cocktails |
| phage_designer | tail-fiber retargeting (receptor binders, adsorption), chimeric lysin potency incl. gram- strategy |
| chemgpt_engine | fragment assembly, Crippen-style LogP / logS / RO5 / CYP-hERG priors, Pareto front, retrosynthesis steps |
| bioprint_pro | Cross-model rheology, SI-corrected Poiseuille printability window, first-order crosslinking, fidelity |
| bioplayground | Wright-Fisher sandbox: selection/drift/mutation/bottlenecks, construct retention verdicts |
| biosimvr | headless 3D lab scene graph + scripted sessions (CRISPR transfection, docking) with observations/conclusions |
| synlife_evo | multi-generation pathway evolution: expression mutation, burden-vs-yield selection, silencing prediction |
| bio_copilot | mutation->domain->ddG->pathway->phenotype DAG with inconsistency flags, FASTA/PDB writers, query routing |
| synbio_wizard | goal->pathway->chassis->assembly pipeline, Monte-Carlo yield CI, feasibility verdict + experiments |
| neuro_pipeline | numpy MLP training with STDP modulation, virtual lesion study, activation trace, RSA manifold analysis |
| biogpt_lit | evidence-weighted temporal knowledge graph, contradiction detection, multi-hop BFS, hypothesis generation |
| enterprise_bio | tier entitlement engine: module gating, compute quotas, vault/robot access, audit trail |
| nexus_support | inquiry triage/routing to owning sub-network (registry-derived), SLA by tier, KB matching |


### Known limits (named, not hidden)

- External database integrations (PubMed, NCBI, UniProt, ClinVar, AlphaFold) are
  not yet wired; modules that need them use built-in reference data or physics/
  statistics models. Live connectors are a later drop.
- No trained deep models yet (GenomeGPT, DeepSplice-full, BioImage AI etc. need
  learned weights); current versions use PWM/ODE/FBA/heuristic models that are
  real computations, not labels.
- Frontend/UI is API-only in this drop.
- CRISPR on/off-target scores are calibrated heuristics (Doench-style), not the
  published Rule Set 2 / CFD weight matrices.

## Quickstart

```bash
pip install -e .[dev]
python -m pytest -q                 # 160 tests
python - <<'PY'
from omega.search import biological_search
print(biological_search("CRISPR guide design")["results"][0]["name"])
from sugarcode.modules.crispr_opt import design_guides
print(design_guides("ATG" + "CG"*40 + "GG" + "A"*40)["guides"][0])
PY
uvicorn omega.api:app --reload      # API surface
```
