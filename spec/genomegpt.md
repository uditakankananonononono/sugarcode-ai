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

## Genome sequence stack scope at 692143ee

The following row-specific descriptions supersede the corresponding aspirational claims only. Original requirements and the opening banner remain unchanged. No clinical use, biological outcome or model-training claim follows from these bounded computations. Status remains PARTIAL until an independent reproduction records its evidence. UNSUPPORTED names an absent requested capability in the inspected core.py, not absence across unrelated files.

### S5-005.A01

Historical claim: "k-mer z-score anomalies"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Counts observed k-mers and reports deviation from a mononucleotide-frequency expectation. This is a composition heuristic, not a learned genomic model.

Source: `src/sugarcode/modules/genomegpt/core.py:9 (_kmer_zscores)`.

### S5-005.A02.C01

Historical claim: "TF"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Scans supplied DNA for embedded degenerate motif matches. Hits and hit differences do not establish binding or biological function.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-005.A02.C02

Historical claim: "CTCF motif scan"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Scans supplied DNA for embedded degenerate motif matches. Hits and hit differences do not establish binding or biological function.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-005.A03

Historical claim: "convergent-CTCF chromatin loop prediction"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Enumerates convergent CTCF motif pairs exceeding a span threshold and assigns a hand-set span score. This is not learned long-range dependence or a structural contact prediction.

Source: `src/sugarcode/modules/genomegpt/core.py:49 (predict_loops)`.

### S5-005.A04

Historical claim: "motif-disruption variant reading"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Scans supplied DNA for embedded degenerate motif matches. Hits and hit differences do not establish binding or biological function.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-021.A01.C01

Historical claim: "NOT a GPT or neural model"

Disposition: CORRECT. Status: PARTIAL.

Current scope: The genomegpt module name is retained for import compatibility. The inspected core.py uses explicit sequence statistics and heuristics; it contains no GPT or neural-model training.

Source: `src/sugarcode/modules/genomegpt/core.py:111 (sequence_embedding)`.

### S5-021.A01.C02

Historical claim: "slug kept for compatibility"

Disposition: CORRECT. Status: PARTIAL.

Current scope: The genomegpt module name is retained for import compatibility. The inspected core.py uses explicit sequence statistics and heuristics; it contains no GPT or neural-model training.

Source: `src/sugarcode/modules/genomegpt/core.py:111 (sequence_embedding)`.

### S5-021.A02

Historical claim: "k-mer statistics"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Counts observed k-mers and reports deviation from a mononucleotide-frequency expectation. This is a composition heuristic, not a learned genomic model.

Source: `src/sugarcode/modules/genomegpt/core.py:9 (_kmer_zscores)`.

### S5-021.A03

Historical claim: "PWM motif energies"

Disposition: CORRECT. Status: PARTIAL.

Current scope: motif_energy and local_tf_binding score IUPAC match fractions and scale them by -7.5. These are not PWM-derived or learned energies or experimentally established binding affinities.

Source: `src/sugarcode/modules/genomegpt/core.py:185 (motif_energy)`.

### S5-021.A04

Historical claim: "heuristic loop/contact functions"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A distance-power law, fixed orientation multiplier and exponential residence-time factor produce contact proxies. The inspected core.py contains no learned 3D architecture or differentiable loop-extrusion model.

Source: `src/sugarcode/modules/genomegpt/core.py:151 (contact_probability)`.

### S5-021.A05

Historical claim: "ClinVar variant lookup"

Disposition: CORRECT. Status: PARTIAL.

Current scope: The sequence wrapper calls a local variant helper using a context-relative c. coordinate without transcript mapping. Motif differences are not clinical or disease-phenotype interpretation; no ClinVar fetch is performed by this wrapper.

Source: `src/sugarcode/modules/genomegpt/core.py:69 (interpret_sequence_variant)`.

### S5-058.01.C01

Historical claim: "genomic transformer model"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "genomic transformer model" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-058.01.C02

Historical claim: "raw sequence data at scale"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Calculations accept a supplied DNA string and preserve motif positions within that string. No chromosome-scale throughput, coordinate provenance or long-context reasoning guarantee is established by the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-058.02.C01

Historical claim: "regulatory motifs"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Scans supplied DNA for embedded degenerate motif matches. Hits and hit differences do not establish binding or biological function.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-058.02.C02

