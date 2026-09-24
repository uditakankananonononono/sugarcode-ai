
## chem_descriptors (2026-09-24, branch pb6)
- `src/sugarcode/modules/chem_descriptors/data/periodic_table.json` (sha256
  459ca66f1511a5e584c061982ab6f5f51e950d8d3687270324cdbce15ab3e644): element
  average weights, most-common-isotope and isotope masses parsed by
  `vendor_atomic_data.py` from RDKit `Code/GraphMol/atomic_data.cpp` at tag
  Release_2024_09_6 (commit b3076c77284b9a8b9d5ef78957ee067037f373a8; source
  sha256 7f9cee6e430b60d303a0a7fa9e33c45e5c529ee204f86afeab6a20f68b6b0631),
  https://raw.githubusercontent.com/rdkit/rdkit/Release_2024_09_6/Code/GraphMol/atomic_data.cpp.
  BSD-3-Clause; license copied to data/RDKIT_LICENSE.txt and
  LICENSES/RDKIT-BSD-3-CLAUSE.txt (sha256 daeb8d19...9fca30).
- HBD/HBA SMARTS and Strict rotatable-bond definitions re-implemented (not
  copied) from RDKit `Code/GraphMol/Descriptors/Lipinski.cpp` at the same tag
  (sha256 4a5b49e7007b65b4375e3252ef37b0a4a904a54b89e7c3fbdd2b19208a8f2b4f).
- TPSA fragment contributions: Ertl, Rohde & Selzer 2000, J Med Chem 43:3714
  (PMID 11020286, doi 10.1021/jm000942e), rule order as coded in RDKit
  `Code/GraphMol/Descriptors/MolSurf.cpp` at the same tag (sha256
  3496f0251bc07ac5a49c21fdde9262cb8c3d4b3c917c0b1d35b7f863c6b3296b).
- Filters: Lipinski et al. 2001, Adv Drug Deliv Rev 46:3 (PMID 11259830, doi
  10.1016/s0169-409x(00)00129-0); Veber et al. 2002, J Med Chem 45:2615 (PMID
  12036371, doi 10.1021/jm020017n).
- `tests/fixtures/chem_descriptors_oracle.json` (sha256
  89d947403cb10baee294d50145519db65576aaa55b821bb304b879ddf6c9f7b0): RDKit
  2024.09.6 descriptor values plus PubChem PUG-REST properties (formula, MW,
  exact mass, TPSA, XLogP, SMILES; fetched 2026-09-24) for 66 named compounds,
  and RDKit values for 60 stress SMILES. Regenerate with
  scripts/chem_descriptors_oracle_ladder.py and scripts/chem_descriptors_oracle_stress.py.

## profile_hmm (2026-09-24, branch pb6)

- Topology and algorithms: Durbin R, Eddy SR, Krogh A, Mitchison G, "Biological
  Sequence Analysis: Probabilistic Models of Proteins and Nucleic Acids",
  Cambridge University Press 1998, ISBN 978-0-521-62971-3, DOI
  10.1017/CBO9780511790492 (bibliographic data checked on the publisher's page,
  https://www.cambridge.org/core/books/biological-sequence-analysis/921BB7B78B745198829EF96BC7E0F29D,
  2026-09-24). Chapter 5 "Profile HMMs for sequence families": Fig. 5.2
  architecture (Begin, M/I/D states, End; nine transition types), model
  construction from an alignment with match columns by gap fraction and
  pseudocounts, Viterbi and Forward recurrences.
- The book is not freely available, so unlike the Tavtigian module there is no
  text hash. The recurrences are written from Chapter 5 and the original
  Krogh A, Brown M, Mian IS, Sjolander K, Haussler D, J Mol Biol
  1994;235:1501-1531, DOI 10.1006/jmbi.1994.1104, PMID 8107089 (checked on
  PubMed). Correctness does not rest on the citation: every score is checked
  against exhaustive path enumeration.
- No vendored data or parameter tables. Fixtures are hand-computed exact
  fractions (derivations in tests/test_profile_hmm.py).
