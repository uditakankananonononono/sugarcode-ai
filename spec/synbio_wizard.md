> **Current claim-local scope at 7ff2dc87:** the correction section below supersedes the original aspirational wording for its named row IDs only. The original text is retained for traceability, not as a shipped-capability claim. Existing corrections for other rows remain in force.

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


## Claim-local wording corrections at 7ff2dc87

Pinned implementation: `src/sugarcode/modules/synbio_wizard/core.py` at `7ff2dc8748965fcfc55f6ffd3a2efcab4e592368`. These are wording corrections only. They do not implement missing capabilities, establish biological validation, or change runtime behavior.

### Pin-scoped S5-041.03.C01

Original claim (historical): "solid foundations"

Current wording: Wizard combines embedded product/chassis catalog, weighted scores, GC/diversity proxy, dinucleotide energy surrogate and serial-pathway LP. It has no demonstrated comprehensive biological validation.

Source: `src/sugarcode/modules/synbio_wizard/core.py:28 (parse_goal); src/sugarcode/modules/synbio_wizard/core.py:36 (score_chassis); src/sugarcode/modules/synbio_wizard/core.py:44 (codon_metrics); src/sugarcode/modules/synbio_wizard/core.py:52 (rbs_thermodynamics); src/sugarcode/modules/synbio_wizard/core.py:74 (flux_balance)`.

### Pin-scoped S5-041.03.C02

Original claim (historical): "standardized laboratory execution"

Current wording: Assembly helper returns a method/standard name and explicitly says architecture only. No validated procedures, laboratory control or execution protocol is produced.

Source: `src/sugarcode/modules/synbio_wizard/core.py:168 (assembly_recommendation); src/sugarcode/modules/synbio_wizard/core.py:172 (plasmid_architecture)`.

### Pin-scoped S5-041.04.C01

Original claim (historical): "self-evolving"

Current wording: Catalog parameters and design pipeline are fixed. Feedback is a separately invoked count update, not modification of models, code or objectives.

Source: `src/sugarcode/modules/synbio_wizard/core.py:211 (compile_project); src/sugarcode/modules/synbio_wizard/core.py:194 (ingest_experimental_feedback)`.

### Pin-scoped S5-041.04.C02

Original claim (historical): "full-stack biological intelligence system"

Current wording: logic_circuit evaluates Boolean AND/OR/NOT and returns an implementation label. Broader wizard composes catalog/surrogate helpers, not a full-stack biological intelligence system.

Source: `src/sugarcode/modules/synbio_wizard/core.py:110 (logic_circuit); src/sugarcode/modules/synbio_wizard/core.py:211 (compile_project)`.

### Pin-scoped S5-041.04.C05

Original claim (historical): "continuously learning"

Current wording: Manual successes/total updates change caller-carried Beta parameters. There is no persistent learning service or feedback consumption by chassis/flux/yield predictions.

Source: `src/sugarcode/modules/synbio_wizard/core.py:190 (feedback_posterior); src/sugarcode/modules/synbio_wizard/core.py:194 (ingest_experimental_feedback); src/sugarcode/modules/synbio_wizard/core.py:211 (compile_project)`.

### Pin-scoped S5-041.05.C01

Original claim (historical): "constraint-aware biological compiler"

Current wording: Boolean circuit evaluator and project aggregator run. parts_max is not enforced against generated part count, so project output is not a constraint-valid biological compiler.

Source: `src/sugarcode/modules/synbio_wizard/core.py:110 (logic_circuit); src/sugarcode/modules/synbio_wizard/core.py:211 (compile_project); src/sugarcode/modules/synbio_wizard/core.py:216 (run_wizard)`.

### Pin-scoped S5-041.06.C02

Original claim (historical): "codon adaptation index (CAI)"

Current wording: cai_proxy depends on total GC deviation from a chassis target and codon diversity. It does not compute geometric-mean relative synonymous-codon adaptiveness from host usage tables.

Source: `src/sugarcode/modules/synbio_wizard/core.py:44 (codon_metrics)`.

### Pin-scoped S5-041.06.C04

Original claim (historical): "ribosome binding site (RBS) strength (ΔG folding)"

Current wording: RBS energy adds dinucleotide GC/CG and AU/UA counts to a constant and converts this to accessibility. No RNA folding ensemble or ribosome-binding thermodynamics is solved.