Historical claim: "3D chromatin loop interactions"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Enumerates convergent CTCF motif pairs exceeding a span threshold and assigns a hand-set span score. This is not learned long-range dependence or a structural contact prediction.

Source: `src/sugarcode/modules/genomegpt/core.py:49 (predict_loops)`.

### S5-058.02.C03

Historical claim: "clinical interpretations of sequence variants"

Disposition: CORRECT. Status: PARTIAL.

Current scope: The sequence wrapper calls a local variant helper using a context-relative c. coordinate without transcript mapping. Motif differences are not clinical or disease-phenotype interpretation; no ClinVar fetch is performed by this wrapper.

Source: `src/sugarcode/modules/genomegpt/core.py:69 (interpret_sequence_variant)`.

### S5-058.03.C01

Historical claim: "long-range dependencies"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Enumerates convergent CTCF motif pairs exceeding a span threshold and assigns a hand-set span score. This is not learned long-range dependence or a structural contact prediction.

Source: `src/sugarcode/modules/genomegpt/core.py:49 (predict_loops)`.

### S5-058.03.C02

Historical claim: "non-coding regions"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Calculations accept a supplied DNA string and preserve motif positions within that string. No chromosome-scale throughput, coordinate provenance or long-context reasoning guarantee is established by the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-058.03.C03

Historical claim: "gene regulation"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A fixed combination of GC, supplied/fixed cell tracks, promoter match and a contact scalar produces an expression proxy. This is not a trained or experimentally established expression profile.

Source: `src/sugarcode/modules/genomegpt/core.py:210 (expression_prediction)`.

### S5-058.03.C04

Historical claim: "disease phenotypes"

Disposition: CORRECT. Status: PARTIAL.

Current scope: The sequence wrapper calls a local variant helper using a context-relative c. coordinate without transcript mapping. Motif differences are not clinical or disease-phenotype interpretation; no ClinVar fetch is performed by this wrapper.

Source: `src/sugarcode/modules/genomegpt/core.py:69 (interpret_sequence_variant)`.

### S5-059.01.C01

Historical claim: "foundation-scale genomic reasoning system"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "foundation-scale genomic reasoning system" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-059.01.C02

Historical claim: "ultra-long-context sequence modeling"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "ultra-long-context sequence modeling" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-059.01.C03

Historical claim: "explicit 3D genome priors"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A distance-power law, fixed orientation multiplier and exponential residence-time factor produce contact proxies. The inspected core.py contains no learned 3D architecture or differentiable loop-extrusion model.

Source: `src/sugarcode/modules/genomegpt/core.py:151 (contact_probability)`.

### S5-059.01.C04

Historical claim: "cell-state conditioning"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Named cell states select fixed priors; caller-supplied scalar or per-bin tracks can override them. No cell-specific learned representation is fitted in the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:138 (epigenetic_fusion)`.

### S5-059.02.C01

Historical claim: "hybrid state-space models"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "hybrid state-space models" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-059.02.C02

Historical claim: "S4/Mamba-like kernels"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "S4/Mamba-like kernels" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-059.02.C03

Historical claim: "million–basepair contexts"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Calculations accept a supplied DNA string and preserve motif positions within that string. No chromosome-scale throughput, coordinate provenance or long-context reasoning guarantee is established by the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-059.02.C04

Historical claim: "long-range signal fidelity"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "long-range signal fidelity" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-059.03.C01

Historical claim: "raw DNA sequence"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Calculations accept a supplied DNA string and preserve motif positions within that string. No chromosome-scale throughput, coordinate provenance or long-context reasoning guarantee is established by the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-059.03.C02

Historical claim: "positional encodings tied to chromosomal coordinates"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "positional encodings tied to chromosomal coordinates" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-059.03.C03

Historical claim: "learned embeddings from epigenomic tracks"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "learned embeddings from epigenomic tracks" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-059.03.C04

Historical claim: "cross-attention layers"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "cross-attention layers" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-059.04.C01

Historical claim: "Hi-C/ Micro-C contact maps"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "Hi-C/ Micro-C contact maps" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-059.04.C02

Historical claim: "equivariant representations of chromatin topology"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "equivariant representations of chromatin topology" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-059.04.C03

Historical claim: "loop extrusion dynamics"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A distance-power law, fixed orientation multiplier and exponential residence-time factor produce contact proxies. The inspected core.py contains no learned 3D architecture or differentiable loop-extrusion model.

Source: `src/sugarcode/modules/genomegpt/core.py:151 (contact_probability)`.

### S5-059.04.C04

Historical claim: "CTCF motif orientation constraints"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Enumerates convergent CTCF motif pairs exceeding a span threshold and assigns a hand-set span score. This is not learned long-range dependence or a structural contact prediction.

Source: `src/sugarcode/modules/genomegpt/core.py:49 (predict_loops)`.

### S5-059.04.C05

Historical claim: "TAD boundary formation as differentiable priors"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "TAD boundary formation as differentiable priors" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-060.01.C01

Historical claim: "masked sequence modeling"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Seeded mask selection reports marginal base-frequency surprisal. No sequence model is fitted or trained to reconstruct masked bases in the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:249 (masked_sequence_objective)`.

