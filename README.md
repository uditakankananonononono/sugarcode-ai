# SugarCode AI

**Current honest status: see [STATUS.md](STATUS.md)** - what is verified, thin, and Missing, updated each push. Recorded full-suite runs and their exact scope are in STATUS.md; test counts do not establish spec completeness.

A multi-omic bio-design platform organized as a network of specialized modules on the
**Omega OS v7.0** framework. Built line-by-line from the SugarCode AI spec doc
(`spec/` holds the full per-module spec corpus extracted from the source document).

## Install + CLI (drops 57-60)

Requires Python 3.10+ and a modern pip (23+; older pips can mis-handle PEP 517
builds - drop 58 root cause). Upgrade with `pip install -U pip` if unsure.

```
pip install .
sugarcode version
sugarcode modules                       # the 95 registered modules (77 spec + 18 beyond-spec)
sugarcode splice assess RB1 'c.2500-28T>G'   # deepsplice live assessment, JSON out
sugarcode splice assess SCN1A 'c.959+1G>A' --transcript NM_001165963.1 --offline

# offline bio tools (drop 60), all JSON on stdout:
sugarcode codon cai ATGGCGGCGAAA                 # CAI vs a published usage table
sugarcode codon optimize MAAKRF --gc-min 0.4 --gc-max 0.6
# optimization rejects invalid amino-acid symbols and impossible forbidden motifs; GC repair is heuristic
# CAI treats any observed zero-reference-frequency synonymous codon as a zero index
sugarcode fasta stats sequences.fa               # records, lengths, GC
sugarcode genbank features plasmid.gb            # feature counts + spans
sugarcode pwm score CAGGTAAGT --motif donor      # splice matrix score/scan

# lab reports + notebooks (drop 62):
sugarcode report splice RB1 'c.2490-28T>G' --format html --out report.html
sugarcode report splice RB1 'c.2490-28T>G' --format json   # sha256 evidence bundle
sugarcode report notebook RB1 'c.2490-28T>G' --out assessment.ipynb
sugarcode report validate-notebook assessment.ipynb

# VCF toolkit (drop 63):
sugarcode vcf stats calls.vcf                  # variant classes, Ti/Tv, genotype counts
sugarcode vcf filter calls.vcf --pass-only --min-qual 50 --out clean.vcf
sugarcode vcf csv calls.vcf --sample NA12878 --out calls.csv

# FASTQ toolkit (drop 64):
sugarcode fastq stats reads.fq                 # FastQC-style summary, per-position quality
sugarcode fastq filter reads.fq --min-mean-phred 20 --out clean.fq
sugarcode fastq trim reads.fq --window 4 --min-phred 15 --min-len 36 --out trimmed.fq
sugarcode fastq to-fasta reads.fq --out reads.fa

# GFF3/GTF annotations (drop 65):
sugarcode gff stats anno.gff3                  # feature/seqid/strand summary
sugarcode gff query anno.gff3 --chrom chr1 --start 180 --end 850 --type CDS
sugarcode gff filter anno.gff3 --type gene --seqid chr1 --out genes.gff3
sugarcode gff csv anno.gff3 --out anno.csv

# BED intervals (drop 66):
sugarcode bed stats peaks.bed                  # interval/width/coverage summary
sugarcode bed merge peaks.bed --out merged.bed
sugarcode bed to-gff peaks.bed --feature-type peak --out peaks.gff3

# SAM alignments (drop 67, text SAM):
sugarcode sam stats aln.sam                    # mapping rate, MAPQ, per-reference
sugarcode sam filter aln.sam --mapped-only --min-mapq 30 --out mapped.sam
sugarcode sam to-bed aln.sam --out reads.bedsugarcode sam pileup aln.sam --min-mapq 30           # per-position base counts (drop 70)

# Newick trees (drop 68):
sugarcode phylo stats tree.nwk                 # shape, total length, height
sugarcode phylo mrca tree.nwk --leaves A,B
sugarcode phylo distance tree.nwk --a A --b D
sugarcode phylo prune tree.nwk --drop B,D --out pruned.nwk
sugarcode phylo dist --fasta aln.fa --model jc69   # distance matrix (drop 78)
sugarcode phylo build --fasta aln.fa --method nj --model k80
sugarcode phylo cophenetic tree.nwk

# Alignments (drop 69, Stockholm or A3M - auto-detected):
sugarcode msa stats aln.sto                    # nseq, width, gaps, mean identity
sugarcode msa consensus aln.sto --threshold 0.6
sugarcode msa pid aln.sto --a seq1 --b seq2
sugarcode msa a2m aln.a3m --out aligned.fa     # strip inserts -> match states

# Structures (drop 71, PDB or mmCIF - auto-detected):
sugarcode pdb stats mol.pdb                    # chains, residues, atoms, hetatms
sugarcode pdb contacts mol.pdb --cutoff 4.5 --chain-a A --chain-b B
sugarcode pdb select mol.pdb --chain A --names CA,CB --out trace.pdb

# Protein properties (drop 72, ProtParam-style):
sugarcode protein props proteins.fasta
sugarcode protein props --sequence FVNQHLCGSHLVEALYLVCGERGFFYTPKT

# Primers (drop 73):
sugarcode primer tm CGTTCCAAAGATGTGGGCATGAGCTTAC   # SantaLucia NN Tm + GC%
sugarcode primer check GGGGAAACCCC                # hairpin/dimer heuristics
sugarcode primer pick template.fa --region 250:350 --n 3

# Motifs (drop 74):
sugarcode motif scan --jaspar MA0001.jaspar --fasta promoters.fa --fraction 0.8
sugarcode motif info --iupac RGYWRC
sugarcode motif to-jaspar --sites aligned_sites.fa

# Restriction digests (drop 75, 610 enzymes from REBASE via Biopython):
sugarcode digest run --fasta plasmid.fa --enzymes EcoRI,BamHI --circular
sugarcode digest info EcoRI
sugarcode digest list --match hind

# Pairwise alignment (drop 76, Needleman-Wunsch + Smith-Waterman, affine gaps):
sugarcode align run --a GATTACA --b GATACA                       # global DNA, match/mismatch
sugarcode align run --a WWKNDE --b WWKE --mode local --matrix BLOSUM62
sugarcode align run --fasta pair.fa --gap-open 11 --gap-extend 2

# Differential expression (drop 82, simple per-gene tests - not an NB model):
sugarcode de run --counts counts.tsv --groups ctrl,ctrl,ko,ko --method welch
sugarcode de run --counts counts.tsv --groups ctrl,ctrl,ko,ko --out de.tsv

# Genetics stats (drop 81, HWE exact / association / FDR):
sugarcode gstats hwe --aa 30 --ab 45 --bb 25           # Wigginton 2005 exact
sugarcode gstats allelic --cases 10,20,30 --controls 30,20,10 --yates
sugarcode gstats or --a 40 --b 60 --c 50 --d 50      # OR + Woolf 95% CI
sugarcode gstats adjust --pvalues 0.001,0.02,0.4 --method bh

# RNA-seq counts (drop 80, CPM/RPKM/TPM + DESeq median-of-ratios):
sugarcode rnaseq normalize --counts counts.tsv --method tpm --lengths lens.tsv
sugarcode rnaseq sizefactors --counts counts.tsv        # Anders & Huber 2010
sugarcode rnaseq filter --counts counts.tsv --min-count 10 --min-samples 2

# ORFs + translation (drop 79, NCBI tables 1/2/4/11 vendored):
sugarcode orf translate ATGAAAGGCTAA --table 1
sugarcode orf find --fasta contigs.fa --min-aa 100 --allow-truncated
sugarcode orf find --sequence GTGAAATAA --table 11 --starts table

# k-mers (drop 77, canonical counts + Mash-style minimizer sketches):
sugarcode kmer count --file reads.fq --k 21 --top 5
sugarcode kmer compare --file-a genome1.fa --file-b genome2.fa --k 21
sugarcode kmer compare --a ACGTACGT --b ACGTACGA --k 5 --w 3    # sketch estimate
sugarcode kmer sketch --file genome.fa --k 21 --w 20
```