- Baum-Welch training (training.py): Durbin et al. Chapter 3.3 expected-count
  equations (forward-backward, with the silent-state variant for delete
  states) applied to the Chapter 5 profile HMM. Pseudocounts act as a symmetric
  Dirichlet prior (MAP-EM). Hand-computed E/M fixtures are in
  tests/test_profile_hmm_training.py; exact posterior counts come from
  brute-force path enumeration.

## rna_nussinov (2026-09-24, branch pb6)

- Algorithm: Nussinov R, Jacobson AB, "Fast algorithm for predicting the
  secondary structure of single-stranded RNA", Proc Natl Acad Sci USA
  1980;77(11):6309-6313, DOI 10.1073/pnas.77.11.6309, PMID 6161375, PMC350273
  (citation checked against NCBI PubMed esummary, 2026-09-24).
- No vendored data or parameter tables. Allowed pairs are the Watson-Crick set
  plus optional G-U wobble; min_loop is a caller parameter (default 3).
- Fixtures are hand-computed (derivations in tests/test_rna_nussinov.py) and
  cross-checked by an in-module brute-force enumerator that shares no code
  with the DP.

## acmg_bayesian model constants and fixtures (2026-09-24, branch pb6)

- Source: Tavtigian SV, Greenblatt MS, Harrison SM, et al. "Modeling the ACMG/AMP
  variant classification guidelines as a Bayesian classification framework."
  Genet Med 2018;20:1054-1060. DOI 10.1038/gim.2017.210, PMID 29300386, free
  author manuscript PMC6336098 (NIHMS915467). A paper, not a code repository, so
  there is no commit to pin; the fetched full text is hash-pinned instead:
  BioC JSON from
  https://www.ncbi.nlm.nih.gov/research/bionlp/RESTful/pmcoa.cgi/BioC_json/PMC6336098/unicode
  SHA-256 `6af181739e6d462e316b2489702974eca5f95990ebe25cef2baa505f0dab543d`
  (81,882 bytes; fetched twice on 2026-09-24, identical).
- Constants taken from that text: OP_VSt = 350; exponent X = 2 (so strong
  350^(1/2) = 18.7, moderate 350^(1/4) = 4.3, supporting 350^(1/8) = 2.08, as
  printed); benign categories "assigned reciprocal OP"; Prior_P = 0.10; bands
  Pathogenic > 0.99, Likely pathogenic 0.90-0.99, Likely benign 0.001-<0.10,
  Benign < 0.001; "OP of 81 are the exact odds required to convert a Prior_P of
  0.10 to a Post_P of 0.90" (basis for placing 6 points = 350^0.75 at the LP
  floor); BA1 excluded "because it is used as absolute evidence that a variant is
  benign, irrespective of other evidence, which is contrary to Bayesian
  reasoning" (basis for the stand-alone override). No constant was fitted or
  invented; the orphan's BA1 odds of 1/1000 had no source and were dropped.
- Fixtures in `tests/test_acmg_bayesian.py`: the 17 combining-rule rows of the
  paper's Table 2 and the 4 mixed-evidence rows of Table 3, with the printed
  combined odds and posterior (e.g. Path (ia) 6,548 / 0.999, Likely Path (ii)-(vi)
  81 / 0.900, Benign (ii) 0.0028 / 0.00032, two strong + BS1 18.7 / 0.675).
  Criterion codes per row follow the ACMG/AMP 2015 combining rules the rows name.