### S5-060.01.C02

Historical claim: "contrastive alignment across modalities"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Supplied same-shape arrays are compared by Pearson correlation and absolute error. The inspected helper has no contrastive learning objective or learned alignment transformation.

Source: `src/sugarcode/modules/genomegpt/core.py:254 (modality_alignment)`.

### S5-060.01.C03

Historical claim: "predicting ATAC-seq peaks from sequence"

Disposition: CORRECT. Status: PARTIAL.

Current scope: ATAC values are supplied or repeated fixed priors. delta_atac is a difference in combined regulatory-activity proxies, not inferred ATAC peaks or chromatin-accessibility signal.

Source: `src/sugarcode/modules/genomegpt/core.py:138 (epigenetic_fusion)`.

### S5-060.01.C04

Historical claim: "reconstructing Hi-C maps from latent embeddings"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A motif/orientation and distance-decay proxy matrix is returned. variant delta_contact is a scaled CTCF match difference. Neither is a Hi-C reconstruction or enhancer/promoter-identified frequency estimate.

Source: `src/sugarcode/modules/genomegpt/core.py:156 (reconstruct_contact_map)`.

### S5-060.01.C05

Historical claim: "cell-type-specific expression profiles"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A fixed combination of GC, supplied/fixed cell tracks, promoter match and a contact scalar produces an expression proxy. This is not a trained or experimentally established expression profile.

Source: `src/sugarcode/modules/genomegpt/core.py:210 (expression_prediction)`.

### S5-060.02.C01

Historical claim: "conditional generation"

Disposition: CORRECT. Status: PARTIAL.

Current scope: The module scores supplied sequences and exhaustively ranks single-base substitutions under a scalar objective. It does not generate sequences from a learned conditional model.

Source: `src/sugarcode/modules/genomegpt/core.py:294 (propose_regulatory_edits)`.

### S5-060.02.C02

