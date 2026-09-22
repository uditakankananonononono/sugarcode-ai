# SugarCode AI

**Current honest status: see [STATUS.md](STATUS.md)** - what is verified, thin, and Missing, updated each push.

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
| 3 | **77 (all)** | 0 | 0 | 160 passing |
| 4 | **77 (all)** + 4 live DB connectors | 0 | 0 | 169 passing |
| 5 | + RCSB PDB & AlphaFold DB structure connector | 0 | 0 | 175 passing |
| 6 | + real-geometry docking & published CFD off-target model | 0 | 0 | 186 passing |
| 7 | + published Doench 2014 on-target in design pipeline, e2e connector workflow | 0 | 0 | 193 passing |
| 8 | + MutDock live UniProt grounding; phageforge inherits CFD | 0 | 0 | 196 passing |
| 9 | + RareNet live ClinVar enrichment; structure resistance scan; streaming FASTA scan | 0 | 0 | 201 passing |
| 10 (current) | + ChEMBL live bioactivity in NeoDTI; PubMed trends; Copilot live grounding | 0 | 0 | 206 passing |

### Verified in this drop (real implementations, named tests)

| Module | What is real |
|---|---|
| neuro_hub | dashboard aggregation over live health + unified search + project store |
| gene_explorer | full central dogma: transcription, translation, ORFs, MW, hydrophobicity, animation keyframes |
| crispr_opt | PAM enumeration both strands, GC 40-60% filter, position-weighted on-target score, seed-weighted off-target scan, hairpin check, browser-track payload |
| codon_opt | CAI optimization vs E. coli K12 / H. sapiens tables, GC-window repair, motif avoidance, CHI tRNA-strain index, TASEP ribosome-flow KMC simulation, FBA constraint export |
| prime_design | pegRNA design (PBS 10-17 nt by Tm, RTT 10-20 nt), PE2/PE3 nicking sgRNA finder, outcome distribution, off-target scan |
| deepsplice | splice PWMs learned from 1,170 real RefSeqGene GT-AG junctions (29 title-verified genes) + U12 minor-spliceosome matrices from 500 human gold introns (intronIC index; AT-AC and GT-AG U12 donors routed, U12 acceptor routing declined - too weak); variant delta + isoform calls + a polypyrimidine-tract term for AG acceptors (learned from the harvest, additive with unscaled matrix contribution) calibrated on a 28-gene ClinVar golden set + U12 family goldens, 2,720 unique pathogenic + 86 benign cases after full (gene, notation) dedupe (100% of ALL 2,430 canonical sites called loss: 2,414 U2 GT/GC-AG and 16 AT-AC across five sodium-channel genes), transcript-isoform junction maps via cDNA-record alignment (SCN1A NM_001165963 native), 5'-UTR intron routing (negative c. numbers, GJB2 c.-23+1G>A, canonical and explicit-transcript maps), exon-skip in-frame/frameshift context + alternative outcomes (intron retention with real intron lengths, cryptic-site-use candidates), cryptic-site activation scan validated on the published CFTR 3849+10kbC>T pseudoexon case |
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
| openclinvar | ACMG-flavored evidence-weighted interpretation (BA1/PM2/PS3/PP1 rules), live ClinVar evidence with official 0-4 star review tiers, gnomAD frequency/constraint, curated exemplars, patient-friendly reports, VCF parsing |
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
| organoid_screen | organoid drug panel, ranking + hit calling; live combo screen: real ChEMBL potency x co-crystal-pocket resistance folds -> effective IC50; per-compound pockets (allosteric drugs scored on their own site); outside-pocket mutations annotated against UniProt binding sites (accession + range, advisory only) |
| neuroplan_ai | tumor segmentation volume, corridor optimization around eloquent regions, risk class + surgical plan |
| neodti_engine | drug-target-pathway-disease graph walk, therapeutic resilience index, disease alias resolution, docking hook |
| liquid_biopsy | error-rate-aware ctDNA calling (beta-binomial floor), denoise, serial-monitoring plan |
| rarenet_ai | phenotype-driven rare-disease matching + unified variant evidence panel (star-tiered ClinVar, gnomAD, splice assessment with U12 GT-AG/AT-AC flags and exon-skip in-frame/out-of-frame context, constraint), ranked differentials |
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

- Live connectors for NCBI Entrez (Gene/PubMed/ClinVar), UniProt, RCSB,
  AlphaFold DB and ChEMBL are wired and live-verified (drops 4-11), with disk
  cache, throttling, retries and explicit offline/failure behavior. Coverage is
  per-module; anything not wired says so in its output instead of fabricating.