Source: `src/sugarcode/modules/synbio_wizard/core.py:52 (rbs_thermodynamics)`.

### Pin-scoped S5-042.01.C01

Original claim (historical): "biology-as-code"

Current wording: deterministic_expression solves a fixed two-state mRNA/protein ODE. This is not a biology programming language or genetic-code compiler.

Source: `src/sugarcode/modules/synbio_wizard/core.py:93 (deterministic_expression)`.

### Pin-scoped S5-042.01.C03

Original claim (historical): "executable genetic constructs"

Current wording: Boolean circuit evaluation, forward guide enumeration, codon proxy and plasmid module labels are produced. No complete DNA construct or laboratory-executable artifact is compiled.

Source: `src/sugarcode/modules/synbio_wizard/core.py:110 (logic_circuit); src/sugarcode/modules/synbio_wizard/core.py:118 (scan_guides); src/sugarcode/modules/synbio_wizard/core.py:128 (variant_effect); src/sugarcode/modules/synbio_wizard/core.py:172 (plasmid_architecture)`.

### Pin-scoped S5-043.02.C03

Original claim (historical): "COBRA/FBA"

Current wording: flux_balance solves a serial-pathway SciPy HiGHS LP under uptake and aggregate ATP/redox inequalities. No stoichiometric equality matrix or COBRA metabolic network is loaded.

Source: `src/sugarcode/modules/synbio_wizard/core.py:74 (flux_balance)`.

### Pin-scoped S5-044.01.C04

Original claim (historical): "continuously updating knowledge graph"

Current wording: knowledge_graph rebuilds nodes/edges from an embedded fixed product catalog. environment_response is a standalone formula; there is no graph persistence or publication update stream.

Source: `src/sugarcode/modules/synbio_wizard/core.py:184 (knowledge_graph); src/sugarcode/modules/synbio_wizard/core.py:200 (environment_response)`.

### Pin-scoped S5-045.02.C01

Original claim (historical): "confidence intervals"

Current wording: uncertainty_distribution reports normal-sampling 5th/95th quantiles as ci90; run_wizard reports 5th/195th sorted values of 200 simulated draws with a corrected approximate-95% label. Neither is fitted confidence coverage.

Source: `src/sugarcode/modules/synbio_wizard/core.py:150 (uncertainty_distribution); src/sugarcode/modules/synbio_wizard/core.py:216 (run_wizard)`.

### Pin-scoped S5-045.04.C01

Original claim (historical): "high epistemic uncertainty"

Current wording: epistemic_fraction is defined as 1/sqrt(data_n), and project uncertainty labels are derived from catalog difficulty. No identifiable epistemic/aleatoric decomposition is fitted.

Source: `src/sugarcode/modules/synbio_wizard/core.py:150 (uncertainty_distribution); src/sugarcode/modules/synbio_wizard/core.py:211 (compile_project)`.

### Pin-scoped S5-045.04.C05

Original claim (historical): "reduce uncertainty"

Current wording: suggest_experiments ranks supplied uncertainty numbers and returns domain templates; expected_information_gain is uncertainty times sensitivity, not predicted posterior reduction.

Source: `src/sugarcode/modules/synbio_wizard/core.py:163 (suggest_experiments)`.

### Pin-scoped S5-045.05.C05

Original claim (historical): "preventing overconfidence"

Current wording: Sampling and a sample-count proxy produce intervals but no calibration, out-of-distribution rejection or overconfidence evaluation exists.

Source: `src/sugarcode/modules/synbio_wizard/core.py:150 (uncertainty_distribution)`.

### Pin-scoped S5-046.01.C03

Original claim (historical): "experimentation"

Current wording: suggest_experiments returns short domain-template descriptions. No experiments are conducted, ingested automatically or evaluated against hypothesis acceptance criteria.

Source: `src/sugarcode/modules/synbio_wizard/core.py:163 (suggest_experiments)`.

### Pin-scoped S5-046.03.C05

Original claim (historical): "truly predictive"

Current wording: feedback_posterior computes a supplied-count Beta posterior; compile_project uses fixed catalog/surrogate formulas and does not consume that feedback. Predictive accuracy has not been validated.

