# Builder claims (append-only; one line per builder)

| builder | branch | component claimed | status |
|---|---|---|---|
| lane lead | (main lane) | provider-agnostic model layer (free local default; Fugu/Inkling optional endpoints) | claimed via main |
| PB6 | pb6 | crispr_opt Rule Set 2 (Fusi/Doench 2016 Azimuth V3) portable on-target scoring: pure-numpy port of the published BSD-3-Clause model + featurizer, validated against Microsoft's saved-model test fixture; closes the STATUS.md "Missing" item | shipped on pb6 |
| PB6 | pb6 | crisprscan_score (Moreno-Mateos 2015 CRISPRscan) promotion: orphaned published linear sgRNA activity model moved into src/, byte-exact vendored coefficients (crisprVerse/crisprScore pinned commit, SHA-256 verified), registered as 89th module | shipped on pb6 |
| PB6 | pb6 | acmg_bayesian: Tavtigian 2018 Bayesian ACMG/AMP classifier (exact 350^(1/2^k) odds, BA1 stand-alone override, paper Table 2/3 rows as fixtures) with optional live ClinVar/PubMed context; fixed rebuild of the unpromoted clinical_evidence_fusion orphan, registered as 90th module | shipped on pb6 |
| PB6 | pb6 | rna_nussinov: Nussinov-Jacobson 1980 max base-pair RNA secondary structure (DP + traceback, min loop, G-U option, dot-bracket, pair lists, exact optimal-structure count, stats), hand-computed fixtures + independent brute-force verifier, registered as 91st module | shipped on pb6 |
| PB6 | pb6 | profile_hmm: Durbin Ch. 5 profile HMM from multiple alignments (match/insert/delete, pseudocounts), Viterbi state path, Forward score, log-odds; hand-computed exact-fraction fixtures + independent brute-force path enumerator, registered as 92nd module | shipped on pb6 |
| PB6 | pb6 | profile_hmm Baum-Welch extension: forward-backward EM on unaligned sequences (alignment-built or random-seeded start, ML or Dirichlet MAP), LL-delta convergence, held-out log-likelihood; hand-computed E/M steps + brute-force exact posterior counts | shipped on pb6 |
