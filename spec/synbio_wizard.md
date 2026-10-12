> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep
> learning, foundation, GNN, or RL model, whatever the text below says. See
> STATUS.md for what is actually verified.

# SynBio Wizard

SynBio Wizard: A guided, multi-step pipeline for synthetic biology projects, taking users from goal definition to pathway design and chassis selection. It automates technical decision-making, providing feasibility assessments and assembly recommendations. This wizard ensures that genetic designs are built on solid foundations and are ready for standardized laboratory execution and synthesis. SynBio Wizard: A self-evolving, full-stack biological intelligence system that transforms synthetic biology into a programmable, simulation-driven, and continuously learning engineering discipline. Rather than operating as a linear design pipeline, it functions as a constraint-aware biological compiler that decomposes high-level user intent into multi-dimensional optimization problems across genomic, transcriptomic, proteomic, and metabolic layers. Given a natural language objective, the system constructs a design manifold constrained by codon adaptation index (CAI), GC content windows, ribosome binding site (RBS) strength (ΔG folding), promoter kinetics, transcription factor binding affinities, and host-specific metabolic burden. It integrates thermodynamic models (e.g., nearest-neighbor RNA folding), enzyme kinetics (a Michaelis–Menten rate and a kcat-to-capacity conversion; there is no kcat/Km optimization), and flux balance analysis (FBA) to generate pathway architectures that are not only theoretically valid but metabolically feasible under chassis-specific constraints such as ATP cost, redox balance, and precursor availability.

At its core, the platform operates as a “biology-as-code” engine, compiling goals that name one of five catalog products (insulin, artemisinin_precursor, vanillin, spider_silk, butanol; any other goal raises KeyError) into executable genetic constructs. It programmatically generates gene circuits using logic-gate abstractions (AND/OR/NOT via repressors and activators), designs plasmid architectures with modular assembly standards (Golden Gate, Gibson), and simulates transcriptional–translational coupling using stochastic and deterministic models (e.g., Gillespie simulations for noise, ODE-based systems for steady-state dynamics). CRISPR modules are integrated at the design layer, enabling automated guide RNA selection using sliding-window + PAM (NGG/NAG) scanning, GC optimization (40–60%), and an off-target proxy score from guide GC and seed-region nucleotide diversity (no mismatch scoring, no genome search). Variant effect prediction pipelines (VEP-like) annotate mutations with predicted deleteriousness (SIFT, PolyPhen proxies), while a variant module maps a user-supplied conservation score to a heuristic ΔΔG and applies an active-site flag (no protein structure is predicted or used).
The system extends beyond static design by embedding multi-scale simulation pipelines that propagate perturbations from DNA edits to phenotypic outcomes. A single nucleotide change is mapped to amino acid substitution, structural perturbation (e.g., disruption of hydrogen bonding networks or metal ion coordination), pathway flux redistribution (via constraint-based modeling such as COBRA/FBA), and ultimately cellular phenotypes such as growth rate or a flux-retention proxy for metabolite yield (there is no stress-response model). a single-gene mRNA/protein ODE and a serial-pathway linear program run, and an SBML-style XML export is written (it fails libsbml checks for SBML L3V2); there is no multi-gene regulatory-network simulation, allowing time-resolved analysis of system dynamics under varying environmental conditions (temperature, pH, nutrient availability). Evolutionary modeling is incorporated through a closed-form mutation-rate decay formula (not a stochastic simulation), a single burden-minus-selection term (there is no fitness landscape), and selection pressure modeling, enabling prediction of construct stability, emergence of resistance, and long-term functional decay, one of the most critical unsolved problems in synthetic biology.
SynBio Wizard also acts as a unified biological data infrastructure, integrating heterogeneous datasets from genomic (Ensembl), proteomic (UniProt), and structural (AlphaFold-like) sources into a continuously updating knowledge graph. Each node (gene, protein, pathway, or phenotype) is linked through experimentally confirmed and inferred relationships, enabling cross-layer reasoning from genotype to phenotype. Experimental outputs (NGS reads, RNA-seq expression profiles, proteomics data) are automatically parsed, normalized, and reintegrated into the system, enabling reinforcement learning from experimental feedback. Protocol generation is limited to a Golden Gate vs Gibson recommendation by part count. Reagent concentrations, thermocycler conditions and validation workflows (e.g., Sanger vs. NGS) are not implemented, and seeded runs repeat numerically but nothing here ensures lab reproducibility.
Critically, the system is uncertainty-aware and probabilistic by design. Instead of deterministic outputs, it generates distributions over possible outcomes, incorporating confidence intervals from a Gaussian whose width is set by a user-supplied model CV and a sample-count term (there is no experimental-noise input). Competing design strategies are presented with quantified trade-offs in efficiency, robustness, and risk. The platform can identify regions of high epistemic uncertainty and propose targeted experiments, such as mutational scans or promoter strength libraries (pathway knockouts are not implemented), to reduce uncertainty and refine predictions. Molecular docking modules simulate protein–ligand interactions using scoring functions approximating binding affinity (ΔG), while highlighting limitations due to conformational flexibility or solvent effects, preventing overconfidence in purely computational predictions.
Ultimately, SynBio Wizard becomes an active discovery engine that closes the loop between design, simulation, and experimentation. It does not merely assist researchers but augments scientific reasoning, ranking templated experiment suggestions by supplied uncertainty (there is no hypothesis generation), stress-testing them against multi-scale models, and iteratively refining them through experimental data. By integrating compiler-like abstraction, systems biology modeling, machine learning, and experimental feedback, it transforms synthetic biology into a discipline that is not just descriptive but truly predictive and programmable, capable of engineering biological systems with the same rigor and reproducibility expected in mature engineering fields.


