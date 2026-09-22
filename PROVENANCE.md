
## Branch-point data (drop 50 groundwork, 2026-09-22)
- `src/sugarcode/bio/data/branchpoints/leman_rnaseq_bp.txt` — 103,972 experimentally supported
  RNA-seq branch points (hg19), `data/RNAseqBP.txt` from Leman et al. 2020, BMC Genomics 21:97
  ("Assessment of branch point prediction tools to predict physiological branch points and their
  alteration by variants", doi.org/10.1186/s12864-020-6484-5), vendored verbatim from
  https://raw.githubusercontent.com/raphaelleman/BenchmarkBPprediction/master/data/RNAseqBP.txt
  (SHA-256 0c0b58ce81470254eba8f918df3d486d89da55a14331430885fbb4cedbcbc51b). Compiles the
  Mercer et al. 2015 (Genome Res 25:290-303) laSSO/CaptureSeq branch-point lineage.
  Mercer GEO GSE53328 carries bigWig tracks only (2.7 GB RAW tar, no BED); the genome.cshlp.org
  supplemental index 404s - the Leman redistribution is the verifiable verbatim path.
- `src/sugarcode/bio/data/branchpoints/leman_variant_bp.txt` — 120 experimentally assayed
  branch-point-region variants with functional readouts (minigene/RT-PCR; class_effect 0 = no
  effect n=82, 1 = splicing defect n=38), `data/variantBP.txt` from the same repo. Variants sit
  at c.-44..-18 (median -25) relative to the 3' splice site; cNomen is cDNA-based and therefore
  build-independent.
