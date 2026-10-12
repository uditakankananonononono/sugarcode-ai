> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep
> learning, foundation, GNN, or RL model, whatever the text below says. See
> STATUS.md for what is actually verified.

# GenomeGPT

GenomeGPT: A specialized genomic transformer model designed to analyze raw sequence data at scale. It identifies regulatory motifs, predicts 3D chromatin loop interactions, and provides clinical interpretations of sequence variants. By modeling long-range dependencies in DNA, GenomeGPT offers functional insights into how non-coding regions influence gene regulation and disease phenotypes.

GenomeGPT can be pushed into a truly foundation-scale genomic reasoning system by combining ultra-long-context sequence modeling with explicit 3D genome priors and cell-state conditioning. Architecturally, this would move beyond vanilla transformers into hybrid state-space models (e.g., S4/Mamba-like kernels) that scale to million–basepair contexts while preserving long-range signal fidelity. The model would jointly encode raw DNA sequence, positional encodings tied to chromosomal coordinates, and learned embeddings from epigenomic tracks (ATAC-seq, ChIP-seq for histone marks and TF occupancy, DNA methylation), fused via cross-attention layers that align sequence features with biochemical state. A parallel geometric branch would ingest Hi-C/ Micro-C contact maps and learn equivariant representations of chromatin topology, enabling the model to internalize loop extrusion dynamics, CTCF motif orientation constraints, and TAD boundary formation as differentiable priors rather than post hoc annotations.
Training would be multi-objective and self-supervised at scale, combining masked sequence modeling with contrastive alignment across modalities (e.g., predicting ATAC-seq peaks from sequence, reconstructing Hi-C maps from latent embeddings, or inferring cell-type-specific expression profiles from regulatory context). Critically, GenomeGPT would implement conditional generation: given a target cell type or epigenetic state vector, it can predict how the same genomic locus behaves across contexts. This allows it to learn regulatory grammars that are not static but dynamically modulated by cellular environment. Incorporating perturbational datasets (CRISPRi/a screens, MPRA assays) into training enables the model to anchor its predictions in causal signals rather than purely correlative patterns.
A central capability is variant-to-function propagation. For any SNV/indel/structural variant, the model computes Δ-embeddings that quantify changes in transcription factor binding affinity (via learned motif energy landscapes), nucleosome occupancy, and local chromatin accessibility. These local changes are then propagated through the learned 3D genome representation to predict alterations in enhancer–promoter contact probabilities and, ultimately, gene expression shifts. The output is not a single pathogenicity score but a vector of mechanistic deltas: ΔTF binding, ΔATAC signal, ΔHi-C contact frequency, and ΔRNA expression, each with uncertainty estimates derived from ensemble or Bayesian layers. This effectively operationalizes the sequence → structure → regulation → phenotype cascade in a single forward pass.
GenomeGPT would also support in silico genome editing simulation with edit-aware attention masking. Given a proposed CRISPR edit (base edit, prime edit, or indel), the model re-embeds the modified sequence and recomputes downstream regulatory effects, including potential creation/destruction of motifs, shifts in CTCF boundary strength, and reorganization of local chromatin loops. By integrating a differentiable proxy for loop extrusion (parameterized by cohesin residence time and CTCF orientation), it can predict whether an edit will induce ectopic enhancer hijacking or insulation loss—key drivers of disease in non-coding regions. This enables pre-lab screening of edits for both efficacy and unintended regulatory consequences.
Finally, GenomeGPT becomes a design engine through reinforcement learning over regulatory objectives. Users can specify target expression profiles (e.g., “increase gene X expression in hepatocytes without affecting neurons”), and the model proposes minimal sequence edits or synthetic regulatory elements that achieve the objective while respecting constraints on off-target regulatory perturbation. Reward signals are derived from predicted expression changes, chromatin stability, and safety metrics (e.g., avoiding creation of cryptic splice sites or oncogenic enhancer activation). With continual learning from new functional genomics datasets, GenomeGPT converges toward a high-fidelity “genome simulator” that unifies sequence, epigenetics, and 3D architecture into a single, actionable intelligence layer.


## Claim-local corrections at base 99cb2d32 (2026-10-12)

The original aspirational wording above is not an implementation claim. These corrections record counterexamples for the named claims only. They do not mark the requested capability implemented.