- Recorded NCBI E-utilities responses in `tests/fixtures/acmg_ncbi_cache/`
  (fetched live 2026-09-24, no API key; request URLs kept in the .json sidecars):
  ClinVar esearch `BRCA1[gene] AND "c.68_69del"` -> IDs 54425, 17662; esummary of
  both (17662 = NM_007294.4(BRCA1):c.68_69del, Pathogenic, reviewed by expert
  panel); PubMed esearch + efetch for the orphan-style literature query.
  Body SHA-256:
  - esearch clinvar `c23ffa81134f2538120b0112014c70b7fb3c5e4ca1d124ecb4440e75d4d411e7`
  - esummary clinvar `1c7a773a756708bb6ce3d61a1a687cdb2c3a850545c218b434e2fb07be3c3e54`
  - esearch pubmed `1a07d7ce910a931f9202b6ce1a59585856d174e09252c9bb7936c8aacd00f93c`
  - efetch pubmed `f28f16d8e490c67ea669a2117eff8f560916c14e68942397de8d541f0b9bc57f`
- NCBI client code carried over from orphan commit b78b943 (module-local,
  urllib only), with two fixes: ClinVar-style HGVS normalization and exact-title
  matching (unrelated search hits are no longer summarized).

## crisprscan_score model data (2026-09-24, branch pb6)

- `src/sugarcode/modules/crisprscan_score/data/coefficients.csv`: the 91
  position-specific mono/di-nucleotide coefficients + intercept of the
  published CRISPRscan / Moreno-Mateos 2015 linear sgRNA activity model
  (Nature Methods 12:982-988, DOI 10.1038/nmeth.3543). Byte-identical to the
  machine-readable artifact `inst/crisprscan/crisprscan_coefficients.csv` in
  https://github.com/crisprVerse/crisprScore at pinned commit
  `cbd6f9f60dc7fb50d14b90485b9561d582caf21e` (re-verified 2026-09-24: SHA-256
  `6e3f1bbfd58e5426651a15cfd0db6ac2094e0a93158dc51639b5929fc9ced5a4`, 93
  lines, diff-clean against the raw URL). No coefficient was refit or altered.
- Parity fixtures in `tests/test_crisprscan_score.py` (5 sequences, expected
  scores 0.531/0.531/0.450/0.712/0.618) are copied verbatim from the reference
  repo's `tests/testthat/test-crisprscan.R` at the same pinned commit.
- Scoring semantics re-verified against the reference implementation
  `R/getCRISPRscanScores.R`: one-based motif start positions, additive
  intercept + matched-feature sum, canonical GG required at 1-based positions
  28-29, ambiguous bases score Missing (never fabricated).
- Package recovered from orphaned commit 35e0995 (unpackaged top-level tree,
  deleted in the audit-fix drop) and promoted into `src/` unchanged.

## crispr_opt Rule Set 2 model data (2026-09-24, branch pb6)

- `src/sugarcode/modules/crispr_opt/data/rule_set_2_model.json`: trained
  Azimuth V3 / V3-nopos gradient-boosted trees (Fusi & Doench 2016), extracted
  from `azimuth/saved_models/V3_model_{full,nopos}.pickle` in
  https://github.com/MicrosoftResearch/Azimuth (BSD-3-Clause, (c) Microsoft;
  license text in LICENSES/AZIMUTH-BSD-3-CLAUSE.txt). No weights were refit or
  altered: prediction equality vs the original saved models is proven against
  Microsoft's own fixture below (max abs error 5e-10).
- `tests/fixtures/azimuth_1000guides.csv`: verbatim copy of
  `azimuth/tests/1000guides.csv` (947 synthetic 30mers + reference scores
  generated by Microsoft in Nov 2016). Used only as a test fixture.
- SantaLucia (1998) DNA_NN3 thermodynamic table values are republished
  constants (Allawi & SantaLucia, Biochemistry 36:10581-10594), matching
  Biopython's table; the Tm implementation in rule_set_2.py is ours.

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

## U12 acceptor PWM column 14 (drop 55, 2026-09-22)
The intronIC export carried no downstream flank, so both U12 acceptor matrices shipped with a
uniform 0.25 placeholder at column 14 (+1 exonic). Replaced with the U2 acceptor +1 column
(1,170-junction harvest) as a documented approximation: the exonic +1 base preference is
spliceosome-independent. Verified no U12-golden fixture case sits at acceptor +1 exonic, so no
existing delta changes; U2 matrix untouched.
