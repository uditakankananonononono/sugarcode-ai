# PBS duplex build-out, 2026-10-07

## Checked source

- https://biopython.org/docs/latest/api/Bio.SeqUtils.MeltingTemp.html
  Tm_NN documents the Sugimoto 1995 RNA/DNA table R_DNA_NN1, says the input
  strand must be RNA, explains individual strand concentration and salt methods.
- https://raw.githubusercontent.com/biopython/biopython/master/Bio/SeqUtils/MeltingTemp.py
  Retrieved on 2026-10-07; the R_DNA_NN1 literal contains 16 oriented hybrid
  dinucleotide H/S values and general initiation (1.9 kcal/mol, -3.9 cal/mol/K).
  All terminal and symmetry terms are zero. Parameters transcribed as data, not
  a new dependency. The source table uses T to denote RNA U.

## Implemented domain and caveats

Perfect unmodified RNA PBS/complementary DNA duplex only; PBS encoded as DNA
letters in RNA 5'->3' orientation, length 8-25 bases. H/S sum includes initiation.
The implemented salt entropy term is 0.368*(length-1)*ln([Na+] in M).
This is Biopython method 5, a DNA-derived SantaLucia 1998 approximation, not a
PBS-specific or independently validated RNA/DNA salt model.

Each distinct strand has total C (default 25 nM). Tm uses C/2, corresponding to
total oligo concentration divided by four. No palindrome symmetry term: RNA
and DNA are different species. K=exp(-deltaG/RT); fraction f follows
f=K*C*(1-f)^2. A stable quadratic evaluation avoids overflow at strong binding.
At Tm the solution is f=0.5. Concentration is explicit, not intracellular fit.

Regression demonstrates code behavior, hand-summed hybrid H/S and mass-action
consistency, not agreement with prime-edit assays. Automated architecture ranking
can consume the new fraction; its score weights remain uncalibrated. Legacy
PBS selection and pbs_tm_c remain Wallace-based. Repair and outcome distributions
remain unfitted. No clinical/spec validation is claimed.

## Evidence

- prime-pbs-before-2026-10-07.txt: 15 failing, 3 passing initial canaries.
- prime-pbs-after-2026-10-07.txt: 70 passed, 2 skipped targeted prime tests.
- prime-pbs-regression-batch-{1,2,3,4}.txt: full tests/ in four isolated processes,
  2,480 passed, 15 skipped, 0 failed over 341 test files.
