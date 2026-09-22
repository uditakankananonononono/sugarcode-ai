# SugarCode AI - honest status (as of drop 31 / this push)

This document is the current truth ledger. It says what is verified against
real external data, what runs on real published algorithms, what is a
spec-level heuristic, and what is Missing. If a claim here conflicts with a
module's behavior, the module is right and this doc is stale - say so.

Test suite: **385 passed, 0 failed** (hermetic fixtures; live calls verified
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
| deepsplice real splice PWMs | Donor/acceptor PWMs learned from 1,170 real GT-AG junctions parsed out of 29 title-verified RefSeqGene records; learned consensus AAG|GTAAGT and (T)nCAG|G matches the published mammalian consensus. Vendored with PROVENANCE (accessions, method, GC-donor and AT-AC counts). Catch: first harvest silently used six wrong-locus records (BRCA2's query returns ZAR1L first); title verification fixed all six, goldens re-verified | NCBI RefSeqGene |
| deepsplice BRCA1 golden | ClinVar golden: 186 pathogenic + 20 benign NM_007294 splice SNVs mapped onto NG_005905.2 junction windows. All 150 canonical +/-1/+/-2 pathogenic variants called loss; calibrated thresholds (sens 0.81 / spec 0.95 at -0.15, fit stated as calibration, not independent validation). Known limits kept visible: deeper intronic pathogenic variants act via cryptic sites a fixed-window PWM cannot see; c.594-2A>C (ENIGMA-benign at conserved -2) is a documented false positive, locked in a regression test | NCBI ClinVar + RefSeqGene |
| deepsplice cryptic-site activation | cryptic_scan compares ref/alt context with both real PWMs. Literature golden: CFTR c.3718-2477C>T (3849+10kbC>T) detected as a NEW donor 0.68->0.92 (the published pseudoexon mechanism), vendored fixture. Honest negative result: weak site-strength perturbations fire in BOTH classes of the BRCA1 k>=3 golden (83% pathogenic vs 84% benign) - the verdict labels them candidate-generating, NOT evidence; only new sites crossing 0.75 carry the high-precision claim (0 FP in 55) | NCBI RefSeqGene + ClinVar |
| organoid_screen allosteric pockets | per-compound co-crystal pocket overrides + resnum_offset for construct numbering. Live: asciminib scored on 5MO4:AY7 (myristoyl site, verified via RCSB chemcomp) is untouched by T315I (fold 1.0) and now ranks above imatinib against the gatekeeper mutant - the clinically correct order. Numbering catch: 5MO4 is 1a-numbered AND already carries the T334I gatekeeper mutation; offset +19 verified against the sequence, wt checks fail loudly on wrong offsets | ChEMBL + RCSB PDB (2 structures) |
| deepsplice multi-gene golden | 28 genes: pooled 2,700 pathogenic + 86 benign ClinVar splice SNVs on title-verified junction maps. ALL 2,413 canonical +/-1/+/-2 sites called loss (100%): 2,405 U2 (GT/GC-AG) + 8 AT-AC scored with the U12 matrices; benign specificity 85/86 (99%, the one FP is the documented BRCA1 c.594-2A>C). Drop 29 added CHEK2, PALB2, MUTYH, F8, DMD, MYH7, PKD1, TSC1, TSC2, HBB, VHL - per-gene canonical capture 100% each (DMD 187/187, TSC2 153/153). ClinVar-cited transcripts diagnosed from live titles; for the 10 in-record transcripts a paired-CDS probe verified the cited CDS exactly equals the record's canonical CDS. MUTYH cites NM_001048174 (absent from NG_008189.1) - map built via cdna_junction_map (NM_001048174.2 CDS aligned to the record). GJB2 deliberately excluded: single-exon CDS (intronless coding), its splice variants are 5'-UTR (c.-23+1G>A), outside the CDS-junction harness. Overall sensitivity is lower than canonical capture (e.g. HBB 68%, deep-window and cryptic cases) - reported per gene in fixtures | NCBI ClinVar + RefSeqGene x28 |
| deepsplice GC-donor matrix | GC-AG donors (~0.6% of junctions) scored with the documented swapped +2 matrix (cross-checked: observed GC windows 0.83-1.00 vs 0.36-0.61 under GT). BRCA2 c.7976+2C>G/A now called loss. Catch: first version scored the ALT window on its own class, making GT->GC conversions look tolerated - the multi-gene golden caught +2T>C pathogenic variants dropping out (canonical capture fell 151->142); ref-class matrix discipline restored and regression-locked | RefSeqGene + ClinVar golden |
| deepsplice AT-AC site-class detection + U12 matrices | Extended golden caught 8 pathogenic canonical variants at two SCN1A AT-AC (U12 minor-spliceosome) introns silently scoring delta=0 'minimal effect' - or +0.25 'strengthened' - under the GT-AG matrix (drop 26: named not-applicable). Drop 27 RESOLVES it: U12 donor/acceptor matrices learned from 361 GT-AG + 139 AT-AC human gold minor introns (Larue & Roy 2023 intronIC training index, verifiable machine-readable source, PROVENANCE; consensuses match literature RTATCCTTT / (T)nCCTTRCAC). All 8 pathogenic AT-AC variants now called loss (delta -0.158/-0.205) with a u12_atac flag; non-canonical classes still refuse to score. Caveat: the export has no downstream exon flank, so acceptor column 14 is a uniform placeholder (labeled). Legacy consensus-seed acceptor windows predate the harvest convention; fallback-only | intronIC/FigShare + SCN1A golden |
| deepsplice exon-skip context | Natural-site loss calls now carry real exon context from the junction map (CDS spans): skipped-exon length and in-frame vs frameshift consequence, explicitly conditional ('if skipping occurs'). Live: BRCA1 c.212+1G>A -> 78-nt in-frame exon (matches the published in-frame exon 5 skipping debate); MLH1 c.790+1G>A -> 113-nt out-of-frame (LoF) | RefSeqGene CDS spans |
| organoid_screen UniProt binding annotation | Mutations OUTSIDE the co-crystal lining now checked against UniProt binding/active-site features (bio/uniprot.binding_sites): overlap or +/-3-aa adjacency adds a binding_annotation with accession and range (never re-scores; the drop-22 5MO4 lesson generalized). Live ABL1: E255K/G250E outside the 1IEP lining flagged against the 248-256 ATP-binding annotation (P00519, numbering verified - gatekeeper T315 precedes annotated 316-322); M351T clean negative. UniProt failure degrades to 'annotation unavailable', never fabricated | UniProt P00519 + RCSB 1IEP |
| deepsplice transcript-isoform junction maps | bio/splice.cdna_junction_map: aligns a transcript's cDNA-record CDS to the RefSeqGene genomic sequence by exact-match segmentation with splice-consensus boundary refinement (extension overshoots snap to canonical GT/GC/AT+AG/AC termini), dinucleotide sanity, annotated-boundary cross-check that CLASSIFIES alternative splice events instead of failing. SCN1A proof: NM_001165963 CDS aligns to NG_011906.1 at coverage 1.0; all 25 shared junctions reproduced exactly, downstream junctions native at ClinVar's own coordinates. MECHANISM CORRECTION to drop 26: the +33 shift is an alternative 3' DONOR extending exon 11 by 33 nt (both donors are real GT sites on the genomic sequence), not a cassette exon. 106/107 ClinVar rows now map natively (was 97 with the hand remap) | NCBI NM_001165963.2 + NG_011906.1 |
| deepsplice U12 GT-AG donor routing | U12 GT-AG donors (RTATCCTTT consensus, minor spliceosome) are now distinguished from U2 GT-AG donors by matrix score margin 0.15 and scored with the learned U12 GT-AG matrix (361 gold introns). Calibration on the vendored sets, regression-locked: 99.2% recall / 0.09% FPR. Zero golden cases flip (the 17 golden genes' variants are all U2). The one U2-harvest junction the margin flags is PTEN c.79 (CCTGTATCC, RTATCCT signature) - reported as a candidate, no ClinVar variants there. Acceptor-side U12 discrimination is too weak (41% recall at 6.4% FPR) and is intentionally NOT routed: AG acceptors keep the U2 matrix, documented | intronIC gold set + U2 harvest (both vendored, hermetic calibration test) |
| deepsplice U12 GT-AG golden | First ClinVar-backed exercise of the drop-28 U12 GT-AG routing: PTEN intron 1 is confirmed U12 by the intronIC gold set (HomSap-gene-PTEN@rna-NM_001304717.5_2(9); donor window CCTGTATCC matches the harvest row). Both likely-pathogenic +1 donor variants (c.79+1G>A, c.79+1G>C) called loss with donor_subtype U12 GT-AG (delta -0.152); the three pathogenic acceptor variants (c.80-1G>A/C, c.80-2A>C) called loss on the U2 matrix (U12 acceptor routing declined). No benign cases fit the +/-6 window (benign c.79+7A>G sits at +7) - recorded honestly | ClinVar live + NG_007466.2 + intronIC gold set (hermetic test) |
| rarenet panel U12/exon-context display | rarenet's variant_evidence_panel now carries the full splice assessment through: site_class, donor_subtype (U12 GT-AG), u12_atac + u12_note, and exon_context (skipped-exon length, in-frame vs out-of-frame). Readable score components annotate too: "predicted loss of natural donor site [U12 GT-AG] (delta -0.15, RefSeqGene map; exon-skip context: 108 nt in-frame) (+1.5)". Plain U2 sites show no annotations. Scoring weights unchanged | hermetic tests (mocked live_splice_assessment, drop-27 pattern) |
| openclinvar splice evidence | interpret_variant_live now carries splice evidence like the rarenet panel (stack unification): natural-site loss +0.4, weakened +0.1, new cryptic +0.3, weak perturbations and AT-AC/other-class notes add ZERO with the reason stated. Live: BRCA1 c.212+1G>A SPLICE_PWM_LOSS +0.4 next to CLINVAR_LIVE 3-star 0.8; CFTR c.3718-2477C>T SPLICE_CRYPTIC_NEW +0.3; SCN1A c.383+1A>G now scores U12 loss; BRCA1 c.594-2A>C (documented benign FP) still visible as +0.4 with its honest golden context | RefSeqGene + ClinVar + gnomAD |
| rarenet_ai splice + star panel | variant_evidence_panel now carries splice evidence (natural-site delta on the gene's real RefSeqGene map via live_splice_assessment; deep-intronic -> cryptic_scan; weak perturbations add ZERO by validation) and star-tiered ClinVar weights (4-star 2.5 / 3-star 2.0 / 2-star 1.5 / 1-star 0.75 / 0-star 0.38). Live: BRCA1 c.212+1G>A 3.5 strong (3-star +2.0, splice loss +1.5); CFTR c.3718-2477C>T 3.5 strong (4-star practice guideline +2.5, new cryptic donor +1.0) | ClinVar + RefSeqGene + gnomAD |
| openclinvar star tiers | Official ClinVar 0-4 review-status tiers now weight the live evidence (4 guideline 1.0 / 3 expert panel 0.8 / 2 multi-submitter 0.6 / 1 single or conflicting 0.3 / 0 none 0.15); live: c.212+1G>A +0.8 (3-star), c.213-1G>T +0.3 (1-star), c.594-2A>C -0.8 (3-star benign) | NCBI ClinVar |
| organoid_screen live combo | screen_with_structure: WT potency = real ChEMBL IC50/Ki/Kd per compound vs resolved target, resistance = co-crystal pocket (RCSB) + mutdock ddG for mutations in the lining; effective IC50 = potency x affinity-loss folds. Live ABL1 panel (imatinib/nilotinib/dasatinib/asciminib, 1IEP pocket, T315I+Y253F): real potencies 0.1-1.1 nM, folds 3.4-16.7 applied. Honest limit stated: pocket is the co-crystal ligand's ATP site - applying it to the allosteric asciminib ranks it last here while clinically it is the T315I-active drug; the caveat field says so | ChEMBL + RCSB PDB |
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
- protein_painter, alpha_fold_ui: PWM log-odds / Chou-Fasman-style
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
- U12 AT-AC acceptor column 14 (first exonic base): the intronIC export has no
  downstream exon flank, so that column is a uniform placeholder (labeled in
  PROVENANCE); the 14 intronic positions are real learned data (drop 27).
- Genome-wide / SpliceAI-scale splice models: our PWMs are real but window-local;
  deep long-range splice predictors are not available as verifiable free artifacts.
- Learned weights generally (GenomeGPT, BioImage AI):
  unavailable as verifiable free artifacts; statistical substitutes are named
  per module.

## Live data sources in use

NCBI Entrez (Gene, PubMed, ClinVar) - UniProt REST - RCSB PDB - AlphaFold DB -
ChEMBL REST (+ similarity endpoint) - gnomAD r4 GraphQL - Edinburgh Genome
Foundry codon-usage-tables - CRISPOR/Doench published scoring matrices.
All connectors: disk cache, throttle, retries, explicit offline mode, failures
reported not fabricated.