Source: `src/sugarcode/modules/synbio_wizard/core.py:190 (feedback_posterior); src/sugarcode/modules/synbio_wizard/core.py:211 (compile_project)`.

### Pin-scoped S5-046.03.C07

Original claim (historical): "rigor and reproducibility"

Current wording: Project compiler aggregates deterministic/seeded helpers without verified model correctness, recorded environment manifest or laboratory replication. Statistical feedback is manual.

Source: `src/sugarcode/modules/synbio_wizard/core.py:211 (compile_project); src/sugarcode/modules/synbio_wizard/core.py:190 (feedback_posterior)`.


## Stack-local scope corrections

These 140 row-specific dispositions supersede earlier wording only for their listed IDs. No independent reproducer has signed these rows. Counts: COMPLETE 0, PARTIAL 140, UNSUPPORTED 0. Three BUILD rows contain local red/green tests; 137 CORRECT rows narrow wording without capability completion. Original banner and historical text remain unchanged.

### S5-012.A01.C01

Disposition: CORRECT. Final label: PARTIAL.

Input is matched to one of five embedded product names by normalization/substring rules; arbitrary goals and natural-language reasoning are not supported.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:28`.

### S5-012.A01.C02

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-012.A01.C03

Disposition: CORRECT. Final label: PARTIAL.

Four embedded host profiles are ranked using a fixed weighted formula; scores do not establish biological host suitability.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:36`.

### S5-012.A01.C04

Disposition: BUILD. Final label: PARTIAL.

Architecture part budget is enforced before producing the catalog result; no lab procedure or construct sequence is produced.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-012.A02

Disposition: CORRECT. Final label: PARTIAL.

Seeded Gaussian draws and caller-set width/sample-count terms produce central draw intervals; they do not establish coverage against observations or uncertainty reduction.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:156`.

### S5-012.A03.C01

Disposition: CORRECT. Final label: PARTIAL.

A noisy catalog difficulty prior and host score yield a heuristic go/redesign label, not a lab readiness verdict.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:248`.

### S5-012.A03.C02

Disposition: CORRECT. Final label: PARTIAL.

Supplied uncertainty and decision sensitivity rank fixed suggestion strings; no hypothesis search, pathway-knockout simulator or experimental feedback loop is executed.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:169`.

### S5-017.A01.C01

Disposition: CORRECT. Final label: PARTIAL.

Input is matched to one of five embedded product names by normalization/substring rules; arbitrary goals and natural-language reasoning are not supported.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:28`.

### S5-017.A01.C02

Disposition: CORRECT. Final label: PARTIAL.

A serial-pathway linear program constrains abstract uptake, ATP and redox; it is not a genome-scale stoichiometric reconstruction or coupled omics optimizer.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:80`.

### S5-017.A02

Disposition: CORRECT. Final label: PARTIAL.

Four embedded host profiles are ranked using a fixed weighted formula; scores do not establish biological host suitability.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:36`.

### S5-017.A03.C01

Disposition: CORRECT. Final label: PARTIAL.

A noisy catalog difficulty prior and host score yield a heuristic go/redesign label, not a lab readiness verdict.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:248`.

### S5-017.A03.C02

Disposition: CORRECT. Final label: PARTIAL.

Part count chooses Golden Gate or Gibson as an architecture label; no executable assembly procedure or sequence design is produced.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-041.01.C01

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-041.01.C02

Disposition: CORRECT. Final label: PARTIAL.

Input is matched to one of five embedded product names by normalization/substring rules; arbitrary goals and natural-language reasoning are not supported.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:28`.

### S5-041.01.C03

Disposition: CORRECT. Final label: PARTIAL.

A serial-pathway linear program constrains abstract uptake, ATP and redox; it is not a genome-scale stoichiometric reconstruction or coupled omics optimizer.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:80`.

### S5-041.01.C04

Disposition: CORRECT. Final label: PARTIAL.

Four embedded host profiles are ranked using a fixed weighted formula; scores do not establish biological host suitability.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:36`.

### S5-041.02.C01

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied unit-interval scores are combined by fixed weights; ranking is a numerical preference formula.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:161`.

### S5-041.02.C02

Disposition: CORRECT. Final label: PARTIAL.

A noisy catalog difficulty prior and host score yield a heuristic go/redesign label, not a lab readiness verdict.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:248`.

### S5-041.02.C03