- No trained deep models yet (GenomeGPT, DeepSplice-full, BioImage AI etc. need
  learned weights); current versions use PWM/ODE/FBA/heuristic models that are
  real computations, not labels.
- Frontend/UI is API-only in this drop.
- CRISPR **off-target scoring is the published CFD model** (Doench et al. 2016)
  as of drop 6, and **on-target scoring is the published Doench 2014 (Rule Set 1)
  model** as of drop 7 - both vendored verbatim from the CRISPOR distribution
  (`crispr_opt/data/`, PROVENANCE.md included) and cross-validated 500/500
  against the reference implementations. `design_guides` now scores with the
  published models end-to-end; guides at sequence edges (no 30-mer context)
  are labeled `heuristic_edge_fallback`, never silently. Rule Set 2
  (Fusi/Azimuth) is **Missing**: its pickled sklearn model is not portably
  loadable on modern stacks - labeled, not faked.
- Ensembl REST is unreachable from the build environment (HTTP 500 on all
  endpoints, later connection timeout on final retry - treated as unusable);
  OpenClinVar uses live ClinVar + curated exemplars instead.

## Live data (drop 4)

```python
from sugarcode.modules.gene_analysis import live_gene_profile
from sugarcode.modules.openclinvar import live_lookup
from sugarcode.modules.biogpt_lit import KnowledgeGraph, ingest_pubmed
from sugarcode.modules.bio_copilot import live_gene_context

live_gene_profile("TP53")        # NCBI Gene + UniProt, merged, sources named
live_lookup("BRCA1")             # live ClinVar classifications
kg = KnowledgeGraph(); ingest_pubmed(kg, "BRCA1 DNA repair", retmax=5)
live_gene_context("KRAS")        # UniProt grounding, local slice as named fallback
```

Connectors cache to `~/.sugarcode_cache/` and support `offline=True` for
air-gapped/test runs (raises unless cached - no silent fabrication).

### Real structures (drop 5)

```python
from sugarcode.modules.alpha_fold_ui import analyze_real_structure
analyze_real_structure("P04637")   # AlphaFold DB: 393 res, real pLDDT, pockets
analyze_real_structure("1TUP")     # RCSB PDB: experimental coords, resolution
```

`src/sugarcode/bio/structures.py` fetches from RCSB and AlphaFold DB (EBI),
parses C-alpha traces with confidence (pLDDT / B-factors), and finds pockets
from real coordinate density - replacing the Chou-Fasman stand-in for any
protein with a known structure.

### Real-geometry docking & published CFD (drop 6)

```python
from sugarcode.modules.docking_studio import dock_into_structure
from sugarcode.modules.crispr_opt import (design_guides, cfd_score,
                                          score_off_targets_cfd, doench2014_ontarget)

dock_into_structure("1TUP", "c1ccncc1", chain="B")   # real pocket, geometry terms
cfd_score("GAGTCCGAGCAGAAGAAGAA", "GAGTCCGAGCAGAAGAAGCA", "GG")  # Doench 2016
doench2014_ontarget(seq30)                            # Doench 2014 RS1, needs 30-mer
score_off_targets_cfd(guide20, genome_background)     # genome scan, PAM-aware
design_guides(locus, background=genome)               # published models end-to-end
```

An end-to-end connector workflow (gene grounding -> structure -> pocket ->
dock -> provenance-labeled report) is covered by `tests/test_e2e_connectors.py`.

### Mutation effects on live proteins (drop 8)

```python
from sugarcode.modules.mutdock import live_mutation_context
live_mutation_context("TP53", 273, "H", "c1ccncc1")
```

Pulls the reviewed UniProt record live, extracts the real sequence window and
feature annotations at the mutated position (domains, binding/active sites),
runs the ddG/resistance model on real context, and says when a change hits
annotated functional real estate. 1-based residue numbering is preserved
exactly (R273H stays R273H). PhageForge's guide design inherits the published
CFD off-target scan automatically through CRISPR Opt's design_guides.

### Clinical enrichment, structural resistance, genome files (drop 9)

```python
from sugarcode.modules.rarenet_ai import enrich_variants_live
from sugarcode.modules.mutdock import structure_resistance_scan
from sugarcode.modules.crispr_opt import score_off_targets_cfd_fasta

enrich_variants_live([{"gene": "BRCA1", "hgvs": "NM_007294.4:c.68_69del"}])
structure_resistance_scan("1TUP", {"imatinib": "...", "erlotinib": "..."}, chain="B")
score_off_targets_cfd_fasta(guide20, "chr7.fa")   # streaming, constant memory
```