Historical claim: "target cell type"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Named cell states select fixed priors; caller-supplied scalar or per-bin tracks can override them. No cell-specific learned representation is fitted in the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:138 (epigenetic_fusion)`.

### S5-060.02.C03

Historical claim: "epigenetic state vector"

Disposition: BUILD. Status: PARTIAL.

Current scope: Added scalar/per-bin tracks through fusion, expression and cell contrast. This is caller-supplied state conditioning, not a learned epigenetic model.

Source: `src/sugarcode/modules/genomegpt/core.py:138 (epigenetic_fusion)`.

### S5-060.02.C04

Historical claim: "genomic locus behaves across contexts"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A fixed combination of GC, supplied/fixed cell tracks, promoter match and a contact scalar produces an expression proxy. This is not a trained or experimentally established expression profile.

Source: `src/sugarcode/modules/genomegpt/core.py:210 (expression_prediction)`.

### S5-060.03

Historical claim: "This allows it to learn regulatory grammars that are not static but dynamically modulated by cellular environment."

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "This allows it to learn regulatory grammars that are not static but dynamically modulated by cellular environment." capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-060.04.C01

Historical claim: "CRISPRi/a screens"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "CRISPRi/a screens" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-060.04.C02

Historical claim: "MPRA assays"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "MPRA assays" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-060.04.C03

Historical claim: "causal signals"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "causal signals" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-061.01

Historical claim: "A central capability is variant-to-function propagation."

Disposition: CORRECT. Status: PARTIAL.

Current scope: Substitution, insertion and deletion operations re-score motif/expression/contact proxies. No general structural-variant, CRISPR mechanism, repair-outcome or biological function propagation is established by the inspected helpers.

Source: `src/sugarcode/modules/genomegpt/core.py:237 (simulate_edit)`.

### S5-061.02.C01

Historical claim: "SNV/indel/structural variant"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Substitution, insertion and deletion operations re-score motif/expression/contact proxies. No general structural-variant, CRISPR mechanism, repair-outcome or biological function propagation is established by the inspected helpers.

Source: `src/sugarcode/modules/genomegpt/core.py:237 (simulate_edit)`.

### S5-061.02.C02

Historical claim: "Δ-embeddings"

Disposition: BUILD. Status: PARTIAL.

Current scope: Fixed identical short-sequence zero-vector cosine delta to zero. K-mer frequency vectors still discard ordering and are not learned representations.

Source: `src/sugarcode/modules/genomegpt/core.py:214 (delta_embedding)`.

### S5-061.02.C03

Historical claim: "transcription factor binding affinity"

Disposition: CORRECT. Status: PARTIAL.

Current scope: motif_energy and local_tf_binding score IUPAC match fractions and scale them by -7.5. These are not PWM-derived or learned energies or experimentally established binding affinities.

Source: `src/sugarcode/modules/genomegpt/core.py:185 (motif_energy)`.

### S5-061.02.C04

Historical claim: "learned motif energy landscapes"

Disposition: CORRECT. Status: PARTIAL.

Current scope: motif_energy and local_tf_binding score IUPAC match fractions and scale them by -7.5. These are not PWM-derived or learned energies or experimentally established binding affinities.

Source: `src/sugarcode/modules/genomegpt/core.py:185 (motif_energy)`.

### S5-061.02.C05

Historical claim: "nucleosome occupancy"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A fixed GC and ten-base AT periodicity formula produces a bounded occupancy proxy, not fitted nucleosome placement.

Source: `src/sugarcode/modules/genomegpt/core.py:206 (nucleosome_occupancy)`.

### S5-061.02.C06

Historical claim: "local chromatin accessibility"

Disposition: CORRECT. Status: PARTIAL.

Current scope: ATAC values are supplied or repeated fixed priors. delta_atac is a difference in combined regulatory-activity proxies, not inferred ATAC peaks or chromatin-accessibility signal.

Source: `src/sugarcode/modules/genomegpt/core.py:138 (epigenetic_fusion)`.

### S5-061.03.C01

Historical claim: "learned 3D genome representation"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "learned 3D genome representation" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-061.03.C02

Historical claim: "enhancer–promoter contact probabilities"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A motif/orientation and distance-decay proxy matrix is returned. variant delta_contact is a scaled CTCF match difference. Neither is a Hi-C reconstruction or enhancer/promoter-identified frequency estimate.

Source: `src/sugarcode/modules/genomegpt/core.py:156 (reconstruct_contact_map)`.

### S5-061.03.C03

Historical claim: "gene expression shifts"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A fixed combination of GC, supplied/fixed cell tracks, promoter match and a contact scalar produces an expression proxy. This is not a trained or experimentally established expression profile.

Source: `src/sugarcode/modules/genomegpt/core.py:210 (expression_prediction)`.

### S5-061.04.C01

Historical claim: "ΔTF binding"

Disposition: CORRECT. Status: PARTIAL.

Current scope: motif_energy and local_tf_binding score IUPAC match fractions and scale them by -7.5. These are not PWM-derived or learned energies or experimentally established binding affinities.

Source: `src/sugarcode/modules/genomegpt/core.py:185 (motif_energy)`.

### S5-061.04.C02

Historical claim: "ΔATAC signal"

Disposition: CORRECT. Status: PARTIAL.

Current scope: ATAC values are supplied or repeated fixed priors. delta_atac is a difference in combined regulatory-activity proxies, not inferred ATAC peaks or chromatin-accessibility signal.

Source: `src/sugarcode/modules/genomegpt/core.py:138 (epigenetic_fusion)`.

### S5-061.04.C03

Historical claim: "ΔHi-C contact frequency"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A motif/orientation and distance-decay proxy matrix is returned. variant delta_contact is a scaled CTCF match difference. Neither is a Hi-C reconstruction or enhancer/promoter-identified frequency estimate.

Source: `src/sugarcode/modules/genomegpt/core.py:156 (reconstruct_contact_map)`.

### S5-061.04.C04

Historical claim: "ΔRNA expression"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A fixed combination of GC, supplied/fixed cell tracks, promoter match and a contact scalar produces an expression proxy. This is not a trained or experimentally established expression profile.

Source: `src/sugarcode/modules/genomegpt/core.py:210 (expression_prediction)`.

### S5-061.04.C05

Historical claim: "uncertainty estimates derived from ensemble or Bayesian layers"

Disposition: CORRECT. Status: PARTIAL.

Current scope: uncertainty_std is .05 plus inverse square root of sequence length. It is not an ensemble/Bayesian uncertainty estimate.

Source: `src/sugarcode/modules/genomegpt/core.py:226 (variant_mechanistic_deltas)`.

### S5-061.05.C01

Historical claim: "sequence"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Calculations accept a supplied DNA string and preserve motif positions within that string. No chromosome-scale throughput, coordinate provenance or long-context reasoning guarantee is established by the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-061.05.C02

Historical claim: "structure"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "structure" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-061.05.C03

Historical claim: "regulation"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A fixed combination of GC, supplied/fixed cell tracks, promoter match and a contact scalar produces an expression proxy. This is not a trained or experimentally established expression profile.

Source: `src/sugarcode/modules/genomegpt/core.py:210 (expression_prediction)`.

### S5-061.05.C04

Historical claim: "phenotype"

Disposition: CORRECT. Status: PARTIAL.

Current scope: The sequence wrapper calls a local variant helper using a context-relative c. coordinate without transcript mapping. Motif differences are not clinical or disease-phenotype interpretation; no ClinVar fetch is performed by this wrapper.

Source: `src/sugarcode/modules/genomegpt/core.py:69 (interpret_sequence_variant)`.

### S5-062.01.C01

Historical claim: "genome editing simulation"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Substitution, insertion and deletion operations re-score motif/expression/contact proxies. No general structural-variant, CRISPR mechanism, repair-outcome or biological function propagation is established by the inspected helpers.

Source: `src/sugarcode/modules/genomegpt/core.py:237 (simulate_edit)`.

### S5-062.01.C02

Historical claim: "edit-aware attention masking"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "edit-aware attention masking" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-062.02.C01

Historical claim: "CRISPR edit (base edit, prime edit, or indel)"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Substitution, insertion and deletion operations re-score motif/expression/contact proxies. No general structural-variant, CRISPR mechanism, repair-outcome or biological function propagation is established by the inspected helpers.

Source: `src/sugarcode/modules/genomegpt/core.py:237 (simulate_edit)`.

### S5-062.02.C02

Historical claim: "creation/destruction of motifs"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Scans supplied DNA for embedded degenerate motif matches. Hits and hit differences do not establish binding or biological function.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-062.02.C03

Historical claim: "CTCF boundary strength"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Edit output contains motif-match, expression and contact/insulation proxy comparisons. ctcf_boundary_delta is a match-fraction difference and enhancer_hijack_risk is an expression-increase ratio, not disease hijacking or efficacy.

Source: `src/sugarcode/modules/genomegpt/core.py:237 (simulate_edit)`.

### S5-062.02.C04

Historical claim: "reorganization of local chromatin loops"

Disposition: BUILD. Status: PARTIAL.

Current scope: Edit results now compare reference/edited motif loops and contact proxies. Indels retain separate matrices without ungrounded coordinate subtraction. No biological loop reorganization is established.

Source: `src/sugarcode/modules/genomegpt/core.py:326 (compare_edit_chromatin)`.

### S5-062.03.C01

Historical claim: "differentiable proxy for loop extrusion"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A distance-power law, fixed orientation multiplier and exponential residence-time factor produce contact proxies. The inspected core.py contains no learned 3D architecture or differentiable loop-extrusion model.

Source: `src/sugarcode/modules/genomegpt/core.py:151 (contact_probability)`.

### S5-062.03.C02

Historical claim: "cohesin residence time and CTCF orientation"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A distance-power law, fixed orientation multiplier and exponential residence-time factor produce contact proxies. The inspected core.py contains no learned 3D architecture or differentiable loop-extrusion model.

Source: `src/sugarcode/modules/genomegpt/core.py:151 (contact_probability)`.

### S5-062.03.C03

Historical claim: "ectopic enhancer hijacking"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Edit output contains motif-match, expression and contact/insulation proxy comparisons. ctcf_boundary_delta is a match-fraction difference and enhancer_hijack_risk is an expression-increase ratio, not disease hijacking or efficacy.

Source: `src/sugarcode/modules/genomegpt/core.py:237 (simulate_edit)`.

### S5-062.03.C04

Historical claim: "insulation loss"

Disposition: BUILD. Status: PARTIAL.

Current scope: Edit results now include reference/edited insulation proxies and same-length bin deltas. This is not experimental insulation loss.

Source: `src/sugarcode/modules/genomegpt/core.py:326 (compare_edit_chromatin)`.

### S5-062.04.C01

Historical claim: "efficacy"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Edit output contains motif-match, expression and contact/insulation proxy comparisons. ctcf_boundary_delta is a match-fraction difference and enhancer_hijack_risk is an expression-increase ratio, not disease hijacking or efficacy.

Source: `src/sugarcode/modules/genomegpt/core.py:237 (simulate_edit)`.

### S5-062.04.C02

Historical claim: "unintended regulatory consequences"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Edit output contains motif-match, expression and contact/insulation proxy comparisons. ctcf_boundary_delta is a match-fraction difference and enhancer_hijack_risk is an expression-increase ratio, not disease hijacking or efficacy.

Source: `src/sugarcode/modules/genomegpt/core.py:237 (simulate_edit)`.

### S5-063.01

Historical claim: "Finally, GenomeGPT becomes a design engine through reinforcement learning over regulatory objectives."

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "Finally, GenomeGPT becomes a design engine through reinforcement learning over regulatory objectives." capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-063.02.C01

Historical claim: "target expression profiles"

Disposition: BUILD. Status: PARTIAL.

Current scope: Added per-cell scalar expression-delta targets and preservation tolerances for bounded single-base search. Per-gene profiles and biological target achievement remain unsupported.

Source: `src/sugarcode/modules/genomegpt/core.py:356 (propose_expression_profile_edits)`.

### S5-063.02.C02

Historical claim: "minimal sequence edits"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Exhaustive single-base search ranks an expression-error and splice-match proxy reward. It does not establish safety, chromatin stability or off-target regulatory effects. Splice results are sequence-match proxies.

Source: `src/sugarcode/modules/genomegpt/core.py:294 (propose_regulatory_edits)`.

### S5-063.02.C03

Historical claim: "synthetic regulatory elements"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "synthetic regulatory elements" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-063.02.C04

Historical claim: "off-target regulatory perturbation"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Exhaustive single-base search ranks an expression-error and splice-match proxy reward. It does not establish safety, chromatin stability or off-target regulatory effects. Splice results are sequence-match proxies.

Source: `src/sugarcode/modules/genomegpt/core.py:294 (propose_regulatory_edits)`.

### S5-063.03.C01

Historical claim: "predicted expression changes"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A fixed combination of GC, supplied/fixed cell tracks, promoter match and a contact scalar produces an expression proxy. This is not a trained or experimentally established expression profile.

Source: `src/sugarcode/modules/genomegpt/core.py:210 (expression_prediction)`.

### S5-063.03.C02

Historical claim: "chromatin stability"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Exhaustive single-base search ranks an expression-error and splice-match proxy reward. It does not establish safety, chromatin stability or off-target regulatory effects. Splice results are sequence-match proxies.

Source: `src/sugarcode/modules/genomegpt/core.py:294 (propose_regulatory_edits)`.

### S5-063.03.C03

Historical claim: "safety metrics"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Exhaustive single-base search ranks an expression-error and splice-match proxy reward. It does not establish safety, chromatin stability or off-target regulatory effects. Splice results are sequence-match proxies.

Source: `src/sugarcode/modules/genomegpt/core.py:294 (propose_regulatory_edits)`.

### S5-063.03.C04

Historical claim: "cryptic splice sites"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Exhaustive single-base search ranks an expression-error and splice-match proxy reward. It does not establish safety, chromatin stability or off-target regulatory effects. Splice results are sequence-match proxies.

Source: `src/sugarcode/modules/genomegpt/core.py:294 (propose_regulatory_edits)`.

### S5-063.03.C05

Historical claim: "oncogenic enhancer activation"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "oncogenic enhancer activation" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-063.04.C01

Historical claim: "continual learning"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "continual learning" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-063.04.C02

Historical claim: "functional genomics datasets"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "functional genomics datasets" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-063.04.C03

Historical claim: "high-fidelity"

Disposition: CORRECT. Status: UNSUPPORTED.

Current scope: The inspected src/sugarcode/modules/genomegpt/core.py contains no implementation or supplied artifact supporting the requested "high-fidelity" capability. Existing sequence statistics and heuristic proxies do not establish this claim.

Source: `src/sugarcode/modules/genomegpt/core.py:321 (genomegpt_report)`.

### S5-063.04.C04

Historical claim: "sequence"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Calculations accept a supplied DNA string and preserve motif positions within that string. No chromosome-scale throughput, coordinate provenance or long-context reasoning guarantee is established by the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-063.04.C05

Historical claim: "epigenetics"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Named cell states select fixed priors; caller-supplied scalar or per-bin tracks can override them. No cell-specific learned representation is fitted in the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:138 (epigenetic_fusion)`.

