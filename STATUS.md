# SugarCode AI - honest status (as of drop 21 / this push)

This document is the current truth ledger. It says what is verified against
real external data, what runs on real published algorithms, what is a
spec-level heuristic, and what is Missing. If a claim here conflicts with a
module's behavior, the module is right and this doc is stale - say so.

Test suite: **283 passed, 0 failed** (hermetic fixtures; live calls verified
outside pytest and recorded below).

## Tier 1 - verified against live external data

| Module | What is verified | Source (live this project) |
|---|---|---|
| crispr_opt | Off-target = published CFD (Doench 2016), on-target = Doench 2014 Rule Set 1; both vendored verbatim, cross-validated 500/500 vs CRISPOR reference | CRISPOR distribution (maximilianh/crisporWebsite) |
| crispr_cargo, phageforge | CFD scan inherited from crispr_opt for real guides | same provenance |
| openclinvar | Live ClinVar exact-variant evidence; near-miss titles rejected; conflicting classifications weight 0. BRCA1 c.5266dup -> Pathogenic, expert panel. Plus gnomAD gene constraint (pLI/LOEUF): supports LOF evidence only in truly constrained genes (SCN1A LOEUF 0.107 yes, TP53 0.418 honestly no) | NCBI ClinVar, gnomAD r4 |
| neohunter specificity | gnomAD population frequency as second tumor-specificity check (when a GRCh38 variant_id is supplied; skipped honestly otherwise) | gnomAD r4 |
| rarenet_ai panel | Combined per-variant evidence panel (ClinVar + gnomAD frequency + gene constraint) with named components and weights, ranked, clinician-adjudicates disclaimer. Live-verified: R273H strong support (2.5), P72R evidence against (-3.5) | NCBI ClinVar, gnomAD r4 |
| mutdock T315I golden | Live golden: 1IEP T315 correctly labeled (true non-contiguous numbering, single-chain), T315I ddG +0.468 / 2.2x affinity loss - direction and identity right, magnitude honestly low vs the ~100x clinical resistance (feature-model limit, stated). Numbering and two-chain dedupe bugs caught by the golden run | RCSB PDB |
| openclinvar unified gnomAD | population frequency now evidence in interpret_variant_live too (common AF -0.8, absent +0.2), mirroring the rarenet panel | gnomAD r4 |
| mutdock co-crystal pockets | Resistance scans on the experimentally observed binding site from real PDB HETATM ligands: 1IEP/imatinib pocket (46 residues) contains the gatekeeper T315 and Y253 - the actual known resistance sites | RCSB PDB co-structures |
| infinite_diagnosis joint view | symptom differential x live variant panel crossed on structured gene membership; live: PKU symptoms + PAH variant -> lead hypothesis | rarenet + ClinVar + gnomAD |
| mutdock pocket validation | geometry pockets compared against UniProt-annotated BINDING features; non-overlap verdicts stated plainly (P04637: annotated sites are DNA-binding, geometry pocket flagged honestly) | UniProt, AlphaFold DB |
| rarenet_ai | Live ClinVar gene context + gnomAD population frequency. P72R AF 0.716 (common, ruled out); R273H absent (ultra-rare, stated) | NCBI ClinVar, gnomAD r4 GraphQL |
| neohunter | Real UniProt sequence + WT-residue validation + published variant priors + live ClinVar germline caveat. TP53 R273H: 9 priors, top 9-mer NSFEVHVCA | UniProt, NCBI ClinVar |
| mutdock | Real structure pockets (true residue numbering), Vina-form WT baseline per drug. 1TUP chain B live | RCSB PDB, AlphaFold DB |
| docking_studio | Vina-form scoring (Trott & Olson 2010 terms/weights, hand-verified ramps) on real coordinates | RCSB PDB |
| organoid_screen | Drug pockets on real structures | RCSB PDB, AlphaFold DB |
| evofold_4d | ANM normal modes on real coordinates, validated vs experimental B-factors (1TUP: r=0.05, honestly "weak") | RCSB PDB, AlphaFold DB |
| neodti_engine | Live ChEMBL measured potency: sirolimus IC50 0.1 nM/mTOR, simvastatin Ki 2.6 nM/HMGCR, aspirin IC50 62.5 uM/COX2 | ChEMBL REST |
| gene_analysis | Live PubMed yearly literature counts + trend call | NCBI PubMed |
| bio_copilot | Gene route grounded in live UniProt, sources named | UniProt |
| chemgpt_engine | Live ChEMBL similarity: aspirin 100% self-match (phase 4); novel molecules correctly report no neighbors | ChEMBL similarity endpoint |
| codon_opt | Published codon tables (E. coli, human, yeast) vendored with PROVENANCE.md; cross-validated vs legacy (Arg tie documented) | Edinburgh Genome Foundry codon-usage-tables |
| liquid_biopsy | cfDNA fragment model anchored to published peaks (166 bp healthy / 134-144 bp ctDNA; Snyder 2016, Underhill 2016); monotone in tumor fraction | literature anchors (labeled) |
| neuroplan_ai | A* over eloquent-region risk field; 33% risk reduction on obstructed entries live-verified | internal verification |

## Tier 2 - real published algorithms (not learned weights)

- virtual_cell: flux balance analysis via HiGHS linear programming
- deepsplice, protein_painter, alpha_fold_ui: PWM log-odds / Chou-Fasman-style
  statistical propensities (real computations, not trained models)
- codon_opt: TASEP stochastic simulation (Gillespie KMC) + CAI (Sharp & Li 1987)
- living_computer, synbio_wizard: stochastic kinetics (Gillespie)
- gene_analysis: Hill-kinetics ODE models
- evofold_4d: anisotropic network model normal modes

## Tier 3 - spec-level heuristic engines

The remaining ~55 modules implement deterministic, documented heuristic
engines per their specs (rule systems, scoring functions, simulations with
named constants). They compute real outputs from real inputs, but their
calibration is ours, not fitted to published data. Each module's docstring
states its method; none of them pretends to be a trained model. Deepening
continues drop by drop in order of scientific usefulness.

## Missing (labeled, not faked)

- CRISPR on-target Rule Set 2 (Fusi/Azimuth): pickled sklearn model not
  portably loadable on modern stacks - crispr_opt says Missing.
- Ribo-seq-calibrated codon dwell times: no verifiable machine-readable source
  found; TASEP dwells are the tRNA-abundance approximation, labeled as such.
- Ensembl REST: unreachable from the build environment (HTTP 500, then
  connection timeouts on retries). Ensembl-dependent routes stay Missing.
- Learned weights generally (GenomeGPT, DeepSplice-full, BioImage AI):
  unavailable as verifiable free artifacts; statistical substitutes are named
  per module.

## Live data sources in use

NCBI Entrez (Gene, PubMed, ClinVar) - UniProt REST - RCSB PDB - AlphaFold DB -
ChEMBL REST (+ similarity endpoint) - gnomAD r4 GraphQL - Edinburgh Genome
Foundry codon-usage-tables - CRISPOR/Doench published scoring matrices.
All connectors: disk cache, throttle, retries, explicit offline mode, failures
reported not fabricated.