RareNet attaches live ClinVar classifications to patient variants (exact-match
when the notation matches, honest VUS call otherwise). MutDock runs its full
all-positions x 20-AA x drugs resistance scan on real structure pockets with
true residue numbering. The CFD scan now reads FASTA files via a streaming
parser (`bio.fasta.stream_fasta`) - real reference files, constant memory.

### T315I golden, true numbering, HETATM filter, unified gnomAD (drop 21)

The T315I golden regression exposed two real bugs, both fixed and locked:
resistance scans labeled positions with contiguous numbering, wrong for
non-contiguous co-crystal linings (position 315 was printed as 262), and an
unspecified chain pulled both 1IEP copies into one pocket (46 -> 23 residues).
With true resnum labels and ligand-chain default: **T315I = ddG +0.468, 2.2x
affinity loss - direction and identity correct, magnitude honestly far below
the ~100x clinical resistance (feature-model limit, stated)**. HETATM parsing
now filters crystallization additives (GOL/SO4/PEG/...) and <8-atom groups.
OpenClinvar's interpret_variant_live now also weighs gnomAD population
frequency (common AF = benign evidence, absent = weak support), unifying the
two interpretation stacks; live on P72R both evidence lines agree.

### Co-crystal pockets, feature awareness, joint case view (drop 20)

```python
from sugarcode.modules.mutdock import structure_resistance_scan
from sugarcode.modules.infinite_diagnosis.core import joint_case_view

structure_resistance_scan("1IEP", {"imatinib": "..."}, ligand_resname="STI")
joint_case_view(["intellectual disability", "seizures", "musty odor"],
                [{"gene": "PAH", "hgvs": "c.1A>G", "variant_id": "12-1-A-G"}])
```

MutDock can now run resistance scans on the **experimentally observed binding
site**: HETATM co-crystal ligands from real PDBs define the pocket. Live on
1IEP: the imatinib pocket (46 residues within 6 A) contains T315 and Y253 -
the actual documented imatinib-resistance sites. MutDock also flags lining
residues with annotated natural variants (TP53: 110 annotated, caveat
stated). Infinite Diagnosis crosses the symptom differential with the live
variant panel on structured gene membership: PKU-shaped symptoms + a
strong-support PAH variant = lead hypothesis, plainly labeled. Honest catches
this drop: a symptom normalization bug (spaces vs underscores made
user-entered symptoms silently never match), and my joint view reading a
nonexistent "differential" key (always-empty) - both caught by live runs and
locked with tests.

### RareNet combined evidence panel (drop 19 - diagnostic-workflow capstone)

```python
from sugarcode.modules.rarenet_ai.core import variant_evidence_panel

variant_evidence_panel([
    {"gene": "TP53", "hgvs": "p.Arg273His", "variant_id": "17-7674221-C-T"},
    {"gene": "TP53", "hgvs": "p.Pro72Arg", "variant_id": "17-7676154-G-C"},
])
```

One panel per patient variant: live ClinVar classification (exact phrase
query + title verification - rarenet now uses the same discipline as
openclinvar after a live run exposed gene-page scans missing first-page-past
variants), gnomAD frequency/rarity, and gene constraint, combined into a
support score with every component named and weighted in the open. Live-
verified: TP53 R273H -> strong support (2.5: ClinVar Pathogenic + absent from
gnomAD), P72R -> evidence against (-3.5: Benign + AF 0.716), SCN1A frameshift
-> moderate via LOEUF 0.107. Explicitly not a diagnosis - clinician
adjudicates; the disclaimer is in the output itself.

### gnomAD constraint, specificity checks, pocket validation (drop 18)

```python
from sugarcode.bio import gnomad
from sugarcode.modules.openclinvar import interpret_variant_live

gnomad.gene_constraint("SCN1A")                 # pLI 1.0, LOEUF 0.107 - constrained
interpret_variant_live("SCN1A", "c.100dup", consequence="frameshift")
```

OpenClinVar now weighs **gnomAD gene constraint** for LOF consequences - and
says no honestly: TP53 (LOEUF 0.418) adds zero support, SCN1A (0.107) adds
real support, missense consequences get no constraint evidence at all.
NeoHunter takes an optional GRCh38 variant_id and runs a gnomAD population
frequency check as a second tumor-specificity test. MutDock validates its
geometry pockets against UniProt-annotated BINDING features, with plain
verdicts when they do not overlap (may be allosteric/unannotated - or a false
positive; the user sees the doubt).