Disposition: CORRECT. Final label: PARTIAL.

Part count chooses Golden Gate or Gibson as an architecture label; no executable assembly procedure or sequence design is produced.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-041.03.C01

Disposition: CORRECT. Final label: PARTIAL.

This module supplies part-count assembly labels and architecture only; it does not carry out laboratory work or provide operational laboratory procedures.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-041.03.C02

Disposition: CORRECT. Final label: PARTIAL.

This module supplies part-count assembly labels and architecture only; it does not carry out laboratory work or provide operational laboratory procedures.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-041.03.C03

Disposition: CORRECT. Final label: PARTIAL.

This module supplies part-count assembly labels and architecture only; it does not carry out laboratory work or provide operational laboratory procedures.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-041.04.C01

Disposition: CORRECT. Final label: PARTIAL.

This module uses fixed formulas and count-level Beta posterior updates; no trained learning model, autonomous code growth or experimental-prediction evidence is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:222`.

### S5-041.04.C02

Disposition: CORRECT. Final label: PARTIAL.

This module uses fixed formulas and count-level Beta posterior updates; no trained learning model, autonomous code growth or experimental-prediction evidence is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:222`.

### S5-041.04.C03

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-041.04.C04

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-041.04.C05

Disposition: CORRECT. Final label: PARTIAL.

This module uses fixed formulas and count-level Beta posterior updates; no trained learning model, autonomous code growth or experimental-prediction evidence is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:222`.

### S5-041.05.C01

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-041.05.C02

Disposition: CORRECT. Final label: PARTIAL.

Input is matched to one of five embedded product names by normalization/substring rules; arbitrary goals and natural-language reasoning are not supported.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:28`.

### S5-041.05.C03

Disposition: CORRECT. Final label: PARTIAL.

A serial-pathway linear program constrains abstract uptake, ATP and redox; it is not a genome-scale stoichiometric reconstruction or coupled omics optimizer.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:80`.

### S5-041.05.C04

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-041.05.C05

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-041.05.C06

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-041.05.C07

Disposition: CORRECT. Final label: PARTIAL.

A serial-pathway linear program constrains abstract uptake, ATP and redox; it is not a genome-scale stoichiometric reconstruction or coupled omics optimizer.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:80`.

### S5-041.06.C01

Disposition: CORRECT. Final label: PARTIAL.

Input is matched to one of five embedded product names by normalization/substring rules; arbitrary goals and natural-language reasoning are not supported.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:28`.

### S5-041.06.C02

Disposition: CORRECT. Final label: PARTIAL.

CAI is explicitly a GC-distance/codon-diversity proxy, not host codon-frequency CAI.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:44`.

### S5-041.06.C03

Disposition: BUILD. Final label: PARTIAL.

GC fractions are computed over explicit sliding nucleotide windows; ambiguous input bases are rejected. These are sequence counts, not an expression model.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:44`.

### S5-041.06.C04

Disposition: CORRECT. Final label: PARTIAL.

A local adjacent GC/AU-pair energy proxy is computed; it is not nearest-neighbor RNA folding or a fitted translation-initiation model.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:58`.

### S5-041.06.C05

Disposition: CORRECT. Final label: PARTIAL.

A supplied Hill occupancy model returns relative transcription rates; parameters are caller choices, not fitted host kinetics.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:63`.

### S5-041.06.C06

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied concentrations and dissociation constants determine competitive occupancy; affinity is not inferred from sequence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:68`.

### S5-041.06.C07

Disposition: CORRECT. Final label: PARTIAL.

Copy number, promoter strength and protein length enter a fixed ATP-demand ratio capped at one; this is a resource proxy.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:94`.

### S5-041.07.C01

Disposition: CORRECT. Final label: PARTIAL.

A local adjacent GC/AU-pair energy proxy is computed; it is not nearest-neighbor RNA folding or a fitted translation-initiation model.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:58`.

### S5-041.07.C02

Disposition: CORRECT. Final label: PARTIAL.

Michaelis-Menten rate and kcat-to-capacity unit conversion are computed; there is no kcat/Km optimization.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:76`.

### S5-041.07.C03

Disposition: CORRECT. Final label: PARTIAL.

A serial-pathway linear program constrains abstract uptake, ATP and redox; it is not a genome-scale stoichiometric reconstruction or coupled omics optimizer.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:80`.

