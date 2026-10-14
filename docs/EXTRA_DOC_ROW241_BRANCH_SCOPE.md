# Row 241 Branch and Bound
Exact description: "Prunes search space".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact binary knapsack branch-and-bound, ratio-ordered fractional relaxation
upper bounds and deterministic include-first traversal. Prunes only bounds
strictly below incumbent, preserving original-order lexicographic bit ties.
Returns optimum, weight, visited/pruned counts and pruning witnesses.
Floats mean decimal literals Fraction(str(v)). Caps sixteen items, positive
weights at least 1e-6, weights/values/capacity at most 1000, values/capacity
nonnegative. Strict nonbool/range before conversion, no mutation/effects.

Tests: tests/extra_doc/test_branch_bound241.py. Five cases, 400 independent
exhaustive subset references, literal count/bound witnesses, capacity equality,
zero values/capacity, ties, all caps and staged huge integer/type refusals.
Two own mutation survivors: strict tie comparison to inclusive changes only
identical-bit reassignment; initial incumbent bits zero->one still get replaced
by the best reachable leaf, since equality bounds are not pruned. Neither alters
returned optimum or statistics. Independent audit required.

SCOPED, literal PARTIAL. NOT_CLAIMED arbitrary integer programs, large-scale
throughput, authentic model, external execution or runtime integration.
New native files, namespace imports, no __init__.py.