### ClinVar priors, mutdock Vina baseline, live gnomAD frequencies (drop 16)

```python
from sugarcode.modules.rarenet_ai.core import enrich_variants_live
from sugarcode.bio import gnomad

gnomad.variant_frequency("17-7676154-G-C")   # TP53 P72R: AF 0.716 live
enrich_variants_live([{"gene": "TP53", "variant_id": "17-7674221-C-T"}])
```

New connector: **gnomAD GraphQL** (verified reachable and correct: TP53 P72R
returns exome AF 0.716, matching the known common polymorphism; R273H returns
absent - a REAL answer, zero observed carriers, stated explicitly and distinct
from lookup failure). RareNet enrichment now attaches population frequency
with a rarity interpretation (AF > 1% = too common for a rare-disease cause).
NeoHunter attaches live ClinVar germline priors with the tumor-specificity
caveat a neoantigen call needs (R273H: Pathogenic, expert panel - germline,
present in normal tissue, caveat stated). MutDock's structure resistance scan
adds a Vina-form WT affinity baseline on the real pocket CA coordinates per
drug - labeled honestly: mutants are NOT re-docked, ddG still comes from the
feature scorer.

### NeoHunter on live UniProt with variant priors (drop 15)

```python
from sugarcode.modules.neohunter import find_neoantigens_live

find_neoantigens_live("TP53", 273, "H")   # real P04637 sequence + priors
```

Neoantigen scans now run on the **live UniProt sequence**: the WT residue is
validated against the real record (wrong numbering refuses loudly), the
mutation is applied, and published Natural variant / Mutagenesis features at
that position attach as priors. Live-verified on TP53 R273H: 9 published
variant annotations at codon 273 (Li-Fraumeni, sporadic cancers), nine
mutation-spanning 9-mers scored, top candidate NSFEVHVCA (strong binder,
A*02:01). Out-of-range positions and lookup failures raise - never fabricate.

### Vina-form scoring + real SASA interfaces (drop 14)

```python
from sugarcode.modules.docking_studio.vina import dock_vina_structure
from sugarcode.bio.structures import interface_area

dock_vina_structure("1TUP", "CC(=O)Oc1ccccc1C(=O)O", chain="B")  # Vina form, real pocket
interface_area("1TUP", "B", "C")                                  # buried surface area
```

Docking Studio gains a **Vina-form empirical scoring function**: the five
Trott & Olson 2010 terms (gauss1/gauss2/repulsion/hydrophobic/hbond, published
weights) evaluated pairwise over real pocket coordinates with a translation
grid, torsion penalty counted from rotatable bonds. Term ramps verified
against the published functional forms (hbond ramp, hydrophobic ramp - two
sign bugs caught by hand-check before shipping). Honest limits in every
result: rigid linear ligand embedding (no conformer generator available), no
torsional sampling. Structures connector gains **Shrake-Rupley SASA** (1973,
fibonacci sphere, spatial-hashed for real PDB sizes; analytic checks: isolated
carbon = 120.76 A^2, contact burial, non-interaction at 20 A) and
**interface_area** (BSA = (SA+SB-SAB)/2) on live RCSB complexes - 1TUP B-C
interface measured at 347 A^2 from real coordinates.

### A* surgical pathfinding, TASEP dwell times, cfDNA fragmentomics (drop 13)

```python
from sugarcode.modules.neuroplan_ai.core import plan_path_astar
from sugarcode.modules.liquid_biopsy import fragment_length_model
from sugarcode.modules.codon_opt.core import tasep_simulate

plan_path_astar({"center": [32,32,20]}, entry=[5,5,63])   # real A* over risk field
fragment_length_model(0.2)                                # cfDNA entropy + KL classifier
```

NeuroPlan now runs **real A\* pathfinding** on a 26-connected voxel grid over
an eloquent-region risk field (cost = distance x (1 + lambda*risk)), returning
the actual path and comparing its risk integral against the straight-line
corridor (obstructed off-axis entry: 33% risk reduction live-verified; clear
lines are tracked, not detoured, with sampling noise named). Building it
surfaced two real bugs now fixed and tested: region placement spilled outside
the image grid (clamped), and a TASEP KMC off-by-one (rate index vs lattice
index) that crashed whenever the terminal-site hop was drawn. TASEP now also
exposes per-codon dwell times derived from the vendored published usage table,
labeled as the tRNA-abundance approximation (Dana & Tuller 2014) - empirical
Ribo-seq-calibrated rates are **Missing** (no verifiable machine-readable
source found; said so in the output). Liquid Biopsy adds a cfDNA
fragment-length model anchored to published peaks (healthy ~166 bp, ctDNA
134-144 bp; Snyder 2016, Underhill 2016): Shannon entropy, short-fragment
fraction and KL divergence all rise monotonically with tumor fraction
(live-checked 0/5/20%); labeled as a literature-anchored model, not fitted
patient data.

