> **Current claim-local scope at 7ff2dc87:** the correction section below supersedes the original aspirational wording for its named row IDs only. The original text is retained for traceability, not as a shipped-capability claim. Existing corrections for other rows remain in force.

> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep
> learning, foundation, GNN, or RL model, whatever the text below says. See
> STATUS.md for what is actually verified.

# Bio-Copilot

Bio-Copilot: An AI-native research assistant grounded in real-time PubMed data. It answers complex biological questions, simulates mutation-to-phenotype pathways, and generates structured scientific outputs like FASTA or PDB files. The Copilot facilitates high-level experimental planning through an intuitive natural language interface, providing researchers with instant access to synthesized biological knowledge. Bio-Copilot can be expanded into a full-stack AI research environment by integrating multi-modal biological data and advanced simulation pipelines. Beyond real-time PubMed synthesis, it should incorporate genomic, proteomic, and structural databases (e.g., Ensembl, UniProt, AlphaFold) to enable cross-layer reasoning from DNA to phenotype. The platform can include automated CRISPR guide RNA design, off-target prediction, and mutation impact analysis using tools like VEP.

To enhance experimental planning, Bio-Copilot could simulate gene regulatory networks and cellular pathways using SBML-based engines, allowing users to test hypotheses in silico before lab work. Molecular docking and protein–ligand interaction modules (e.g., AutoDock integration) would enable drug discovery workflows. A built-in gene circuit designer and plasmid constructor can support synthetic biology applications.
On the interface side, it should generate reproducible research outputs: Jupyter notebooks, protocols, and visualizations (pathway maps, 3D protein structures). Collaboration features like version control, shared workspaces, and citation tracking would make it team-ready. Finally, integrating fine-tuned domain-specific LLMs and reinforcement learning from experimental feedback could allow the system to improve its predictions over time, evolving into a self-optimizing biological discovery engine. Bio-Copilot evolves into a causal, multi-omic biological reasoning engine that operates as an execution layer over heterogeneous biomedical data and mechanistic models, rather than a retrieval-based assistant. At query time, it constructs a directed acyclic computation graph that links genomic loci to phenotypic endpoints via intermediate representations—variant annotation → transcript isoform selection → codon-level mutation mapping → protein structural perturbation → pathway flux redistribution → cellular state transitions. Each node in this graph is parameterized by domain-specific models: variant impact is computed using ensemble predictors (VEP-like consequence classification, SIFT/PolyPhen-style deleteriousness priors), structural perturbation is approximated via ΔΔG estimation and local residue environment disruption (e.g., hydrogen bond network loss, electrostatic repulsion, metal coordination breakage), and pathway effects are propagated using constraint-based modeling (FBA) or ODE-based regulatory systems. The system does not treat these as isolated modules; it performs cross-layer inference, ensuring that inconsistencies (e.g., structurally tolerated mutations with high pathway disruption) are explicitly flagged and reconciled.
> Correction 2026-10-12 (S5-035.01.C02, ledger record 202): the 'protocols' output above is not implemented. The module emits JSON research artifacts (compile_research_artifact) and experiment-name suggestion lists only; no protocol documents are generated.
The platform’s core architecture integrates multi-modal biological embeddings with symbolic reasoning, enabling both statistical generalization and mechanistic interpretability. Genomic sequences are encoded using transformer-based representations trained on large-scale DNA corpora, while protein structures are embedded via geometric deep learning models operating on residue graphs (capturing spatial adjacency, torsion angles, and interaction energies). These embeddings are aligned with curated biological ontologies (GO terms, pathway hierarchies) to enable semantic reasoning. When answering a query, the system performs retrieval-augmented generation over a continuously updated literature index while simultaneously running programmatic reasoning pipelines—for example, mapping a mutation to its UniProt domain, identifying active-site residues, and simulating downstream signaling perturbations. This hybrid architecture overcomes a key limitation in current systems: purely neural models lack mechanistic grounding, while purely rule-based systems cannot generalize across incomplete data.
CRISPR design is implemented as a genome-scale optimization problem, where candidate guide RNAs are generated via exhaustive sliding-window enumeration over the target locus with PAM filtering (SpCas9 NGG/NAG, extended to Cas variants with alternative PAMs). Each candidate is scored using a composite objective function incorporating GC content (optimal 40–60%), predicted on-target efficiency (sequence-dependent models), secondary structure folding energy (to avoid sgRNA hairpins), and off-target risk computed via genome-wide alignment with mismatch tolerance weighting in the seed region (positions 1–12 proximal to PAM). Chromatin accessibility priors (e.g., ATAC-seq derived openness) and epigenetic marks can be incorporated to refine cutting efficiency predictions. For precise edits, the system dynamically selects between HDR, base editing, or prime editing by evaluating edit type constraints (transition vs. transversion), PAM proximity, and bystander edit risk, and then generates pegRNA designs with optimized primer binding site (PBS) lengths (typically 10–17 nt) and reverse transcriptase templates (10–20 nt) based on local sequence thermodynamics.
Bio-Copilot’s simulation layer executes multi-scale, time-resolved biological models. Gene regulatory networks are represented in SBML and solved using stiff ODE solvers for deterministic dynamics, while stochastic simulations (Gillespie SSA) capture transcriptional noise and low-copy-number effects. Metabolic networks are modeled using COBRA-based FBA, allowing prediction of flux distributions under gene knockouts or overexpression scenarios, constrained by mass balance and thermodynamic feasibility. Protein–ligand interactions are approximated through docking pipelines that evaluate binding poses and estimate free energy changes (ΔG) using scoring functions that account for van der Waals interactions, electrostatics, and desolvation penalties. Importantly, the system propagates uncertainty through these models—sampling parameter distributions to generate confidence intervals over predicted outcomes rather than single-point estimates.
On the output side, Bio-Copilot generates fully executable, reproducible computational artifacts. Each query can be compiled into a Jupyter notebook containing data retrieval steps (API calls to genomic/proteomic databases), preprocessing pipelines, model execution code (e.g., FBA solvers, CRISPR scoring functions), and visualization routines (network graphs, 3D structural renderings). Sequence outputs are provided in FASTA format with precise coordinate mapping, while structural summaries are generated in PDB-like schemas annotating residue-level perturbations and functional domains. Additionally, all results are serialized into strict JSON schemas capturing inputs, intermediate computations, model parameters, and outputs, enabling downstream integration with other tools or pipelines.
Critically, Bio-Copilot operates as a closed-loop, reinforcement-driven discovery system. Experimental results—such as NGS-derived edit efficiencies, RNA-seq expression changes, or proteomics data—are ingested and used to update model parameters via Bayesian or reinforcement learning frameworks. The system maintains posterior distributions over key biological parameters (e.g., editing efficiency, pathway flux coefficients), refining predictions as more data becomes available. It actively identifies regions of high epistemic uncertainty and proposes targeted experiments—such as saturation mutagenesis, CRISPR tiling screens, or pathway perturbations—to maximally reduce uncertainty. Over time, this creates a continuously improving system that not only answers biological questions but optimizes the process of discovering answers, effectively functioning as an autonomous layer for hypothesis generation, validation, and refinement in modern biological research.