### S5-041.07.C04

Disposition: CORRECT. Final label: PARTIAL.

A serial-pathway linear program constrains abstract uptake, ATP and redox; it is not a genome-scale stoichiometric reconstruction or coupled omics optimizer.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:80`.

### S5-041.07.C05

Disposition: CORRECT. Final label: PARTIAL.

A serial-pathway linear program constrains abstract uptake, ATP and redox; it is not a genome-scale stoichiometric reconstruction or coupled omics optimizer.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:80`.

### S5-041.07.C06

Disposition: CORRECT. Final label: PARTIAL.

A serial-pathway linear program constrains abstract uptake, ATP and redox; it is not a genome-scale stoichiometric reconstruction or coupled omics optimizer.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:80`.

### S5-042.01.C01

Disposition: CORRECT. Final label: PARTIAL.

A single mRNA/protein two-variable ODE runs; no multi-gene regulatory network is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:99`.

### S5-042.01.C02

Disposition: CORRECT. Final label: PARTIAL.

Input is matched to one of five embedded product names by normalization/substring rules; arbitrary goals and natural-language reasoning are not supported.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:28`.

### S5-042.01.C03

Disposition: CORRECT. Final label: PARTIAL.

This module supplies part-count assembly labels and architecture only; it does not carry out laboratory work or provide operational laboratory procedures.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-042.02.C01

Disposition: CORRECT. Final label: PARTIAL.

Boolean truth operations return a text implementation label, not a biochemical circuit simulation.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:116`.

### S5-042.02.C02

Disposition: CORRECT. Final label: PARTIAL.

A host-family backbone label and ordered promoter/gene/terminator records are returned; no sequence-level plasmid assembly is produced.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:178`.

### S5-042.02.C03

Disposition: CORRECT. Final label: PARTIAL.

Part count chooses Golden Gate or Gibson as an architecture label; no executable assembly procedure or sequence design is produced.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-042.02.C04

Disposition: CORRECT. Final label: PARTIAL.

A seeded four-channel birth/death SSA runs with a stated event cap; no multi-gene circuit is simulated.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:106`.

### S5-042.02.C05

Disposition: CORRECT. Final label: PARTIAL.

A single mRNA/protein two-variable ODE runs; no multi-gene regulatory network is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:99`.

### S5-042.03.C01

Disposition: CORRECT. Final label: PARTIAL.

Forward-strand 20-base windows with NGG/NAG matching are enumerated and sorted by GC/diversity proxies; no guide optimization against experimental outcomes occurs.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:124`.

### S5-042.03.C02

Disposition: CORRECT. Final label: PARTIAL.

Forward-strand 20-base windows with NGG/NAG matching are enumerated and sorted by GC/diversity proxies; no guide optimization against experimental outcomes occurs.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:124`.

### S5-042.03.C03

Disposition: CORRECT. Final label: PARTIAL.

The score uses guide GC distance and seed nucleotide diversity; this module does not search a genome or score mismatch tolerance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:124`.

### S5-042.04.C01

Disposition: CORRECT. Final label: PARTIAL.

A short codon lookup and supplied conservation/active-site flags drive heuristic scores; no protein coordinates, SIFT or PolyPhen implementation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:134`.

### S5-042.04.C02

Disposition: CORRECT. Final label: PARTIAL.

A short codon lookup and supplied conservation/active-site flags drive heuristic scores; no protein coordinates, SIFT or PolyPhen implementation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:134`.

### S5-042.04.C03

Disposition: CORRECT. Final label: PARTIAL.

A short codon lookup and supplied conservation/active-site flags drive heuristic scores; no protein coordinates, SIFT or PolyPhen implementation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:134`.

### S5-042.04.C04

Disposition: CORRECT. Final label: PARTIAL.

A short codon lookup and supplied conservation/active-site flags drive heuristic scores; no protein coordinates, SIFT or PolyPhen implementation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:134`.

### S5-042.04.C05

Disposition: CORRECT. Final label: PARTIAL.

A short codon lookup and supplied conservation/active-site flags drive heuristic scores; no protein coordinates, SIFT or PolyPhen implementation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:134`.

### S5-043.01.C01

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-043.01.C02

Disposition: CORRECT. Final label: PARTIAL.

A codon-change heuristic feeds multiplicative flux/growth retention formulas; no cellular phenotype or stress-response simulation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:142`.

