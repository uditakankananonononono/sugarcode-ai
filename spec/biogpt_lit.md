> **Current claim-local scope at 7ff2dc87:** the correction section below supersedes the original aspirational wording for its named row IDs only. The original text is retained for traceability, not as a shipped-capability claim. Existing corrections for other rows remain in force.

> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep
> learning, foundation, GNN, or RL model, whatever the text below says. See
> STATUS.md for what is actually verified.

# BioGPT Lit

BioGPT Lit: 

BioGPT Lit can be transformed into a continuously evolving, self-indexing scientific reasoning engine that goes far beyond retrieval and summarization to construct a living, multi-layered representation of biological knowledge. At the ingestion layer, the system parses full-text papers, supplementary datasets, figures, and experimental methods, extracting not only entities such as genes, proteins, pathways, and compounds, but also directionally encoded relationships—activation, inhibition, binding affinity shifts, causal disease associations, and experimental conditions. These relationships are embedded into a dynamic, temporally-aware knowledge graph where each edge is weighted by evidence strength, reproducibility signals, citation propagation, and methodological rigor. This enables the system to distinguish between preliminary findings and well-established biological principles, allowing downstream reasoning to be grounded in the quality of evidence rather than mere frequency of mention.

> **Status at 99cb2d32 (rows S5-053.xx):** `parse_full_text` takes an already-loaded dict (title, abstract,
> full_text, methods) and runs regex claim extraction; parse_full_text itself does not fetch papers or parse PDFs; ingest_pubmed separately fetches abstracts. `supplements`
> and `figures` are only counted with `len()`, never read, so supplementary datasets are not parsed
> (S5-053.02.C02 downgraded to UNSUPPORTED). The graph lives in process memory only (no persistence).
> Extraction probe: "Drug X inhibits kinase Y" yields subject "X", object "kinase"; "Gene A binds protein B
> with higher affinity under hypoxia" yields no claim.
On top of this structured graph, BioGPT Lit deploys graph neural networks and long-context transformer architectures to perform multi-hop reasoning across domains that are traditionally siloed. For instance, it can connect insights from immunology, metabolism, and cancer biology by tracing shared intermediates or regulatory motifs, identifying latent connections that are not explicitly stated in any single paper. Temporal modeling allows it to track how scientific consensus evolves, highlighting emerging paradigms, declining hypotheses, or unresolved contradictions. By clustering competing interpretations and quantifying agreement across studies, the system provides a meta-scientific layer of insight—mapping not just what is known, but how confidently it is known and where uncertainty remains.
A defining capability of BioGPT Lit is its ability to detect and formalize contradictions in the literature. Using citation intent classification and semantic entailment models, it can identify when two studies make opposing claims about the same biological mechanism, trace the experimental contexts that led to these differences, and propose reconciliations or targeted experiments to resolve them. This transforms the system into an active participant in scientific discourse, capable of highlighting gaps in knowledge that are not immediately obvious from reading individual papers. It can also prioritize underexplored areas where small amounts of additional data could have outsized impact, effectively guiding researchers toward high-leverage questions.
Beyond analysis, BioGPT Lit functions as a hypothesis-generation engine that produces structured, testable scientific propositions. These hypotheses are not vague suggestions but detailed constructs that include mechanistic rationales, supporting evidence chains, predicted outcomes, and suggested experimental designs. For example, it might propose that a specific non-coding RNA modulates a signaling pathway based on indirect evidence from chromatin accessibility and transcriptional profiling studies, outlining exactly how this could be tested in vitro or in vivo. Each hypothesis is accompanied by a transparent reasoning trace, allowing researchers to audit the logic and evidence behind the suggestion, thereby maintaining scientific rigor while accelerating discovery.
Over time, BioGPT Lit evolves into a self-improving system through feedback from experimental validation and new publications. Confirmed hypotheses strengthen certain edges in the knowledge graph, while disproven ones lead to recalibration of confidence weights and reasoning pathways. This creates a closed-loop system where the engine not only consumes scientific knowledge but actively contributes to its refinement. In its most advanced form, BioGPT Lit becomes a collaborative research partner—one that continuously synthesizes global scientific output, identifies non-obvious connections, and guides researchers toward the most impactful and tractable directions for investigation.


## Claim-local corrections at base 99cb2d32 (2026-10-12)

The original aspirational wording above is not an implementation claim. These corrections record counterexamples for the named claims only. They do not mark the requested capability implemented.

### S5-053.02.C10

Original quote: "experimental conditions"

Verdict: UNSUPPORTED (previous ledger: PARTIAL).