## Architecture

```
src/omega/            Omega OS v7.0 framework
  registry.py         All 95 registered modules (77 spec + 18 beyond-spec) + 9 sub-networks + lifecycle status
  health.py           Per-module import/self-test health, global compute flux
  search.py           Unified BM25-style biological search over the module corpus
  api.py              FastAPI surface (/modules /subnetworks /health /search)
src/sugarcode/
  bio/                Shared scientific toolkit: sequence ops, FASTA, FASTQ,
                      VCF, GFF3/GTF, BED, SAM, GenBank, codon usage/CAI, PWMs
  report/             Report & export engine: HTML/Markdown reports, CSV/TSV,
                      evidence bundles, .ipynb generation (drop 62)
  modules/<slug>/     One package per module
tests/                pytest suite - one named test per public behavior
spec/                 The spec doc split into 77 module spec files + index
```

## Sub-networks (9)

The source doc states "nine functional sub-networks" without naming them; these
assignments are derived from module themes:

| Sub-network | Modules |
|---|---|
| core-intelligence | 8 |
| genome-editing | 17 |
| protein-engineering | 7 |
| synthetic-biology | 14 |
| cellular-systems | 11 |
| therapeutics | 16 |
| microbiome-phage | 7 |
| fabrication-evolution | 10 |
| platform | 4 |

Counts include the 17 beyond-spec modules registered after the audit fix
(see the build status ledger below).

## Build status ledger (honest counts)

The spec's own counts are internally inconsistent: the intro says **78** modules,
Neuro-Hub's text says an "**84-node** neural stack". **77 modules are actually
specified** in the document; all 77 are registered and spec-filed. We build and
count against the 77 that exist, not the 78/84 claimed.