### S5-063.04.C06

Historical claim: "3D architecture"

Disposition: CORRECT. Status: PARTIAL.

Current scope: A distance-power law, fixed orientation multiplier and exponential residence-time factor produce contact proxies. The inspected core.py contains no learned 3D architecture or differentiable loop-extrusion model.

Source: `src/sugarcode/modules/genomegpt/core.py:151 (contact_probability)`.

### S5-DISC-genomegpt

Historical claim: "> **Spec vs implementation:** this file is the original aspirational product-spec\n> text. The shipped module is deterministic/statistical/mechanistic computation\n> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep\n> learning, foundation, GNN, or RL model, whatever the text below says. See\n> STATUS.md for what is actually verified."

Disposition: CORRECT. Status: PARTIAL.

Current scope: Original spec-versus-implementation banner remains unchanged. The inspected core.py contains explicit sequence statistics and heuristic proxies, not a trained foundation model. Module-specific bounds below supplement, rather than replace, that banner.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-CODEDOC-040

Historical claim: "Regulatory-motif and compositional analysis of raw sequence at scale."

Disposition: CORRECT. Status: PARTIAL.

Current scope: Calculations accept a supplied DNA string and preserve motif positions within that string. No chromosome-scale throughput, coordinate provenance or long-context reasoning guarantee is established by the inspected core.py.