## Record-specific implementation corrections at 99cb2d32
These corrections apply to the named claims below. Original aspirational wording above is retained for traceability. This is a wording repair, not a claim that the missing functionality was implemented.

### S5-041.03.C03

Original claim: "synthesis".

Correction (UNSUPPORTED): Compiler yields catalog labels, assembly architecture and toy fluxes, not synthesized DNA sequences, confirmed constructs, or synthesis-ready output.

### S5-041.05.C03

Original claim: "multi-dimensional optimization problems".

Correction (PARTIAL): A serial-pathway LP constrains abstract uptake, ATP and redox. No coupled genomic/transcriptomic/proteomic optimization manifold.

### S5-041.05.C04

Original claim: "genomic".

Correction (UNSUPPORTED): compile_project accepts catalog goal, not genome/sequence input; standalone codon/guide helpers are never invoked by compiler.

### S5-041.05.C06

Original claim: "proteomic".

Correction (UNSUPPORTED): Protein-vs-metabolite catalog flag is not proteomic-layer optimization. No protein measurements or structures enter compiler.

### S5-041.06.C01

Original claim: "natural language objective".

Correction (PARTIAL): Parser recognizes product substring and preserves remaining words as source_text; forbidden selected chassis is still selected, parts_max is ignored, and molecular constraints are not compiled.

### S5-041.06.C02

Original claim: "codon adaptation index (CAI)".

Correction (OVERSTATED): cai_proxy uses global GC distance and codon diversity rather than codon relative adaptiveness. Helper is not invoked as a design constraint.

### S5-041.06.C03

Original claim: "GC content windows".

Correction (UNSUPPORTED): Standalone helper reports min/max GC in 30-nt windows; compiler never accepts DNA or calls it, so claimed design-manifold constraint is absent.

### S5-041.06.C04

Original claim: "ribosome binding site (RBS) strength (ΔG folding)".

Correction (OVERSTATED): RBS helper counts adjacent GC/CG/AU/UA pairs with fixed coefficients, not RNA folding. Not invoked by compiler.

### S5-041.06.C05

Original claim: "promoter kinetics".

Correction (PARTIAL): Standalone Hill kinetics respond to regulator input, but compiler neither calls it nor constrains generated designs using promoter kinetics.

### S5-041.06.C06

Original claim: "transcription factor binding affinities".

Correction (PARTIAL): Standalone competitive occupancy computes supplied ligand/Kd, not TF-affinity prediction; compiler does not call it or enforce affinity constraints.

> **Status at 99cb2d32 (rows S5-046.03.xx):** `compile_project` is deterministic for a fixed seed (probe:
> identical JSON on two runs) but only accepts the 5 catalog products (insulin, artemisinin_precursor,
> vanillin, spider_silk, butanol); other goals raise KeyError. No trained model exists. `ingest_experimental_feedback`
> returns Beta-Binomial posteriors and does not change `compile_project` output. `sbml_export` writes a
> non-standard `estimatedFlux` attribute and no kinetic laws or stoichiometry. The module docstring itself says
> the models are heuristic surrogates.
