# Genome sequence stack: bounded code and claim dispositions

Base: `692143ee3999b08e816e0b90ef3cd39f3c030763`.

103 supplied rows were inspected individually. None had pre_verdict VERIFIED,
so none were excluded. Local dispositions: 5 BUILD, 98 CORRECT. Final labels:
0 COMPLETE, 78 PARTIAL, 25 UNSUPPORTED. Independent reproduction fields remain
empty. No model, wet-lab, clinical, deployment or externally sourced-data claim
is established by this patch.

## Bounded additions

- Per-bin scalar track arrays now pass through epigenetic_fusion,
  expression_prediction and cell_state_contrast. Values and array lengths are
  checked; no inferred ATAC/ChIP signal is produced.
- simulate_edit now returns reference/edited convergent-motif loop lists,
  contact matrices, boundary lists and full-window insulation proxies. Same-length
  substitutions compare common bins; indels do not subtract unaligned coordinates.
  Comparisons are limited to 512 contact bins. This is not a learned 3D model.
- propose_expression_profile_edits exhaustively searches one-base substitutions
  under supplied per-cell scalar target/tolerance and preservation constraints.
  It returns only candidates satisfying those proxy constraints, not per-gene
  profiles or biological target achievement. Limits: 1000 bases, eight cells,
  100 output candidates. No reinforcement learning or off-target genomic check.
- delta_embedding now assigns zero cosine change to identical vectors, including
  short sequences whose four-mer frequency vectors are all zero. One zero vector
  and one nonzero vector use the stated value 1 convention.

The five BUILD rows map to these additions. Existing functions supporting narrower
claims were not counted as fresh builds merely because their candidate tests pass.
The rest receive row-specific wording and PARTIAL/UNSUPPORTED reasons in the CSV
and spec correction section. Original aspirational text and the banner remain
unchanged as historical source; the new section supersedes the named claims only.

## Regression evidence

The four pre-existing focused GenomeGPT suites passed 41 cases before changes.
Twelve new cases failed against the original source. The same unchanged new tests
failed again when core.py was restored exactly from the base commit. After source
restoration to the patch version, all 53 focused cases passed. Existing tests were
not edited or loosened. Logs:

- failing-baseline.txt
- failing-code-reverted.txt
- passing-regression.txt

The failures include two zero-vector semantics, vector-track integration and
shape/value rejection, cell-state conditioning, edit contact/insulation output,
indel coordinate non-comparison, target feasibility and search-budget rejection.
These logs are local evidence, not independent reproduction. No independent
identity or reproduction commit is supplied by this patch.

No network, paid service, external dataset retrieval, patient data, model-training
runtime or laboratory execution is added. Absence statements in the dispositions
are limited to inspected GenomeGPT core.py or specifically named wrappers.