### S5-043.01.C03

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied conditions enter a Q10/Gaussian-pH/nutrient multiplier; the response is not fitted to observations.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:228`.

### S5-043.02.C01

Disposition: CORRECT. Final label: PARTIAL.

A codon-change heuristic feeds multiplicative flux/growth retention formulas; no cellular phenotype or stress-response simulation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:142`.

### S5-043.02.C02

Disposition: CORRECT. Final label: PARTIAL.

A short codon lookup and supplied conservation/active-site flags drive heuristic scores; no protein coordinates, SIFT or PolyPhen implementation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:134`.

### S5-043.02.C03

Disposition: CORRECT. Final label: PARTIAL.

A serial-pathway linear program constrains abstract uptake, ATP and redox; it is not a genome-scale stoichiometric reconstruction or coupled omics optimizer.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:80`.

### S5-043.02.C04

Disposition: CORRECT. Final label: PARTIAL.

A codon-change heuristic feeds multiplicative flux/growth retention formulas; no cellular phenotype or stress-response simulation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:142`.

### S5-043.02.C05

Disposition: CORRECT. Final label: PARTIAL.

A codon-change heuristic feeds multiplicative flux/growth retention formulas; no cellular phenotype or stress-response simulation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:142`.

### S5-043.02.C06

Disposition: CORRECT. Final label: PARTIAL.

A codon-change heuristic feeds multiplicative flux/growth retention formulas; no cellular phenotype or stress-response simulation is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:142`.

### S5-043.03.C01

Disposition: BUILD. Final label: PARTIAL.

Serial stoichiometry exports as SBML L3V2 core with compartment, species, reaction references and namespaced flux annotation. Parser checks pass for fixtures; no kinetic-engine integration is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:182`.

### S5-043.03.C02

Disposition: CORRECT. Final label: PARTIAL.

A single mRNA/protein two-variable ODE runs; no multi-gene regulatory network is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:99`.

### S5-043.03.C03

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-043.03.C04

Disposition: CORRECT. Final label: PARTIAL.

A single mRNA/protein two-variable ODE runs; no multi-gene regulatory network is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:99`.

### S5-043.03.C05

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied conditions enter a Q10/Gaussian-pH/nutrient multiplier; the response is not fitted to observations.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:228`.

### S5-043.03.C06

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied conditions enter a Q10/Gaussian-pH/nutrient multiplier; the response is not fitted to observations.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:228`.

### S5-043.03.C07

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied conditions enter a Q10/Gaussian-pH/nutrient multiplier; the response is not fitted to observations.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:228`.

### S5-043.04.C01

Disposition: CORRECT. Final label: PARTIAL.

A closed-form mutation/burden/selection decay formula runs; this module does not simulate a population fitness landscape or resistance emergence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:146`.

### S5-043.04.C02

Disposition: CORRECT. Final label: PARTIAL.

A closed-form mutation/burden/selection decay formula runs; this module does not simulate a population fitness landscape or resistance emergence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:146`.

### S5-043.04.C03

Disposition: CORRECT. Final label: PARTIAL.

A closed-form mutation/burden/selection decay formula runs; this module does not simulate a population fitness landscape or resistance emergence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:146`.

### S5-043.04.C04

Disposition: CORRECT. Final label: PARTIAL.

A closed-form mutation/burden/selection decay formula runs; this module does not simulate a population fitness landscape or resistance emergence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:146`.

### S5-043.04.C05

Disposition: CORRECT. Final label: PARTIAL.

A closed-form mutation/burden/selection decay formula runs; this module does not simulate a population fitness landscape or resistance emergence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:146`.

### S5-043.04.C06

Disposition: CORRECT. Final label: PARTIAL.

A closed-form mutation/burden/selection decay formula runs; this module does not simulate a population fitness landscape or resistance emergence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:146`.

### S5-044.01.C01

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-044.01.C02

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-044.01.C03

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-044.01.C04

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-044.02.C01

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-044.02.C02

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-044.02.C03

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied conditions enter a Q10/Gaussian-pH/nutrient multiplier; the response is not fitted to observations.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:228`.

### S5-044.03.C01

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-044.03.C02

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-044.03.C03

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-044.03.C04