### S5-058.03.C01

Original quote: "long-range dependencies"

Verdict: OVERSTATED (previous ledger: SCOPED).

Correction: CTCF pair span heuristics exist, but bag-of-4-mer embeddings lose sequence order: AAAACAAA and AAACAAAA are identical. No learned long-range dependency model.

Evidence: `src/sugarcode/modules/genomegpt/core.py:49-66,110-113`, probes `G02,G07,COLLISION` at base `99cb2d329690cf946ae491cb3ca027ee66b7f656`.


## Claim-local wording corrections at 99cb2d32

The original paragraphs above are aspirations, not shipped-capability claims.
These corrections preserve the original quotes and identify narrower shipped behavior.

- S5-060.01.C03: original "predicting ATAC-seq peaks from sequence". Verdict: OVERSTATED. Correct wording: ATAC is caller-provided or a fixed cell-type scalar repeated in every bin, not a sequence-predicted peak signal. No ATAC peak coordinates or peak caller exist.
- S5-060.01.C04: original "reconstructing Hi-C maps from latent embeddings". Verdict: OVERSTATED. Correct wording: A symmetric sequence-motif/distance-decay proxy matrix is produced. No latent embeddings are input, and no Hi-C reconstruction training or validation against experimental contact maps occurs.
- S5-060.02.C01: original "conditional generation". Verdict: OVERSTATED. Correct wording: The module scores a supplied sequence or exhaustively ranks single-base substitutions. No conditional generative model is implemented.
- S5-060.02.C03: original "epigenetic state vector". Verdict: PARTIAL. Correct wording: epigenetic_fusion accepts a scalar-valued track dictionary, but expression_prediction/cell_state_contrast do not take a state vector. Vector-valued track input fails, so the claimed condition-to-locus prediction path is incomplete.
- S5-061.02.C06: original "local chromatin accessibility". Verdict: OVERSTATED. Correct wording: delta_atac subtracts mean regulatory_activity values combining GC and fixed priors; it is not a delta in ATAC signal or experimentally observed local chromatin accessibility.
- S5-061.03.C02: original "enhancer–promoter contact probabilities". Verdict: OVERSTATED. Correct wording: delta_contact is 0.1 times a best CTCF motif-match difference. There are no enhancer/promoter identities, contact-map propagation or Hi-C-frequency estimates.
- S5-061.04.C02: original "ΔATAC signal". Verdict: OVERSTATED. Correct wording: delta_atac subtracts mean regulatory_activity values combining GC and fixed priors; it is not a delta in ATAC signal or experimentally observed local chromatin accessibility.
- S5-061.04.C03: original "ΔHi-C contact frequency". Verdict: OVERSTATED. Correct wording: delta_contact is 0.1 times a best CTCF motif-match difference. There are no enhancer/promoter identities, contact-map propagation or Hi-C-frequency estimates.
- S5-062.02.C03: original "CTCF boundary strength". Verdict: OVERSTATED. Correct wording: ctcf_boundary_delta is a best motif match-fraction difference (-0.07142857 on destroyed CTCF probe), not computed TAD/CTCF boundary strength.
- S5-062.02.C04: original "reorganization of local chromatin loops". Verdict: PARTIAL. Correct wording: predict_loops can separately be called on edited_sequence (probe loop count falls 1 to 0). simulate_edit itself returns no reference/edited loops, contact map or loop-reorganization result, so the claimed integrated path is incomplete.
- S5-062.03.C04: original "insulation loss". Verdict: PARTIAL. Correct wording: Discrete TAD insulation minima can be computed independently, but simulate_edit does not recompute or compare insulation. Integrated edit-induced insulation loss is not returned.
- S5-063.02.C01: original "target expression profiles". Verdict: PARTIAL. Correct wording: A scalar target_delta plus one cell_type is accepted. No per-gene target profile or cross-cell constraint such as preserving neurons is supported.
- S5-063.02.C04: original "off-target regulatory perturbation". Verdict: UNSUPPORTED. Correct wording: No off-target sequence, other gene, or other cell-state constraint is evaluated by the edit search.
- S5-063.03.C02: original "chromatin stability". Verdict: UNSUPPORTED. Correct wording: The reward is -abs(delta-target_delta)+0.2*(1-splice-risk); it contains no chromatin stability term.