### Published codon tables with provenance, honest GC-repair cost (drop 12)

```python
from sugarcode.bio import codon
from sugarcode.modules.codon_opt import optimize

codon.HOST_TABLES            # + ecoli/human/yeast published + legacy fallbacks
optimize(protein, host="s_cerevisiae")   # real S. cerevisiae usage table
```

Codon usage tables are now **published data with provenance** instead of
memory-built "Kazusa-style" numbers: Edinburgh Genome Foundry
`codon-usage-tables` (E. coli K12, H. sapiens, S. cerevisiae) vendored verbatim
with `bio/data/codon_tables/PROVENANCE.md` and cross-validated against the
previous in-memory tables (E. coli top codons 21/21; human 20/21 with an exact
AGA/AGG tie that memory broke the other way - documented, immaterial).
Published tables are the canonical defaults; memory tables remain as named
`*_legacy` fallbacks. Testing surfaced a real behavior worth surfacing:
Codon Opt's GC-window repair can trade CAI for GC-band compliance (yeast
default-band run dropped CAI 0.96 -> 0.69); `optimize()` now reports
`cai_gc_repair_cost` and a note instead of silently returning the worse
sequence.

### Live variant evidence, real-structure dynamics, molecule novelty (drop 11)

```python
from sugarcode.modules.openclinvar import interpret_variant_live
from sugarcode.modules.evofold_4d import structure_dynamics
from sugarcode.modules.chemgpt_engine import similarity_check

interpret_variant_live("BRCA1", "c.5266dup", consequence="frameshift")
structure_dynamics("1TUP", chain="B")        # ANM modes on real 2.2 A coordinates
similarity_check("CC(=O)Oc1ccccc1C(=O)O")    # -> ASPIRIN, 100%, phase 4
```

OpenClinVar now adds live ClinVar evidence to its ACMG-style weighing: a
targeted phrase query, title-verified against the requested notation (ClinVar's
phrase search returns near-misses - caught live when c.5266dup initially
matched c.5484dup), with honest sign handling (conflicting/uncertain = weight
0, not positive). EvoFold 4D runs ANM normal modes on real RCSB coordinates
and validates fluctuations against experimental B-factors (1TUP chain B:
Pearson r = 0.05, honestly reported as weak agreement). ChemGPT designs are
checked against live ChEMBL server-side Tanimoto similarity - live-verified:
aspirin matches itself at 100% with approved neighbors; an invented molecule
correctly reports novel scaffold space. Failures raise/report, never fabricate.
Ensembl REST remains unreachable from this network (final retry failed); the
Ensembl-dependent route stays labeled Missing.

### Real bioactivity, literature trends, grounded copilot (drop 10)

```python
from sugarcode.modules.neodti_engine import repurposing_scan_live
from sugarcode.modules.gene_analysis import live_publication_trend

repurposing_scan_live("breast cancer")   # graph walk + ChEMBL measured potency
live_publication_trend("BRCA1")          # per-year PubMed counts, trend call
```

NeoDTI candidates are now validated against **live ChEMBL bioactivity**: a
curated, exact-name-resolved target map (13 of 14 graph targets; FROUNT has no
ChEMBL target - honestly absent), drug aliases documented (rapamycin queried as
its INN sirolimus, statins via simvastatin). Live-verified: sirolimus IC50
0.1 nM on mTOR, simvastatin Ki 2.6 nM on HMGCR, aspirin IC50 62.5 uM on COX2.
Bio-Copilot's gene route now grounds answers in live UniProt and names the
fallback when offline; unit tests stay hermetic.

Docking now scores against real structure pockets (enclosure bonus, size-fit
penalty, true lining residues) sourced live from RCSB/AlphaFold DB - still a
screening proxy, not a free energy (named in every result).

## Quickstart

```bash
pip install -e .[dev]
python -m pytest -q                 # 439 tests
python - <<'PY'
from omega.search import biological_search
print(biological_search("CRISPR guide design")["results"][0]["name"])
from sugarcode.modules.crispr_opt import design_guides
print(design_guides("ATG" + "CG"*40 + "GG" + "A"*40)["guides"][0])
PY
uvicorn omega.api:app --reload      # API surface
```