Disposition: CORRECT. Final label: PARTIAL.

The graph is an embedded catalog chain and feedback accepts caller-supplied success counts; the module read does not establish the named source integration, omics parser or laboratory evidence.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:212`.

### S5-044.03.C05

Disposition: CORRECT. Final label: PARTIAL.

This module uses fixed formulas and count-level Beta posterior updates; no trained learning model, autonomous code growth or experimental-prediction evidence is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:222`.

### S5-044.04.C01

Disposition: CORRECT. Final label: PARTIAL.

This module supplies part-count assembly labels and architecture only; it does not carry out laboratory work or provide operational laboratory procedures.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-044.04.C02

Disposition: CORRECT. Final label: PARTIAL.

This module supplies part-count assembly labels and architecture only; it does not carry out laboratory work or provide operational laboratory procedures.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-044.04.C03

Disposition: CORRECT. Final label: PARTIAL.

Part count chooses Golden Gate or Gibson as an architecture label; no executable assembly procedure or sequence design is produced.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-044.04.C04

Disposition: CORRECT. Final label: PARTIAL.

This module supplies part-count assembly labels and architecture only; it does not carry out laboratory work or provide operational laboratory procedures.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-044.04.C05

Disposition: CORRECT. Final label: PARTIAL.

This module supplies part-count assembly labels and architecture only; it does not carry out laboratory work or provide operational laboratory procedures.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-045.01

Disposition: CORRECT. Final label: PARTIAL.

Seeded Gaussian draws and caller-set width/sample-count terms produce central draw intervals; they do not establish coverage against observations or uncertainty reduction.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:156`.

### S5-045.02.C01

Disposition: CORRECT. Final label: PARTIAL.

Seeded Gaussian draws and caller-set width/sample-count terms produce central draw intervals; they do not establish coverage against observations or uncertainty reduction.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:156`.

### S5-045.02.C02

Disposition: CORRECT. Final label: PARTIAL.

Seeded Gaussian draws and caller-set width/sample-count terms produce central draw intervals; they do not establish coverage against observations or uncertainty reduction.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:156`.

### S5-045.02.C03

Disposition: CORRECT. Final label: PARTIAL.

Seeded Gaussian draws and caller-set width/sample-count terms produce central draw intervals; they do not establish coverage against observations or uncertainty reduction.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:156`.

### S5-045.02.C04

Disposition: CORRECT. Final label: PARTIAL.

Seeded Gaussian draws and caller-set width/sample-count terms produce central draw intervals; they do not establish coverage against observations or uncertainty reduction.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:156`.

### S5-045.03.C01

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied unit-interval scores are combined by fixed weights; ranking is a numerical preference formula.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:161`.

### S5-045.03.C02

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied unit-interval scores are combined by fixed weights; ranking is a numerical preference formula.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:161`.

### S5-045.03.C03

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied unit-interval scores are combined by fixed weights; ranking is a numerical preference formula.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:161`.

### S5-045.04.C01

Disposition: CORRECT. Final label: PARTIAL.

Seeded Gaussian draws and caller-set width/sample-count terms produce central draw intervals; they do not establish coverage against observations or uncertainty reduction.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:156`.

### S5-045.04.C02

Disposition: CORRECT. Final label: PARTIAL.

Supplied uncertainty and decision sensitivity rank fixed suggestion strings; no hypothesis search, pathway-knockout simulator or experimental feedback loop is executed.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:169`.

### S5-045.04.C03

Disposition: CORRECT. Final label: PARTIAL.

Supplied uncertainty and decision sensitivity rank fixed suggestion strings; no hypothesis search, pathway-knockout simulator or experimental feedback loop is executed.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:169`.

### S5-045.04.C04

Disposition: CORRECT. Final label: PARTIAL.

Supplied uncertainty and decision sensitivity rank fixed suggestion strings; no hypothesis search, pathway-knockout simulator or experimental feedback loop is executed.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:169`.

### S5-045.04.C05

Disposition: CORRECT. Final label: PARTIAL.

Seeded Gaussian draws and caller-set width/sample-count terms produce central draw intervals; they do not establish coverage against observations or uncertainty reduction.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:156`.

### S5-045.04.C06

Disposition: CORRECT. Final label: PARTIAL.

Supplied uncertainty and decision sensitivity rank fixed suggestion strings; no hypothesis search, pathway-knockout simulator or experimental feedback loop is executed.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:169`.