Beyond the spec, 18 more modules (17 real published-model/computational modules were built
(cfd_offtarget, crisprater, crisprscan_score, mit_offtarget, structural_biophysics,
syn_bio_studio, rna_nussinov, profile_hmm, dti_bench, acmg_bayesian, pgx_guidelines, evidence_mining, neuro_hub_dashboard,
qsar_bench, molecule_eval, chem_descriptors, chem_similarity), plus report_studio (lab report/export engine, pb3). Since the audit-fix drop every one of them is registered,
so the canonical registry now holds **95 modules**, every registry slug equals its
package directory name, and every package under `src/sugarcode/modules/` is
registered. The spec corpus stays 77 files because the spec document has 77.

Status per module: **verified** = implemented with passing named tests;
**thin** = partial implementation; **specified** = spec captured, implementation pending.
**As of drop 3 every one of the 77 specified modules is verified - zero thin, zero pending.**

| Drop | Verified | Thin | Specified (pending) | Tests |
|---|---|---|---|---|
| 1 | 16 | 0 | 61 | not re-run; see STATUS.md |
| 2 | 27 | 0 | 50 | not re-run; see STATUS.md |
| 3 | **77 (all)** | 0 | 0 | not re-run; see STATUS.md |
| 4 | **77 (all)** + 4 live DB connectors | 0 | 0 | not re-run; see STATUS.md |
| 5 | + RCSB PDB & AlphaFold DB structure connector | 0 | 0 | not re-run; see STATUS.md |
| 6 | + real-geometry docking & published CFD off-target model | 0 | 0 | not re-run; see STATUS.md |
| 7 | + published Doench 2014 on-target in design pipeline, e2e connector workflow | 0 | 0 | not re-run; see STATUS.md |
| 8 | + MutDock live UniProt grounding; phageforge inherits CFD | 0 | 0 | not re-run; see STATUS.md |
| 9 | + RareNet live ClinVar enrichment; structure resistance scan; streaming FASTA scan | 0 | 0 | not re-run; see STATUS.md |
| 10 | + ChEMBL live bioactivity in NeoDTI; PubMed trends; Copilot live grounding | 0 | 0 | not re-run; see STATUS.md |
| ... | drops 11-61: live connectors, published models, splice goldens, packaging | 0 | 0 | growing |
| audit-fix | **88 registered (77 spec + 11 beyond-spec)**; stale duplicate tree removed; CI added | 0 | 0 | not re-run; see STATUS.md |
| report_studio + 21 bio toolkits (pb3) | **89 registered (77 spec + 12 beyond-spec)**; report_studio lab report/export engine plus sugarcode.bio toolkits (VCF, FASTQ, GFF, BED, SAM, Newick, Stockholm, pileup, PDB, protein props, primers, motifs, restriction, alignment, k-mers, phylo, ORFs, RNA-seq, genome stats, DE) | 0 | 0 | not re-run; see STATUS.md |
| crisprscan promotion (pb6) | **89 registered (77 spec + 12 beyond-spec)**; orphaned crisprscan_score (Moreno-Mateos 2015, byte-exact vendored coefficients) promoted + Rule Set 2 port in crispr_opt | 0 | 0 | not re-run; see STATUS.md |
| acmg_bayesian (pb6) | **90 registered (77 spec + 13 beyond-spec)**; Tavtigian 2018 Bayesian ACMG/AMP classifier (exact 350^(1/2^k) odds, BA1 stand-alone override, all Table 2/3 rows as fixtures) + optional ClinVar/PubMed context; replaces the unpromoted clinical_evidence_fusion orphan | 0 | 0 | not re-run; see STATUS.md |
| rna_nussinov (pb6) | **91 registered (77 spec + 14 beyond-spec)**; Nussinov-Jacobson 1980 max base-pair RNA folding (traceback, min loop, dot-bracket, exact optimal-structure count, stats), hand fixtures + brute-force verifier | 0 | 0 | not re-run; see STATUS.md |
| profile_hmm (pb6) | **92 registered (77 spec + 15 beyond-spec)**; Durbin Ch. 5 profile HMM from alignments (M/I/D states, pseudocounts), Viterbi path, Forward score, log-odds; hand fixtures + brute-force path enumerator | 0 | 0 | not re-run; see STATUS.md |
| profile_hmm Baum-Welch (pb6) | 92 registered (unchanged); forward-backward EM training on unaligned sequences (ML or Dirichlet MAP), LL-delta convergence, held-out log-likelihood; hand E/M steps + brute-force exact posterior counts | 0 | 0 | not re-run; see STATUS.md |
<!-- S5-001.A04 original quote: "1458 passing, 1 skipped". UNSUPPORTED at 99cb2d329690cf946ae491cb3ca027ee66b7f656: no historical run artifact reproduced; a current test count cannot verify this old total. -->
| chem_descriptors (pb6) | **93 registered (77 spec + 16 beyond-spec)**; pure-Python SMILES parser + MW/exact MW, formula, HBD/HBA, rotatable bonds, rings, Ertl TPSA, Fsp3, Lipinski Ro5 + Veber; fixture-bounded RDKit 2024.09.6 comparisons on a 66-drug ladder (aromatic and Kekule SMILES) and a 60-SMILES stress set; not every descriptor equals RDKit: minimum-cycle-basis ring counts differ from symmetrized SSSR for adamantane/cubane in the ladder and two bridged-ring stress molecules, in addition to salt-formula and deuterium HBA/NHOH differences | 0 | 0 | not re-run; see STATUS.md |
<!-- S5-002.A05 original quote: "1466 passing, 1 skipped". UNSUPPORTED at 99cb2d329690cf946ae491cb3ca027ee66b7f656: no historical run artifact reproduced; a current test count cannot verify this old total. -->
| chem_similarity (pb6) | **94 registered (77 spec + 17 beyond-spec)**; Morgan/ECFP count + folded-bit fingerprints with codes identical to RDKit, Tanimoto/Jaccard/Dice, nearest-neighbour search; RDKit oracle on PubChem CIDs 1-400 (radius 1-3 exact, bulk similarities to 1e-12; chirality is not supported); aromaticity perception extended (exocyclic C=C, pyrrolide N-, fused-pair envelope) | 0 | 0 | not re-run; see STATUS.md |
| pb3 + pb6 integration (current) | **95 registered (77 spec + 18 beyond-spec)**; pb3 and pb6 merged to main; pb6 rows above were counted on its own branch before report_studio | 0 | 0 | not re-run; see STATUS.md |

### Verified in this drop (real implementations, named tests)

| Module | What is real |
|---|---|
| neuro_hub | dashboard aggregation over live health + unified search + project store |
| gene_explorer | central-dogma sequence report (transcribed mRNA, longest-ORF or frame translation, MW, hydrophobicity, both-strand ORF scan) plus text-only animation keyframes and hand-set state/variant/pathway surrogates; the protein may come from a reverse-strand ORF while the mRNA shown is the supplied plus strand, and minus-strand ORF coordinates are local to the reverse complement |
| crispr_opt | PAM enumeration both strands, GC 20-80% filter (a GC 25% guide is accepted; a 40-60% GC window applies only inside the heuristic fallback scoring), position-weighted on-target score, hairpin check, browser-track payload; the main design pass reports off-target risk as a sum of published CFD scores when a background sequence is supplied (otherwise 0/None), while the standalone legacy seed-weighted off-target scan uses fixed uncalibrated weights (exact match 0, 0.35 per seed/PAM-proximal single mismatch, 0.13 per distal single mismatch) |
| codon_opt | CAI optimization vs E. coli K12 / H. sapiens tables, greedy synonymous GC-window repair and motif avoidance, CHI-style tRNA-strain index, single-site TASEP ribosome-flow KMC simulation, uncalibrated folding/load/attention proxies, SBML serialization; one hand-built FBA-style constraint row, no FBA solve |
| prime_design | Exact pegRNA sequence construction (PBS 10-16 nt, RTT 10-20 nt) and actual PE3 spacer/nick candidates for the designs it accepts; not all valid PBS/RTT sets are accepted (a valid PBS16/RTT12 candidate is rejected and the compiler assumes primary nick 0); outcome/repair functions remain hand-set surrogates, not validated predictions |
| deepsplice | splice PWMs learned from 1,170 RefSeqGene GT-AG junctions (29 title-verified genes) + U12 minor-spliceosome matrices from 500 human gold introns (intronIC index; AT-AC and GT-AG U12 donors routed, U12 acceptor routing declined - too weak); variant delta + isoform calls + a polypyrimidine-tract term for AG acceptors (learned from the harvest, additive with unscaled matrix contribution) scored against a curated 28-gene ClinVar fixture + U12 family goldens, 2,720 unique pathogenic + 86 benign cases after full (gene, notation) dedupe (all 2,430 canonical sites scored as loss in this in-sample fixture rescoring: 2,414 U2 GT/GC-AG and 16 AT-AC across five sodium-channel genes), transcript-isoform junction maps via cDNA-record alignment (SCN1A NM_001165963 native), 5'-UTR intron routing (negative c. numbers, GJB2 c.-23+1G>A, canonical and explicit-transcript maps), exon-skip in-frame/frameshift context + alternative outcomes (intron retention with intron lengths from the record, cryptic-site-use candidates), cryptic-site activation scan checked on one published case (CFTR 3849+10kbC>T pseudoexon); isoform calls and Psi are hand-set surrogates; fixture-level results only, not held-out clinical accuracy (counts not re-taken by the audit) |
| str_scope | Exact tandem-repeat search and anchored substitution-interrupted tract reconstruction; HTT/FMR1 motif-checked bands. Generic count comparisons are not pathogenicity calls; diagnostic/repair/intervention models remain uncalibrated surrogates. |
| rna_decoder | DRACH candidate ranking (uncalibrated heuristic), real ViennaRNA thermodynamic ensembles, matched-control nanopore residuals and supplied-rate kinetics. Functional-effect and encapsulation models Missing. |
| promoter_lib | sigma70 consensus-match scoring (-35/-10/spacer/UP element), seeded mutation toward a target score, seeded library generation with fixed-offset or fixed-factor host activity values and a motif heatmap, exact-match TF motif counts, burst-noise formula; scores are not expression data |
| dark_genome | Strand-aware motif/interval annotation, coding-union fraction and merged CpG statistics; short ORFs are NOT lncRNA calls, and reverse-strand ORF coordinates are reverse-complement-local, so the coding-span exclusion is unreliable for reverse-strand ORFs. Regulatory/contact/expression functions remain uncalibrated surrogates, not biological predictions. |
| virtual_cell | stoichiometric FBA (scipy linprog/HiGHS), gene knockout lethality + flux rerouting, dynamic FBA growth simulation |
| synbio_studio | Hill-kinetics ODE circuit simulation (solve_ivp), toggle switch bistability, repressilator, truth-table verification |
| living_computer | boolean expression -> circuit compiler with fidelity scoring, parts registry, stochastic noise analysis (CV) |
| omega_stats | metric recording, per-metric aggregates, sub-network rollup |
| ecosystem | SDK snippet generation, plugin manifest contract, machine-readable API reference |
| dna_to_code | 6 biology->Python concept translations (analogy text plus illustrative Python source strings; five of the six strings call helper names that core.py does not define), with separate executable transcription, translation and point-mutation helpers |
| gene_analysis | Sequence/live annotation integration plus hand-set variant and pathway surrogates; not a causally validated digital twin |
| crispr_cargo | hard-coded vehicle/tissue ranking (LNP/AAV/VLP/PNP) per payload+tissue, illustrative one-compartment PK plus a plasma/target/cleared ODE model, fixed delivery blueprints with composition specs; uncalibrated delivery and immune proxies |
| crispr_muse | policy-gradient gRNA generator with GC/off-target rewards and simulated NGS feedback loop |
| epi_edit | CRISPRa/i promoter-window guide enumeration, sequence GC/motif accessibility and histone-mark proxies (no measured ATAC/ChIP input), hand-set fold-change formula and illustrative effector/network dynamics |
| openclinvar | Local heuristic/curated classification plus appended live ClinVar/gnomAD/splice evidence; transparent Bayesian arithmetic and illustrative graphs/trajectories, not clinical AI |
| genomegpt | k-mer z-score anomalies, TF/CTCF motif scan, convergent-CTCF chromatin loop prediction, motif-disruption variant reading |
| alpha_fold_ui | Chou-Fasman secondary prediction, pLDDT/PAE analogs, idealized C-alpha backbone written as PDB-format text, pocket candidates; separate fetch-and-analysis path for deposited PDB and AlphaFold DB entries |
| docking_studio | SMILES feature parsing (atoms, LogP, RO5), complementarity energy terms (vdW/H-bond/electrostatic/desolvation), Kd estimate, virtual screening |
| evofold_4d | anisotropic network model normal modes (3Nx3N Hessian), hinge detection, open/closed transition traces with RMSD, PTM stiffening perturbation |
| mutdock | class-change ddG + docking rescore per mutation, resistance hotspots, cross-drug resistance forecast |
| protein_painter | keyword-selected fixed fold pattern (four templates), seeded propensity-guided sequence sampling with active-site residues placed on coil positions, Chou-Fasman pattern agreement reported as fold_verified (not a 3D check), composition-based stability estimate and design-score ranking |
| metabodesigner | pathway search by reachability over a built-in 17-reaction table (no route outside it), a linear-program flux balance over the chosen route with fluxes bounded 0-10, and heuristic cofactor, kcat, thermodynamic (default -5 plus cofactor count per step) and intermediate-risk scores |
| synthetic_life | essentiality priors by functional category, minimal-genome knockout sets with FBA growth check |
| bio_material | curated four-material table (PHA, spider_silk, bacterial_cellulose, PLA_bio) with fixed modulus/tensile/biocompatibility values, first-order degradation with hand-set rates, an application modulus check, static structure and fabrication notes, a reaction-graph production-pathway lookup for PHA and PLA_bio, and standalone equation helpers (polymerization, network mechanics, swelling, rheology); not a learned property predictor; not an exhaustive function list |
| cell_free_opt | grid search over a hand-set Gaussian response-surface prior for CFPS yield (relative g/L, no fitted data), fixed-price reagent cost arithmetic reported for the best grid point (no cost ceiling is applied), a decaying-rate kinetic trace, and batch-normalization and replicate-QC helpers; not an exhaustive function list |
| stability_ai | plasmid-loss and mutational-drift forecast over generations from hand-set rates, DNA sequence-window risk map, environment-adjusted decay and aggregation proxies, seeded Wright-Fisher drift runs and intervention ranking; no Arrhenius shelf-life, deamidation-site or per-protein thermal model |
| syn_stab_ai | circuit burden and functional-loss estimate built on stability_ai.stability_forecast, fixed-text stabilization suggestions with hard-coded gain ranges, GC/repeat/palindrome sequence-risk proxy and a seeded drift simulation; no formulation search and no shelf-life model |
| bio_switch | ligand-binding domain + effector fusion design, dose-response Hill curves, switching thresholds |
| biofactory_1_a | biofoundry workflow compiler: Golden Gate/assembly step plans, timing, reagent manifests |
| robotic_flow | liquid-class pipetting step lists with uncalibrated default speeds, air gaps and evaporation terms, greedy dependency scheduling of tasks onto instruments, checkpoint-drift alerts over supplied times, tip-change and sample-lineage bookkeeping; no robot or camera connection bundled |
| phageforge | phage genome feature map + CRISPR guide retargeting for phage engineering |
| cell_twin | cell-state ODE twin (growth/cycle/stress), perturbation response, state-space trajectories |
| fate_predictor | curated reprogramming factor maps, route scoring, efficiency/risk estimates |
| cellfatenet | Checked hand-set GRN ODE/noise simulation and dense-relaxation control search with sparse returned-objective verification; simultaneous controls only. Not trained cell-fate prediction, causal identification or biological validation. |
| organoid_ai | organoid differentiation recipes, growth-factor schedules, maturation scoring |
| bioimage_ai | Classical microscopy segmentation and per-object morphology statistics with finite/label/empty-frame guards; shape/coverage are NOT culture health, viability or passage readiness. No trained phenotype classifier or real-image benchmark verified. |
| cellpainter | Cell Painting channel simulation, morphological profile extraction, perturbation fingerprints |
| cellpainter_4d | time-lapse event model (division/death/motility), 4D trajectory rendering data |
| syndroid | minimal-cell toy simulator: mass/ATP/glucose ODE over six hand-set gene-module rates, MILP minimum-genome selection over a 16-gene hand-set catalog, and a coupled 8-state ODE with Gillespie expression sampling; no patient data, disease parameters or treatment model |
| tissue_eng | scaffold porosity/mechanics + cell-seeding model, vascularization limit, tissue growth forecast |
| infinite_diagnosis | cross-domain differential: symptom->systems mapping across module knowledge domains |
| car_t_designer | CAR architecture per antigen (scFv/hinge/costim), toxicity priors (CRS/ICANS), safety switches |
| living_tx | engineered-microbe therapeutics: chassis pick, payload circuits, kill-switch containment as template text plus a computed containment-risk score |
| neohunter | mutation-spanning peptide enumeration, HLA anchor-motif binding score, immunogenicity rank, vaccine payload |
| gene_tx_opt | tissue->vector/promoter matching, transgene capacity enforcement (refuses AAV cargo over 4.7 kb), NAb risk |
| vector_opt | seeded capsid-region variant list (each entry names a region and a mutation count only; no mutation identities), hand-set heuristic NAb-escape and transduction scores |
| organoid_screen | Drug-panel ranking from hand-set kill-curve parameters for five curated drugs (cisplatin, trametinib, olaparib, venetoclax, gefitinib) and a default 0.4 curve for any other compound (flagged uncurated, same ranked list); IC50 is derived from the curve, not measured; Bliss-expectation synergy only; no organoid model. Live ChEMBL/RCSB/UniProt structure paths exist and combine ChEMBL potency with co-crystal pocket resistance folds into an effective IC50 estimate, with per-compound pocket overrides. Resistance folds are uncalibrated heuristic estimates, usable only as a qualitative ranking, and are not fitted to experimental IC50 shifts. UniProt binding-site annotations are attached as a note when a mutation falls outside a compound's pocket but within 3 residues of an annotated binding site; the note does not change the effective IC50, and nothing is shown if the lookup is unavailable. These paths were not re-run in the audit. |
| neuroplan_ai | tumor segmentation volume, corridor optimization around eloquent regions, risk class + surgical plan |
| neodti_engine | drug-target-pathway-disease graph walk, therapeutic resilience index, disease alias resolution, docking hook |
| liquid_biopsy | Exact binomial allele-error-null testing + BH FDR with integer-implied counts; significant variant signal is NOT tumor origin, disease stage or measured sensitivity. Consensus/multiomics remain uncalibrated and not validated diagnostics. |
| rarenet_ai | phenotype-driven rare-disease matching + unified variant evidence panel (star-tiered ClinVar, gnomAD, splice assessment with U12 GT-AG/AT-AC flags and exon-skip in-frame/out-of-frame context, constraint), ranked differentials |
| oncocircuit | two-input AND-gate tumor sensing circuits, promoter logic, payload delivery design |
| pdx_insight | PDX fidelity index (mutation retention, expression concordance, stroma, drift), verdict + CRISPR repair |
| microbiome_exp | 16S alpha diversity (Shannon/Simpson), functional potential, dysbiosis-disease flags |
| microbiome_rx | gLV community ODE with cross-feeding + antibiotic susceptibility kernels, intervention ranking |
| micro_tx | pair_therapeutic: strain-prebiotic lookup per indication, fixed-profile community simulation (does not depend on the pairing), engraftment markers as text; other module functions are not described by this row |
| microaiverse | cultivation solver: lifestyle classes, auxotrophy supplements, coculture partners, success estimate |
| riboswitch | aptamer + switching-stem design (on/off), stem energetics, dynamic-range prediction |
| phage_tx | phage-pathogen matching, receptor-based resistance routes, escape-suppressing cocktails |
| phage_designer | tail-fiber receptor-binder table with a heuristic adsorption formula (0.55 + 12/affinity, capped at 0.99), chimeric lysin potency heuristic; the gram- strategy is a text note |
| chemgpt_engine | fragment assembly, Crippen-style LogP / logS / RO5 / CYP-hERG priors, Pareto front, retrosynthesis steps |
| bioprint_pro | Cross-model rheology, SI-corrected Poiseuille printability window, first-order crosslinking, fidelity |
| bioplayground | one-locus Wright-Fisher sandbox: selection/drift/mutation and conditional bottleneck events; it stops on sampled fixation/loss, so a scheduled later bottleneck can be skipped even when mutation is nonzero. Retention is only a final-frequency >0.5 flag; interpretation text can falsely attribute a non-extinct neutral allele to fitness-cost loss |
| biosimvr | headless 3D lab scene graph (LabScene) + two scripted sessions with fixed outputs (the CRISPR transfection session sets the reporter signal to 0.72 in code and its conclusion text is fixed; the docking session scores one fixed pocket and ligand with docking_studio.dock), plus separate seeded docking, guide-enumeration and protocol simulations |
| synlife_evo | multi-generation pathway evolution: expression mutation, burden-vs-yield selection, silencing prediction |
| bio_copilot | mutation->domain->ddG->pathway->phenotype chain for three built-in genes (TP53, BRCA1, KRAS) with inconsistency flags, FASTA writer, PDB writer for an idealized CA-only alpha-helix trace (not a predicted structure), keyword question routing |
| synbio_wizard | five-goal/four-chassis catalog->serial pathway LP->chassis ranking->assembly architecture (parts_max is not enforced; O1.. overhangs are placeholders), Monte-Carlo yield interval (200 noisy draws of a heuristic base yield, reported from the 6th and 196th sorted draws, roughly a central 95% interval), feasibility verdict + experiments |
| neuro_pipeline | numpy MLP training with a co-activation (STDP-inspired, not spike-timing) update term, virtual lesion study, activation trace, RSA manifold analysis |
| biogpt_lit | temporal knowledge graph of triples extracted by a relation-word regex (no language model), fixed-formula evidence weights (citations, replication, n), contradiction detection between opposing relation words, multi-hop BFS paths over the aggregated graph, hypothesis generation |
| enterprise_bio | tier tables (academic/startup/enterprise) with in-memory module-gate, compute-quota, spend and audit-chain checks, a file-backed per-tenant Fernet vault and an in-memory robot job queue (jobs are recorded, no hardware is driven); the module gate trusts the caller-supplied module_index |
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
  (Fusi/Doench 2016, Azimuth V3) now RUNS in crispr_opt (rule_set_2.py,
  branch pb6): the published gradient-boosted model was ported out of its
  unloadable sklearn-0.17 pickle into JSON + a pure-NumPy evaluator and is
  bit-faithful to Microsoft's own 947-guide saved-model fixture
  (max abs error 5e-10 vs Microsoft's 1e-3 test tolerance).
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
similarity_check("CC(=O)Oc1ccccc1C(=O)O")    # live ChEMBL neighbours (2026-09-24 top hit: CHEMBL2296002, phase 0)
```

OpenClinVar now adds live ClinVar evidence to its ACMG-style weighing: a
targeted phrase query, title-verified against the requested notation (ClinVar's
phrase search returns near-misses - caught live when c.5266dup initially
matched c.5500dup), with honest sign handling (conflicting/uncertain = weight
0, not positive). EvoFold 4D runs ANM normal modes on real RCSB coordinates
and validates fluctuations against experimental B-factors (1TUP chain B:
Pearson r = 0.05, honestly reported as weak agreement). ChemGPT designs are
checked against live ChEMBL server-side Tanimoto similarity - a 2026-09-24 re-check
returned CHEMBL2296002 (phase 0) as aspirin's top hit, not a 100% phase-4 self-match; an invented molecule
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
python -m pytest -q                 # run counts and commit: see STATUS.md; CI (.github/workflows/ci.yml) runs pytest on pushes to main and wip-unaudited/* and on pull requests
python - <<'PY'
from omega.search import biological_search
print(biological_search("CRISPR guide design")["results"][0]["name"])
from sugarcode.modules.crispr_opt import design_guides
print(design_guides("ATG" + "CG"*40 + "GG" + "A"*40)["guides"][0])
PY
uvicorn omega.api:app --reload      # API surface
```

## Model layer (copilot)

Shared layer: SugarCode also runs on `instinct_models` from shared-models (vendored at `src/instinct_models/`, pin in `VENDORED.md`): `sugarcode shared ask` and `sugarcode shared dataset`. The optional Jev evaluation provider (hosted, paid, OFF by default) is `sugarcode.llm.shared.shared_jev()`. See docs/MODELS.md.

SugarCode can answer questions in plain language by routing them to the right modules and
letting a chat model call those modules as tools. Default models are free: a local
open-weight model through Ollama, then Thinking Machines Inkling-Small on Hugging Face with
a free token. Real Inkling-Small can also run on your own hardware, plus Ornith-1.5-9B and
optional paid Sakana Fugu. See [docs/MODELS.md](docs/MODELS.md).

```bash
sugarcode models list
sugarcode ask "codon optimize MKTAYIAKQRQ for E. coli"
```

### OpenClaw / Hermes (free local route)
Set `INSTINCT_HERMES_URL=http://127.0.0.1:11434/v1`, `INSTINCT_HERMES_MODEL=hermes3:3b`, `INSTINCT_ALLOW_HOSTED=0`; pull the free Hermes 3 weights via local Ollama first. SugarCode's shared router then tries Hermes locally if earlier local providers cannot answer. `sugarcode.llm.shared.openclaw_owner_call` is an explicit, authenticated-owner-only call to a separately installed local OpenClaw Gateway, never in `shared_ask` or public endpoints: set `SUGARCODE_OPENCLAW_URL=http://127.0.0.1:18789/v1` and `SUGARCODE_OPENCLAW_TOKEN` only on a trusted single-owner host, enable its chat-completions endpoint, and pass `owner_confirmed=True` only after owner authentication. The gateway bearer grants full operator rights. Hermes Agent is a separate program, not installed or falsely claimed by this Hermes model route. No paid keys, card or hosted route is needed; a running local Ollama, model download, and (for OpenClaw) separately installed/configured gateway remain necessary. Details and sources: https://github.com/uditakankananonononono/shared-models ; https://docs.openclaw.ai/gateway/openai-http-api ; https://ollama.com/library/hermes3 ; https://hermes-agent.nousresearch.com/docs/guides/local-ollama-setup .

## Jev API status (2026-09-26)

Vercel currently lists `typesafe-ai/jev` without Free Tier eligibility; the gateway route is paid. The TypeSafe direct API is also paid. A browser playground, if available from an official provider, is not free API access. The previously referenced `thejevai.com` could not be verified as TypeSafe AI's official site; do not use it for API keys, billing, or model calls. Official direct API: https://api.typesafe.ai/v1/systemone; keys: https://console.typesafe.ai/keys (https://docs.typesafe.ai/api). Gateway: https://ai-gateway.vercel.sh/typesafe/v1/systemone (https://vercel.com/docs/ai-gateway/sdks-and-apis/typesafe). Both routes stay OFF until a key is explicitly configured. Set `AI_GATEWAY_API_KEY` (or `INSTINCT_AI_GATEWAY_API_KEY`) for the preferred gateway route, or `JEV_API_KEY` (or `INSTINCT_JEV_API_KEY`) for the direct alternate; if both are present the gateway wins. Do not add keys to git. Vercel eligibility: https://vercel.com/ai-gateway/models/providers/typesafe-ai and https://vercel.com/docs/ai-gateway/pricing.

### Self-improvement proposal commit boundary

Proposal commits validate the complete prospective registry schema and its 16 MiB
encoded byte cap before creating the candidates directory or code/test files.
Corrupt-registry preflight errors now surface as `RegistryError` with the original
`RegistryValidationError` cause (a deliberate exception-type change). Capacity or
schema refusal leaves no new candidate files/directory; later IO failures can
still leave an empty directory or hard-crash orphan files. This is in-process
admission, not a cross-file transaction or external-writer race guarantee.

Proposal metadata (`created_at`) is now captured before candidate files are
written rather than after them, so it records proposal preparation time. The
independent auditor saw 23 environment-dependent failures identical on base and
candidate, with no new failures; those did not reproduce in the builder's
1,065-passing selected run. (historical selected run; commit not recorded; not re-run) Counts describe those environments, not universal
compatibility.
### Source admission and snapshot execution

Self-improvement proposal, evaluation, activation and dispatch source now has a
1MiB code /1MiB test UTF8 byte admission ceiling. Over-limit or final-symlink/
nonregular source files refuse. Activation copies verified snapshot bytes;
dispatch executes the verified snapshot instead of reopening source through the
loader. It remains in-process execution, not host-effect isolation. Activation's
hash behavior deliberately changes from newline-normalized text to raw UTF8 bytes,
matching proposal checksums and preserving CRLF code. Existing LF code keeps its
hash. Byte admission is not a CPU/RSS/timeout budget; external-writer/ancestor-path
races and cross-file crash transactions remain outside this boundary. Existing
source-admission helper was previously unwired; these real caller changes are the
separate production integration, not retroactive closure of the earlier helper.

### Cooperating approval consumption and revocation

Engine `activate` and `rollback` require a coordinated approval gate. The file
manual gate now holds a shared canonical-path reentrant lock and stable POSIX
advisory sidecar lock through fresh approval checks and registry commit. Full-
record-only custom gates now refuse at BOTH engine entry points unless they
implement `coordinated_record(id)` yielding a stable identity and full record
while holding their decision lock. Generic gate workflows and trusted direct
registry methods remain available; custom Python implementations are trusted.

Consumption is recorded in the same atomic registry JSON replacement as the
activation/rollback effect. Reuse refuses even if a version is manually restored;
legacy IDs start unused. A revoke winning the gate lock first blocks commit; a
revoke after commit cannot undo it. Auto approval does not bypass consumption.
Locks cooperate across objects/processes, acquire with a 5-second timeout, and
fail closed on unsupported POSIX locking or unsafe sidecars. They do NOT stop
direct file editors, noncooperating writers, ancestor swaps or hardlink aliases.
Deleting/restoring consumption metadata can reopen replay. At-most-once registry
commit is not exactly-once host execution or human authentication. Consumption
history counts against the existing 16 MiB limit; no ceiling relief or retention.
Postreplace durability/logging errors may follow committed state; no blind retry.
The reserved `engine_consumed_approvals` extension must now have the strict map
shape; malformed present records refuse, absent legacy map remains supported.

Process start-barrier tests are real-process smoke checks, not proof of every race
window. Additional forced-lock tests hold a parent sidecar until the child reports
a test-only 0.2-second timeout; production default is separately checked at 5s.
Filesystem open/fstat/IO itself remains outside that acquisition deadline.

### Native evaluation output admission

Native POSIX SandboxRunner caps observed stdout/stderr at 1 MiB each, refuses
output overflow with explicit result flag/stream/reason, and kills its process
group then reaps the direct child on overflow/timeout. Deadline includes inherited
pipe drain. Diagnostics now keep 4,000 BYTES per stream rather than 4,000 Unicode
characters, a deliberate memory-bounded behavior change. It is not an absolute
RSS/CPU quota or host-effect sandbox; escaped-session descendants are outside
scope. IsolatedRunner disk-output and isolated dispatch files are unchanged.

Historical builder-only `/proc` flood measurement in the review packet: 17,744 KiB
baseline RSS, 18,120 KiB sampled peak (376 KiB delta, 10 samples), 1,048,577 observed
stdout bytes, 4,000-byte retained diagnostic ring, child exit -9. These are one
environment's measurements, not a total RSS guarantee or a general memory quota.
The independent auditor's separate run measured 17,628 / 18,068 KiB (440 KiB delta,
9 samples); it is a different run, not the builder packet's historical evidence.

### Immutable extension publication and orphan evidence

Activation now publishes complete fsynced source via exclusive POSIX hard link
before registry commit. Destination must be absent: no overwrite/adoption even
when bytes match, and an existing next-version orphan blocks activation. Failures
retain published files; temps remain until successful unlink. If final directory
sync fails after unlink, the complete final file is the retained artifact. No delete,
repair/replay or version skip. Typed publication errors expose destination,
candidate, published status and registry commit status (unknown when necessary).
Read-only `reconcile_extensions()` compares ALL referenced versions, including
inactive ones, with actual files and reports missing/mismatch/unreferenced/temp/
nonregular/refused reads, bound at 10,000 entries. Evidence-now is not permission.
No all-files-atomic, no exact-once, no tamperproof registry. This is not a cross-
file recovery journal, Windows route or hostile-editor/ancestor-race protection.
Real process-kill stage tests do not prove power-loss behavior of every filesystem.

### Isolated evaluator output parity

IsolatedRunner now uses the same bounded observed-output pipes as native evaluation:
1 MiB per stream plus a refusal byte, explicit overflow flags/reason and process-
group cleanup. Its diagnostic tail deliberately changes from 4,000 Unicode
characters to 4,000 BYTES. Observed-vs-attempted-bytes distinction: this counts bytes
read by the parent, not all bytes the child tried to emit. Existing isolated actual
exit code is preserved on timeout. RLIMIT_FSIZE still applies to candidate regular
files; namespace/mount/containment probe behavior stays unchanged, no fallback.
Probe buffering and isolated dispatch files are outside this repair. This is output
semantic consistency, not full-system containment or a general RSS/CPU guarantee.