Source: `src/sugarcode/modules/genomegpt/core.py:30 (analyze_sequence)`.

### S5-CODEDOC-042.C01

Historical claim: "Clinical reading of a variant inside its sequence context."

Disposition: CORRECT. Status: PARTIAL.

Current scope: The wrapper compares TF motif hits and calls a local variant helper with a context-relative coordinate. It supplies no codon context or transcript mapping and does not scan CTCF anchors in this function.

Source: `src/sugarcode/modules/genomegpt/core.py:69 (interpret_sequence_variant)`.

### S5-CODEDOC-042.C02

Historical claim: "Combines codon-level consequence with motif-disruption analysis: does the\n    change break a TF motif or CTCF anchor?"

Disposition: CORRECT. Status: PARTIAL.

Current scope: The wrapper compares TF motif hits and calls a local variant helper with a context-relative coordinate. It supplies no codon context or transcript mapping and does not scan CTCF anchors in this function.

Source: `src/sugarcode/modules/genomegpt/core.py:69 (interpret_sequence_variant)`.

### S5-CODEDOC-044.C02

Historical claim: "loop-extrusion enhancement"

Disposition: CORRECT. Status: PARTIAL.

Current scope: Convergent motif bins use a fixed orientation multiplier in a distance-decay matrix. This is a proxy enhancement, not an extrusion dynamics simulation.

Source: `src/sugarcode/modules/genomegpt/core.py:156 (reconstruct_contact_map)`.

### S5-CODEDOC-045.C02

Historical claim: "Plain distance decay with no\n    CTCF structure gives a flat profile and therefore no boundaries."

Disposition: CORRECT. Status: PARTIAL.

Current scope: In this fixed proxy matrix, absent CTCF motifs yield equal full-window scores and no local-minimum boundaries. This does not establish a general genomic property.

Source: `src/sugarcode/modules/genomegpt/core.py:166 (tad_boundaries)`.
