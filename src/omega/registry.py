"""Module registry: every SugarCode AI module, its sub-network and lifecycle state.

95 modules: the 77 from the spec corpus plus 18 beyond-spec
implementations, all registered (slugs equal their package directory names).

The nine sub-networks are assigned from the module themes in the spec doc
(the doc states "nine functional sub-networks" without naming them).
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ModuleSpec:
    slug: str
    name: str
    subnetwork: str
    summary: str
    status: str = "specified"  # specified | thin | verified
    notes: str = ""


SUBNETWORKS: dict[str, str] = {
    "core-intelligence": "Central reasoning, dashboard and literature engines",
    "genome-editing": "Genomic analysis and CRISPR/variant design",
    "protein-engineering": "Structure prediction, docking and de novo design",
    "synthetic-biology": "Circuits, pathways, promoters and biofoundry",
    "cellular-systems": "Cell/tissue simulation and imaging",
    "therapeutics": "Clinical, oncology and personalized-medicine engines",
    "microbiome-phage": "Microbial community and phage design",
    "fabrication-evolution": "Bioprinting, chemistry and evolutionary sandboxes",
    "platform": "Stats, enterprise tiers, SDK and support",
}

_VERIFIED: set[str] = set()  # populated below from _MODULES

_MODULES: list[tuple[str, str, str, str]] = [
    # slug, name, subnetwork, summary
    ("neuro_hub", "Neuro-Hub (Dashboard)", "core-intelligence",
     "Local dashboard: fraction of registered modules importable in this process, keyword search over indexed registry/spec text, process-memory projects; no service uptime or compute telemetry."),
    ("bio_copilot", "Bio-Copilot", "core-intelligence",
     "Keyword-routed research assistant (no language model): live PubMed retrieval, UniProt gene context; mutation-to-phenotype pipeline; FASTA/PDB outputs; CRISPR design; JSON research-artifact serialization."),
    ("synbio_wizard", "SynBio Wizard", "core-intelligence",
     "Guided synthetic-biology compiler: goal definition to pathway design, chassis selection, feasibility and assembly recommendations."),
    ("neuro_pipeline", "Neuro-Pipeline", "core-intelligence",
     "Small numpy MLP with manual-gradient training, L2 weight-anchor continual-update (no Fisher term), virtual lesion studies, activation traces and RSA analysis."),
    ("biogpt_lit", "Literature Relation Extractor (biogpt_lit)", "core-intelligence",
     "NOT BioGPT or any language model (slug kept for compatibility). Regex entity-relation-entity extraction into a knowledge graph with contradiction detection."),
    ("chemgpt_engine", "Fragment Molecule Designer (chemgpt_engine)", "fabrication-evolution",
     "NOT ChemGPT or a neural generator (slug kept for compatibility). Fragment-library SMILES assembly with additive LogP/descriptor estimates and Pareto ranking; no trained model."),
    # S5-021.A05 correction: original "ClinVar variant lookup" is unsupported
    # in this module path. interpret_sequence_variant calls a local heuristic
    # with context-relative coordinates, not a live ClinVar lookup.
    ("genomegpt", "Genome k-mer & Motif Analyzer (genomegpt)", "core-intelligence",
     "NOT a GPT or neural model (slug kept for compatibility). k-mer statistics, IUPAC motif-match energy proxies (not PWM energies), heuristic loop/contact functions and variant reading through the openclinvar module (heuristic; coordinate is context-relative, no transcript grounding)."),
    ("gene_analysis", "Gene Analysis", "genome-editing",
     "Sequence/live annotation integration plus hand-set variant and pathway surrogates; not a causally validated digital twin."),
    ("gene_explorer", "Gene Explorer", "genome-editing",
     "Central-dogma sequence report: mRNA, longest-ORF or frame translation, ORFs and text-only animation keyframes, plus hand-set variant/state/pathway surrogates; reverse-strand ORF coordinates are reverse-complement-local."),
    ("crispr_opt", "CRISPR Opt", "genome-editing",
     "SpCas9 PAM enumeration and published CFD/RS1/RS2 scoring are separate from heuristic guide/context scoring; the off-target scanner accumulates mismatch hits over a caller-supplied background sequence."),
    ("crispr_cargo", "CRISPR Cargo", "genome-editing",
     "Delivery-vehicle ranking from hard-coded vehicle/tissue tables (LNP, AAV, VLP, PNP), illustrative PK models and fixed blueprints; uncalibrated proxies."),
    ("crispr_muse", "CRISPR Muse", "genome-editing",
     "gRNA designer: REINFORCE-style categorical policy over a mechanistic surrogate reward, optional measured-efficiency feedback (no lab validation, no trained deep model); multi-PAM compatibility."),
    ("epi_edit", "Epi-Edit", "genome-editing",
     "Epigenome engineering via CRISPRa/i: promoter-window guides, sequence-derived accessibility and mark proxies, illustrative effector dynamics; no measured chromatin data."),
    ("prime_design", "Prime Design", "genome-editing",
     "Allele-shape checks and exact PBS/RTT/PE3 construction, duplex thermodynamics; no trained model - repair/outcome scores are hand-set surrogates. Assay loaders are not fitted predictors."),
    ("dark_genome", "Dark Genome", "genome-editing",
     "Non-coding DNA analysis by motif and chromatin-heuristic surrogates (no trained foundation model): candidate enhancers, RNA elements, regulatory-landscape mapping."),
    ("rna_decoder", "RNA Decoder", "genome-editing",
     "DRACH candidate heuristics (not a trained or deep model), real ViennaRNA thermodynamic ensembles and supplied-rate kinetics; functional-effect models Missing."),
    ("deepsplice", "DeepSplice", "genome-editing",
     "Variant effect on splicing: learned PWM splice-site strength, mapped splice-window deltas, contextual consequence text and cryptic-site scans, with hand-set regulatory, Psi and isoform surrogates; fixture-level evidence only."),
    ("openclinvar", "OpenClinVar", "genome-editing",
     "Local heuristic/curated classification plus appended live ClinVar/gnomAD/splice evidence; transparent Bayesian arithmetic and illustrative graphs/trajectories, not clinical AI."),
    ("str_scope", "STR-Scope", "genome-editing",
     "Exact repeat scanning and anchored sequence tracts (no trained model); motif-checked locus bands, not validated disease prediction; biological risk models remain uncalibrated."),
    ("codon_opt", "Codon Opt", "genome-editing",
     "Codon optimization: CAI/CHI-style index, greedy GC-window and motif repair, single-site TASEP simulation, uncalibrated load/folding proxies and SBML export; no FBA solve."),
    ("alpha_fold_ui", "Chou-Fasman Structure Sketch & Viewer (alpha_fold_ui)", "protein-engineering",
     "NOT AlphaFold (slug kept for compatibility). 1978 Chou-Fasman secondary-structure propensities with a C-alpha trace; confidence values are propensity-derived, not pLDDT/PAE; a separate path fetches AlphaFold DB and PDB entries and reports confidence statistics and C-alpha-density pockets."),
    ("docking_studio", "Docking Studio", "protein-engineering",
     "Heuristic protein-ligand scoring: pocket-residue-composition and SMILES-feature terms that give a dg and an estimated Kd, a rigid-ligand translation-grid Vina-form scorer on supplied pocket coordinates (vina.py), key-residue listing and virtual screening. An optional AutoDock Vina path (vina_real.py) needs the vina and openbabel packages and was not run in this audit. The dg and Kd values are model outputs, not experimental affinities; not an exhaustive function list."),
    ("evofold_4d", "EvoFold 4D", "protein-engineering",
     "Conformational-transition dynamics: open/closed states, PTM and ligand effects, temporal traces."),
    ("mutdock", "MutDock", "protein-engineering",
     "Mutation effect on drug binding as an uncalibrated blend of a docking-score change and a hand-set residue-class penalty (ddG), with a pocket scan of all 20 amino acids per position and drug that counts positions whose best ddG exceeds 1.0 kcal/mol across drugs; not fitted to resistance data."),
    ("protein_painter", "Protein Painter", "protein-engineering",
     "Sequence sampling from keyword-selected fixed fold patterns with active-site placement; fold_verified is Chou-Fasman pattern agreement, not a 3D check; stability is a composition-based estimate used for ranking."),
    ("bio_material", "Bio-Material", "synthetic-biology",
     "Synthetic biomaterial design: polymer-production pathways, degradation modeling, structure-function prediction."),
    ("synbio_studio", "Syn-Bio Studio", "synthetic-biology",
     "Python API for genetic logic circuits: Hill-kinetics gate composition, ODE simulation, steady-state truth-table checks, and preset repressilator, toggle switch and AND gate; no visual interface."),
    ("metabodesigner", "MetaboDesigner", "synthetic-biology",
     "Novel metabolic pathway design: enzyme/reaction identification, FBA bottleneck analysis, precursor cost."),
    ("promoter_lib", "Promoter Lib", "synthetic-biology",
     "Sigma70 consensus scoring (-35/-10/spacer/UP weights), seeded promoter design and library generation toward a heuristic strength target, motif heatmap, substring matching of supplied TF sites and uncalibrated host and noise proxies; no bundled expression data; TF effects come from a supplied-concentration and Kd occupancy formula, not a fitted binding model."),
    ("synthetic_life", "Synthetic Life", "synthetic-biology",
     "Minimal genome design: essential gene sets, knockout lethality, metabolic requirements of minimal life."),
    ("biofactory_1_a", "BioFactory 1-A", "synthetic-biology",
     "Three static workflow templates (golden_gate, gibson, pcr_screen) returned as step lists with equipment names, a per-step-minutes runtime estimate and fixed tip strings; serial-DAG scheduling, a Gaussian posterior update and PID helpers sit alongside; not an exhaustive function list."),
    ("robotic_flow", "Robotic Flow", "synthetic-biology",
     "Lab-automation planning arithmetic: liquid-class pipetting steps with uncalibrated defaults, greedy task scheduling, checkpoint-drift alerts over supplied times, tip-change and lineage bookkeeping; no robot, camera or instrument connection."),
    ("syn_stab_ai", "Syn-Stab AI", "synthetic-biology",
     "Evolutionary stability prediction for synthetic circuits: failure risk from burden/drift, half-life improvements."),
    ("cell_free_opt", "Cell-Free Opt", "synthetic-biology",
     "CFPS optimization: reagent concentrations for yield, reaction-kinetics simulation, cost calculation."),
    ("stability_ai", "Stability AI", "synthetic-biology",
     "Genetic/phenotypic stability forecast: plasmid loss, mutational drift over generations, stability scores."),
    ("living_computer", "Living Computer", "synthetic-biology",
     "Cellular logic compiler: logic operations mapped to genetic parts, signal propagation and stochastic noise analysis."),
    ("bio_switch", "Bio-Switch", "synthetic-biology",
     "Molecular biosensor design: binding domains coupled to reporters for metabolite/toxin/biomarker detection."),
    ("phageforge", "PhageForge", "cellular-systems",
     "CRISPR-payload bacteriophage engineering against multi-drug-resistant pathogens; host targeting."),
    ("cell_twin", "Cell-Twin", "cellular-systems",
     "Hand-weighted patient-state vector from expression and mutations, five curated drug-action entries with Bliss-independence combinations, and a four-state (viable, apoptotic, proliferating, damage) ODE drug-response simulation; uncalibrated, not a patient outcome predictor."),
    ("fate_predictor", "Fate Predictor", "cellular-systems",
     "Direct reprogramming predictor: required TFs and protocols between cell types with success rates."),
    ("cellfatenet", "CellFateNet", "cellular-systems",
     "Checked hand-set GRN simulation and numerical control search; not causal identification, trained fate prediction or experimental reprogramming validation."),
    ("organoid_ai", "Organoid AI", "cellular-systems",
     "Patient-derived organoid design/simulation: growth conditions, media recipes, spatial expression, drug response."),
    ("virtual_cell", "Virtual Cell", "cellular-systems",
     "Multi-scale cell simulator: FBA + gene-regulatory integration, growth/expression/phenotype prediction."),
    ("bioimage_ai", "BioImage AI", "cellular-systems",
     "Classical image analysis (thresholding/morphology in numpy/scipy; no deep learning): cell counting, morphology assessment, segmentation correction."),
    ("cellpainter", "CellPainter", "cellular-systems",
     "Multiplex fluorescent imaging signatures: morphological fingerprints of drugs/mutations."),
    ("cellpainter_4d", "CellPainter 4D", "cellular-systems",
     "Temporal cell-morphology simulation: event timelines and morphological-drift traces."),
    ("syndroid", "SynDroid", "cellular-systems",
     "Minimal-cell toy simulator: ODEs over six hand-set gene-module rates (behaviors logged from which modules are absent), MILP minimum-genome selection over a 16-gene hand-set catalog and a coupled 8-state ODE; outputs follow from hand-set parameters, not cell data."),
    ("tissue_eng", "Tissue Eng", "cellular-systems",
     "3D bioprinting strategies: biomaterials, cell types, vascularization, mechanical-response simulation."),
    ("infinite_diagnosis", "Infinite Diagnosis", "therapeutics",
     "Keyword-catalog hits grouped into diagnostic clusters, a curated rare-disease catalog, and PubMed/NCBI record lookups; if the lookup fails offline it returns an explicit empty status. No cross-domain literature reasoning."),
    ("car_t_designer", "CAR-T Designer", "therapeutics",
     "CAR construct optimization: scFv/signaling elements per antigen, toxicity prediction, trial simulation."),
    ("living_tx", "Living Tx", "therapeutics",
     "Curated strain selection, a fixed payload/genetic-program template, and microbiome simulation (4-variable ODE in design_living_therapy; design_living_therapeutic scores with an algebraic engraftment heuristic); success scores are heuristic, not validated."),
    ("neohunter", "NeoHunter", "therapeutics",
     "Neoantigen candidate ranking. HLA binding for 9-mers (5 alleles) is a ridge matrix trained on measured IEDB IC50 data with held-out metrics; other lengths use a disclosed heuristic. Immunogenicity is not a trained model."),
    ("gene_tx_opt", "Gene-Tx Opt", "therapeutics",
     "Gene-therapy vector optimization: tissue-specific promoters/capsids, delivery simulation."),
    ("vector_opt", "Vector Opt", "therapeutics",
     "Viral capsid fine-tuning: capsid-receptor docking, neutralizing-antibody impact, transduction efficiency."),
    ("organoid_screen", "Organoid Screen", "therapeutics",
     "Drug-panel ranking from hand-set kill-curve parameters for five curated drugs (cisplatin, trametinib, olaparib, venetoclax, gefitinib) and a default 0.4 curve for any other compound (flagged uncurated, same ranked list); IC50 is derived from the curve, not measured; Bliss-expectation synergy only; no organoid model."),
    ("neuroplan_ai", "NeuroPlan AI", "therapeutics",
     "Neurosurgical planning: MRI segmentation + tractography, safest-path mapping, NeuroTwin risk scores."),
    ("neodti_engine", "NeoDti Engine", "therapeutics",
     "Drug repurposing by mechanistic path analysis plus deterministic spectral graph embedding over drug-target-pathway-disease links (no trained model); Therapeutic Resilience Index."),
    ("liquid_biopsy", "Liquid Biopsy", "therapeutics",
     "Exact binomial allele error-null tests, supplied junction/depth evidence and supplied-label logistic training; not validated cancer diagnosis or tumor-origin inference."),
    ("rarenet_ai", "RareNet AI", "therapeutics",
     "Rare-disease diagnostic reasoning over symptoms + multi-omics with explainable confidence."),
    ("oncocircuit", "OncoCircuit", "therapeutics",
     "Cancer-targeting synthetic circuits: tumor-specific promoters, logic-gated therapeutic triggers."),
    ("pdx_insight", "PDX Insight", "therapeutics",
     "PDX model monitoring: Model Fidelity Index, translational drift, CRISPR restoration strategies."),
    ("microaiverse", "MicroAiverse", "microbiome-phage",
     "Media-recipe lookup by lifestyle and nutrient gaps, a linear-program medium cost fit and partner ranking over caller-supplied requirement and cost numbers, and a small co-culture ODE; no flux balance analysis or genome-scale model."),
    ("microbiome_exp", "Microbiome Exp", "microbiome-phage",
     "16S rRNA taxonomic analysis: diversity indices, distributions, functional potential."),
    ("micro_tx", "Micro-Tx", "microbiome-phage",
     "Microbiome therapeutics. pair_therapeutic: strain-prebiotic lookup per indication; the attached community simulation runs a fixed profile and does not read the pairing; dosing is fixed text. Other functions in the module are not described by this row."),
    ("microbiome_rx", "Microbiome Rx", "microbiome-phage",
     "Microbial-community metabolic interaction simulation: diet/antibiotic effects on metabolite flux."),
    ("riboswitch", "Riboswitch", "microbiome-phage",
     "RNA biosensor design: metabolite-responsive conformational switches, 2D structure, response curves."),
    ("phage_tx", "Phage-Tx", "microbiome-phage",
     "Phage-therapy efficacy model: phage-bacteria coevolution, cocktail optimization."),
    ("phage_designer", "Phage Designer", "microbiome-phage",
     "Phage tail-fiber receptor-binder lookup, lysin-domain potency heuristic, first-order adsorption kinetics and host-range scoring over a supplied receptor profile; engineering steps are text, with no genome modification, cloning or sequence analysis."),
    ("bioprint_pro", "BioPrint Pro", "fabrication-evolution",
     "Bioprinting arithmetic over three hand-set inks: Cross-model viscosity, Hagen-Poiseuille pressure window, first-order crosslinking and an algebraic shape-fidelity score from conversion at 10 s; not fitted to print data."),
    ("bioplayground", "BioPlayground", "fabrication-evolution",
     "Evolutionary sandbox: selective pressures, population drift, robustness testing of engineered systems."),
    ("dna_to_code", "DNA-to-Code", "fabrication-evolution",
     "Biology-to-Python analogy layer: molecular mechanisms rendered as software architecture."),
    ("biosimvr", "BioSimVR", "fabrication-evolution",
     "Simulated 3D virtual-laboratory runner: two scripted sessions with fixed outputs (reporter signal 0.72 set in code for the transfection session) plus separate seeded docking, guide-enumeration and protocol simulations; not a lab experiment."),
    ("synlife_evo", "SynLife Evo", "fabrication-evolution",
     "Seeded population-genetics simulation over configurable generations under supplied fitness and mutation assumptions; no organism or industrial outcome certification."),
    ("omega_stats", "Omega Stats", "platform",
     "Platform performance dashboard: prediction accuracy, efficiency rates, throughput across sub-networks."),
    ("enterprise_bio", "Enterprise Bio", "platform",
     "Computational tier breakdown: academic to industrial access levels, private data vaults."),
    ("ecosystem", "Ecosystem", "platform",
     "Documentation and SDK hub: SDK and client snippets (client snippets target a placeholder API host and /v1/modules/<module>/<operation> paths with no matching route in this repository), plugin manifests with dependency ordering, standards checklists."),
    ("nexus_support", "Nexus Support", "platform",
     "Communication node: inquiries, custom AI build requests, technical support routing."),
    # Beyond-spec modules: real published-model/computational implementations
    # added after the 77-module spec corpus was fully built. Registered here so
    # every package in src/sugarcode/modules/ is canonical (audit finding:
    # registry/source mismatch). Slugs equal their package directory names.
    ("cfd_offtarget", "CFD Off-Target", "genome-editing",
     "Published Doench 2016 Cutting Frequency Determination SpCas9 off-target scoring, vendored exactly with provenance."),
    ("crisprater", "CRISPRater", "genome-editing",
     "Ten-feature CRISPRater linear sgRNA efficacy formula (Labuhn et al. 2018): GC fraction over positions 4-13 plus nine position-base features, intercept and fixed class thresholds; not a verbatim copy of the upstream R code."),
    ("crisprscan_score", "CRISPRscan Score", "genome-editing",
     "Published CRISPRscan/Moreno-Mateos 2015 linear sgRNA activity model (35 nt context, NGG PAM), vendored exactly with provenance."),
    ("mit_offtarget", "MIT Off-Target", "genome-editing",
     "Published MIT/Hsu 2013 SpCas9 pairwise off-target scoring and aggregate guide specificity."),
    ("structural_biophysics", "Structural Biophysics", "protein-engineering",
     "Coordinate-based structural biophysics: Vina-style docking scores, SASA, interface desolvation, pose refinement."),
    ("syn_bio_studio", "Syn-Bio Studio (spec slug)", "synthetic-biology",
     "Circuit architecture compiler with Hill logic, toggle/oscillator ODE simulation and seeded Gillespie expression; no synthesis claims."),
    ("dti_bench", "DTI Bench", "therapeutics",
     "Target-conditioned drug-target interaction baselines (proteochemometric ridge) with cold-start validation on ChEMBL pairs."),
    ("chem_similarity", "Chem Similarity", "fabrication-evolution",
     "Morgan/ECFP circular fingerprints (counts and folded bits, codes identical to RDKit), Tanimoto/Jaccard and Dice, nearest-neighbour search and similarity matrices over SMILES lists."),
    ("chem_descriptors", "Chem Descriptors", "fabrication-evolution",
     "Cheminformatics-lite: SMILES parser (branches, ring closures, brackets, Kekule re-aromatisation) and descriptors (average/exact MW, Hill formula, HBD/HBA, rotatable bonds, SSSR rings, Ertl TPSA, Fsp3) with Lipinski Rule-of-5 and Veber filters, oracle-tested against RDKit and PubChem."),
    ("profile_hmm", "Profile HMM", "protein-engineering",
     "Profile HMMs from multiple alignments (Durbin et al. 1998 Ch. 5): match/insert/delete states, pseudocounts, Viterbi path, Forward score, Baum-Welch EM training with held-out likelihood, brute-force verifiers."),
    ("rna_nussinov", "RNA Nussinov", "synthetic-biology",
     "Nussinov-Jacobson 1980 maximum base-pair RNA secondary structure: DP with traceback, min loop, dot-bracket, exact optimal-structure count, brute-force verifier."),
    ("acmg_bayesian", "ACMG Bayesian", "therapeutics",
     "Tavtigian 2018 Bayesian ACMG/AMP variant classification (exact 350^(1/2^k) odds, BA1 stand-alone override) with optional live ClinVar/PubMed context."),
    ("pgx_guidelines", "PGx Guidelines", "therapeutics",
     "CPIC-aligned pharmacogenomic decision support with provenance-preserved guideline translation."),
    # S5-029.A02 correction: original "feeding downstream modules." is
    # unsupported as shipped wiring. EvidenceMiner returns a standalone table;
    # no downstream module call of this client was located at this commit.
    ("evidence_mining", "Evidence Mining", "core-intelligence",
     "Live, cached evidence mining from PubMed and ClinicalTrials.gov."),
    ("neuro_hub_dashboard", "Neuro-Hub Dashboard (spec slug)", "core-intelligence",
     "Spec-named dashboard surface: module online-count health, a series of online/total module ratios from supplied samples (named global_flux), token-count search over supplied module records, project state and diagnostics over the Neuro-Hub core."),
    ("qsar_bench", "QSAR Bench", "fabrication-evolution",
     "QSAR baseline benchmarking on caller-supplied compounds and activities: Morgan-like fingerprint ridge model, random, scaffold-like and temporal holdout splits, applicability-domain check; holdout metrics only, not external validation. An optional ChEMBL client (live or cached) fetches pChEMBL data, but the benchmark path does not call it."),
    ("molecule_eval", "Molecule Eval", "fabrication-evolution",
     "Auditable evaluation of generated molecular libraries: validity (SMILES parser acceptance), novelty and Pareto fronts. Novelty and distribution comparison score a library against a caller-supplied reference set; a ChEMBL fetch client is included but is not used by the evaluation path."),
    ("report_studio", "Report Studio", "platform",
     "Lab-grade export engine: HTML/Markdown reports with provenance, CSV/TSV exporters, a generated Jupyter notebook (one deepsplice assessment call, structure-checked, not executed here) and sha256-checksummed evidence bundles."),
]

_VERIFIED = {slug for slug, _, _, _ in _MODULES}

REGISTRY: dict[str, ModuleSpec] = {}
for slug, name, subnet, summary in _MODULES:
    assert subnet in SUBNETWORKS, subnet
    status = "verified" if slug in _VERIFIED else "specified"
    REGISTRY[slug] = ModuleSpec(slug=slug, name=name, subnetwork=subnet, summary=summary, status=status)


def module_slugs(subnetwork: str | None = None) -> list[str]:
    if subnetwork is None:
        return list(REGISTRY)
    return [s for s, m in REGISTRY.items() if m.subnetwork == subnetwork]