## Record-specific implementation corrections at 99cb2d32
These corrections apply to the named claims below. Original aspirational wording above is retained for traceability. This is a wording repair, not a claim that the missing functionality was implemented.

### S5-039.01.C02

Original claim: "reproducible computational artifacts".

Correction (PARTIAL): Serializer repeats supplied result and question; replay lists only generic installation and named-function instructions, not recorded function arguments or executable code.

### S5-039.02.C02

Original claim: "data retrieval steps".

Correction (UNSUPPORTED): Fixture-backed retrieval returns records, but compilation includes no API calls or retrieval steps; notebook generation is absent.

### S5-039.02.C05

Original claim: "CRISPR scoring functions".

Correction (PARTIAL): Standalone guide scoring runs, but compiler emits no executable CRISPR scoring code and no notebook.

### S5-039.03.C03

Original claim: "PDB-like schemas".

Correction (PARTIAL): CA-only ideal helix is parseable fixed-column PDB text; no residue perturbation or domain annotations are added.

### S5-039.04.C02

Original claim: "inputs".

Correction (PARTIAL): Only question and caller-supplied result are captured; actual function inputs gene/ref/pos/alt are not structured inputs in the compiled artifact.

### S5-039.04.C04

Original claim: "model parameters".

Correction (UNSUPPORTED): Artifact has no model-parameter capture. The supplied mutation result contains outputs and labels, not coefficients or full replay parameters.

### S5-039.04.C06

Original claim: "downstream integration".

Correction (PARTIAL): JSON roundtrip works, but no downstream consumer or integration contract is exercised or implemented in this compiler.

### S5-040.01.C01

Original claim: "closed-loop".

Correction (PARTIAL): Feedback returns Beta-binomial counts; the subsequent mutation prediction is identical. No state store or wired closed loop.

### S5-040.02.C01

Original claim: "NGS-derived edit efficiencies".

Correction (PARTIAL): Success/trial counts update posterior mean to .7; no NGS ingestion, read analysis, or updating editing-score pipeline.

### S5-040.02.C04

Original claim: "Bayesian or reinforcement learning frameworks".

Correction (PARTIAL): Standalone Beta-binomial update works; no reinforcement model or updates to model parameters in prediction functions.

