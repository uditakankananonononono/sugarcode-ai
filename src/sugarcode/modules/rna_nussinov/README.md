# RNA Nussinov

Maximum base-pair RNA secondary structure by the Nussinov-Jacobson dynamic
program (Proc Natl Acad Sci USA 1980;77(11):6309-6313, DOI
10.1073/pnas.77.11.6309, PMID 6161375). Pure algorithm: no energy
parameters, no external tables.

What it is not: a thermodynamic (minimum free energy) predictor. It maximizes
the number of allowed pairs in a nested, pseudoknot-free structure. Real RNA
folds depend on stacking and loop energies, which this model does not have.

```python
from sugarcode.modules.rna_nussinov import fold, optimal_structures, brute_force

r = fold("GGGAAACCC", min_loop=3)          # allow_gu=True by default
r["dot_bracket"]              # '(((...)))'
r["pairs"]                    # [[0, 8], [1, 7], [2, 6]]   (pairs_1based also given)
r["optimal_structure_count"]  # 1  (exact count of distinct optimal structures)
r["stats"]                    # pair types GC/AU/GU, stems, hairpins, depth, paired fraction

optimal_structures("GGGAAACCC", min_loop=4)  # all 5 two-pair optima
brute_force("GGGAAACCC", min_loop=4)         # independent exhaustive check (n <= 20)
```

- `min_loop`: minimum unpaired bases enclosed by any pair (default 3).
- `allow_gu`: include G-U wobble pairs (default True). T is read as U.
- The recurrence is unambiguous (split on the fate of the first base), so the
  same tables give an exact count of optimal structures and a full list of them.
- Traceback tie-break: leave a base unpaired when that is optimal, otherwise
  pair it with the nearest optimal partner.
- `evaluate_structure(seq, dot_bracket)` checks any structure against the
  pair and loop rules and reports violations.
- O(n^3) time, O(n^2) memory; default length cap 2000 (about 4-5 s at n = 1000).
  Optimal-structure counting is on by default up to length 400.

Verification: hand-computed fixtures on small RNAs, plus an exhaustive
brute-force verifier (backtracking over compatible pair sets, no DP) on 250
random short sequences with random min_loop and G-U settings. The max pair
count, exact number of optima, full set of optima, and traceback membership all
match. Also agrees with the separate Nussinov helper inside the riboswitch
module on random sequences.