### S5-045.05.C01

Disposition: CORRECT. Final label: PARTIAL.

A contact/hydrogen-bond/charge/flexibility formula returns an energy proxy; no solvent sampling, molecular pose search or conformational ensemble is computed.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:151`.

### S5-045.05.C02

Disposition: CORRECT. Final label: PARTIAL.

A contact/hydrogen-bond/charge/flexibility formula returns an energy proxy; no solvent sampling, molecular pose search or conformational ensemble is computed.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:151`.

### S5-045.05.C03

Disposition: CORRECT. Final label: PARTIAL.

A contact/hydrogen-bond/charge/flexibility formula returns an energy proxy; no solvent sampling, molecular pose search or conformational ensemble is computed.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:151`.

### S5-045.05.C04

Disposition: CORRECT. Final label: PARTIAL.

A contact/hydrogen-bond/charge/flexibility formula returns an energy proxy; no solvent sampling, molecular pose search or conformational ensemble is computed.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:151`.

### S5-045.05.C05

Disposition: CORRECT. Final label: PARTIAL.

Seeded Gaussian draws and caller-set width/sample-count terms produce central draw intervals; they do not establish coverage against observations or uncertainty reduction.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:156`.

### S5-046.01.C01

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-046.01.C02

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-046.01.C03

Disposition: CORRECT. Final label: PARTIAL.

This module supplies part-count assembly labels and architecture only; it does not carry out laboratory work or provide operational laboratory procedures.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-046.02.C01

Disposition: CORRECT. Final label: PARTIAL.

Supplied uncertainty and decision sensitivity rank fixed suggestion strings; no hypothesis search, pathway-knockout simulator or experimental feedback loop is executed.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:169`.

### S5-046.02.C02

Disposition: CORRECT. Final label: PARTIAL.

A single mRNA/protein two-variable ODE runs; no multi-gene regulatory network is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:99`.

### S5-046.02.C03

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-046.03.C01

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-046.03.C02

Disposition: CORRECT. Final label: PARTIAL.

A single mRNA/protein two-variable ODE runs; no multi-gene regulatory network is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:99`.

### S5-046.03.C03

Disposition: CORRECT. Final label: PARTIAL.

This module uses fixed formulas and count-level Beta posterior updates; no trained learning model, autonomous code growth or experimental-prediction evidence is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:222`.

### S5-046.03.C04

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied successes/totals update Beta counts by design name; no assay parser or training loop is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:222`.

### S5-046.03.C05

Disposition: CORRECT. Final label: PARTIAL.

This module uses fixed formulas and count-level Beta posterior updates; no trained learning model, autonomous code growth or experimental-prediction evidence is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:222`.

### S5-046.03.C06

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-046.03.C07

Disposition: CORRECT. Final label: PARTIAL.

This module supplies part-count assembly labels and architecture only; it does not carry out laboratory work or provide operational laboratory procedures.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:174`.

### S5-DISC-synbio_wizard

Disposition: CORRECT. Final label: PARTIAL.

This module uses fixed formulas and count-level Beta posterior updates; no trained learning model, autonomous code growth or experimental-prediction evidence is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:222`.

### S5-CODEDOC-017.C01

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.

### S5-CODEDOC-017.C02

Disposition: CORRECT. Final label: PARTIAL.

A single mRNA/protein two-variable ODE runs; no multi-gene regulatory network is established.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:99`.

### S5-CODEDOC-017.C03

Disposition: CORRECT. Final label: PARTIAL.

Caller-supplied conditions enter a Q10/Gaussian-pH/nutrient multiplier; the response is not fitted to observations.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:228`.

### S5-CODEDOC-017.C04

Disposition: CORRECT. Final label: PARTIAL.

Energy keys in the module use kcal/mol; the source row kJ/mol wording is superseded. Other units are function-specific labels, not an all-input unit guarantee.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:58`.

### S5-CODEDOC-019

Disposition: CORRECT. Final label: PARTIAL.

The callable combines embedded catalog labels, serial flux constraints and numerical proxies. Its outputs are computational examples, not evidence of broader biological performance.

Code read: `src/sugarcode/modules/synbio_wizard/core.py:239`.