### S5-040.03.C01

Original claim: "posterior distributions".

Correction (PARTIAL): Caller can pass previous mean and strength to another scalar update; system does not maintain posterior distributions or parameter-specific state.

### S5-040.03.C02

Original claim: "editing efficiency".

Correction (PARTIAL): Generic success counts can represent a manually supplied rate; no maintained editing-efficiency parameter, recorded edit ingestion, or score update.

### S5-040.03.C04

Original claim: "refining predictions".

Correction (PARTIAL): Repeated scalar posterior update changes .7 to .766667, but mutation/guide predictions do not consume the returned posterior.

### S5-040.05.C04

Original claim: "hypothesis generation".

Correction (UNSUPPORTED): Mutation output contains a fixed experiment list, not hypothesis generation; no hypothesis function in the exported source or artifact compiler.

### S5-040.05.C06

Original claim: "refinement".

Correction (PARTIAL): Manual scalar Bayesian update is not autonomous refinement; unchanged prediction reproduced before and after feedback.


## Claim-local wording corrections at 7ff2dc87

Pinned implementation: `src/sugarcode/modules/bio_copilot/core.py` at `7ff2dc8748965fcfc55f6ffd3a2efcab4e592368`. These are wording corrections only. They do not implement missing capabilities, establish biological validation, or change runtime behavior.

### Pin-scoped S5-037.04.C06

Original claim (historical): "reverse transcriptase templates"

Current wording: For prime editing, selection returns constant PBS=13 and RTT=16 lengths, with no reverse-transcriptase template sequence or thermodynamic optimization.

Source: `src/sugarcode/modules/bio_copilot/core.py:226 (select_editing_strategy)`.

### Pin-scoped S5-038.01.C01

Original claim (historical): "multi-scale"

Current wording: Mutation pipeline chains four scalar heuristic nodes for three embedded genes. It does not couple spatial/time scales or execute SBML, FBA or docking models.

Source: `src/sugarcode/modules/bio_copilot/core.py:28 (mutation_to_phenotype)`.

### Pin-scoped S5-039.01.C01

Original claim (historical): "fully executable"

Current wording: Compiler serializes supplied question/result and generic replay instructions. No notebook, executable code, recorded arguments or runtime environment is emitted.

Source: `src/sugarcode/modules/bio_copilot/core.py:267 (compile_research_artifact)`.

### Pin-scoped S5-039.04.C01

Original claim (historical): "strict JSON schemas"

Current wording: json.dumps is used without a schema validator or a strict JSON configuration; schema_version is a string label, not schema enforcement.

Source: `src/sugarcode/modules/bio_copilot/core.py:267 (compile_research_artifact)`.

### Pin-scoped S5-040.04.C01

Original claim (historical): "regions of high epistemic uncertainty"

Current wording: Monte Carlo multiplies independently sampled Gaussian node values. Mutation output labels data sparsity medium; neither method infers regions of epistemic uncertainty.

Source: `src/sugarcode/modules/bio_copilot/core.py:241 (propagate_uncertainty); src/sugarcode/modules/bio_copilot/core.py:28 (mutation_to_phenotype)`.

### Pin-scoped S5-040.04.C04

Original claim (historical): "pathway perturbations"

Current wording: Mutation result always suggests the same three experiment families, including a catalog pathway reporter. No pathway perturbation is selected or simulated to resolve uncertainty.

Source: `src/sugarcode/modules/bio_copilot/core.py:28 (mutation_to_phenotype)`.

### Pin-scoped S5-040.04.C05

Original claim (historical): "maximally reduce uncertainty"

Current wording: No information-gain objective, posterior experiment simulation, candidate comparison or maximization exists. Feedback suggests replicates based on total pseudo-counts.

Source: `src/sugarcode/modules/bio_copilot/core.py:258 (update_from_experiment); src/sugarcode/modules/bio_copilot/core.py:28 (mutation_to_phenotype)`.

### Pin-scoped S5-040.05.C01

Original claim (historical): "continuously improving system"

Current wording: Standalone Beta-binomial feedback returns new counts/mean. Prediction functions do not consume that state and no durable update loop is wired.

Source: `src/sugarcode/modules/bio_copilot/core.py:258 (update_from_experiment)`.

### Pin-scoped S5-040.05.C03

Original claim (historical): "optimizes the process of discovering answers"

Current wording: Question handling uses keyword routes, gene-catalog responses or PubMed record retrieval. No search-policy learning, outcome-driven discovery optimization or experiment execution occurs.

Source: `src/sugarcode/modules/bio_copilot/core.py:129 (answer); src/sugarcode/modules/bio_copilot/core.py:157 (literature_route)`.
