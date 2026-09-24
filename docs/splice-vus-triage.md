# splice-vus-triage

This command-line tool scores splice-region SNVs: donor +3..+6 and acceptor -3..-14. It uses:
- a ClinVar-trained CNN (8-channel ref+alt one-hot plus PWM features)
- SpliceAI, optional
- a PPV calibrated from gene-grouped cross-validation

Install:
- `pip install sugarcode-ai[splice]` for the CNN only
- `pip install sugarcode-ai[splice_full]` to add SpliceAI

Run: `splice-vus-triage variants.tsv --genome hg38.2bit [--spliceai] [--prior 0.03]`

Input is a TSV with columns name, chrom, pos, ref, alt (GRCh38, 1-based). The name must carry the HGVS intronic offset, e.g. `NM_000398.7(CYB5R3):c.463+4G>A`. If you don't have a genome file, give 81-nt transcript-oriented `ref_ctx`/`alt_ctx` columns instead.

Output columns:
- cnn probability
- SpliceAI max delta score
- CNN calibration bin
- PPV at the given prior
- evidence tier

Evidence and limits (all in mega27-01 `discovery/splice_region_vus/`):
- CNN, gene-grouped CV: AUROC 0.936 (cv_results.json).
- SpliceAI is stronger: 0.9775 vs 0.929, n=757 (headtohead_interim.json). Use SpliceAI as the primary score.
- The PPV comes from sensitivity and FPR at each CNN threshold (cnn_calibration.json), assuming the prior you set.
- This is research triage only, not an ACMG classification.
- Variants whose strand can't be inferred from a canonical GT/AG are reported as errors.

## Model (v2)
When `maxentpy` is installed, scoring uses a logistic model on PWM plus MaxEntScan features. In gene-grouped 5-fold CV on 9,235 ClinVar splice-region variants it reached AUROC 0.9674, vs 0.9635 for MaxEntScan alone and 0.9355 for the CNN (mega27-01 discovery/splice_region_vus/cv_results_me.json). Without maxentpy it falls back to the CNN.