Correction: Text dose/cell context is not extracted; condition fields are only preserved when manually supplied. Claimed ingestion of experimental conditions is absent.

Evidence: `src/sugarcode/modules/biogpt_lit/core.py:141-169,209-220`, probes `B02,B06` at base `99cb2d329690cf946ae491cb3ca027ee66b7f656`.

### S5-053.03.C04

Original quote: "methodological rigor"

Verdict: OVERSTATED (previous ledger: SCOPED).

Correction: Graph ingestion discards paper rigor and edge weighting ignores it: rigor .1 and 1 both produce .315. Separate quality helper uses caller rigor but does not weight graph edges.

Evidence: `src/sugarcode/modules/biogpt_lit/core.py:21-42,195-196`, probes `B03` at base `99cb2d329690cf946ae491cb3ca027ee66b7f656`.

### S5-056.02.C01

Original quote: "mechanistic rationales"

Verdict: OVERSTATED (previous ledger: SCOPED).

Correction: Rationale is low-weight study count or opposing claims, not a biological mechanistic explanation.

Evidence: `src/sugarcode/modules/biogpt_lit/core.py:99-120,242-246`, probes `B09,B16` at base `99cb2d329690cf946ae491cb3ca027ee66b7f656`.

### S5-056.02.C02

Original quote: "supporting evidence chains"

Verdict: PARTIAL (previous ledger: SCOPED).

Correction: Separate evidence_paths preserves paper IDs for requested endpoints, but generated hypotheses do not carry a supporting evidence chain or paper citations themselves.

Evidence: `src/sugarcode/modules/biogpt_lit/core.py:222-229,242-255`, probes `B04,B09,B16` at base `99cb2d329690cf946ae491cb3ca027ee66b7f656`.

### S5-056.04.C02

Original quote: "audit the logic and evidence"

Verdict: PARTIAL (previous ledger: SCOPED).

Correction: Path reports retain IDs for selected endpoints, but hypothesis traces omit claim-level paper evidence; whole hypothesis logic/evidence audit is incomplete.

Evidence: `src/sugarcode/modules/biogpt_lit/core.py:222-229,242-255`, probes `B04,B09,B16` at base `99cb2d329690cf946ae491cb3ca027ee66b7f656`.

### S5-057.02.C02

Original quote: "confidence weights"

Verdict: OVERSTATED (previous ledger: SCOPED).

Correction: Disconfirmation adds an opposing record (.315 to .69) but leaves original activation .94 unchanged; this does not reweight original confidence weights.

Evidence: `src/sugarcode/modules/biogpt_lit/core.py:37-57,248-249`, probes `B11` at base `99cb2d329690cf946ae491cb3ca027ee66b7f656`.

### S5-057.03.C01

Original quote: "closed-loop system"

Verdict: OVERSTATED (previous ledger: SCOPED).

Correction: Publication ingestion and validation are manually invoked helpers; no autonomous experiment/publication feedback loop.

Evidence: `src/sugarcode/modules/biogpt_lit/core.py:172-188,248-249`, probes `B11` at base `99cb2d329690cf946ae491cb3ca027ee66b7f656`.


## Claim-local wording corrections at 7ff2dc87

Pinned implementation: `src/sugarcode/modules/biogpt_lit/core.py` at `7ff2dc8748965fcfc55f6ffd3a2efcab4e592368`. These are wording corrections only. They do not implement missing capabilities, establish biological validation, or change runtime behavior.

### Pin-scoped S5-053.01.C03

Original claim (historical): "scientific reasoning engine"

Current wording: BioGPT Lit uses regex tokenization with relation-word dictionary lookup, in-memory triples, heuristic evidence weights, graph traversal and hypothesis templates. No trained reasoning model or autonomous scientific reasoning is bundled.

Source: `src/sugarcode/modules/biogpt_lit/core.py:8 (KnowledgeGraph); src/sugarcode/modules/biogpt_lit/core.py:141 (extract_claims); src/sugarcode/modules/biogpt_lit/core.py:198 (parse_full_text); src/sugarcode/modules/biogpt_lit/core.py:172 (ingest_pubmed)`.

### Pin-scoped S5-053.01.C04

Original claim (historical): "living, multi-layered representation of biological knowledge"

Current wording: Graph stores claims/metadata in process memory. Updates require manual ingestion; there is no persistent living graph, semantic multi-layer model or continuous indexing service.

Source: `src/sugarcode/modules/biogpt_lit/core.py:17 (KnowledgeGraph.__init__); src/sugarcode/modules/biogpt_lit/core.py:21 (KnowledgeGraph.ingest); src/sugarcode/modules/biogpt_lit/core.py:198 (parse_full_text)`.
