# Row 239 Frank-Wolfe Algorithm

Exact description: "Solves constrained problems".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact rational Frank-Wolfe for positive diagonal quadratic objectives on the
unit simplex. Linear oracle evaluates every vertex gradient score, deterministic
index ties. Exact line search on the feasible segment; full gradient, direction,
gap, step, point and objective trace. Computed gap tolerance stopping, no exact
finite-budget optimum claim. Floats mean decimal literal Fraction(str(v)).

Caps: eight dimensions, thirty iterations, curvature 1e-6..1000, linear values
+-1000, initial coordinates 0..1 with exact sum one, tolerance 1e-9..1. Strict
nonbool and range checks before conversion, huge integer refusals, no mutation.
Tests at tests/extra_doc/test_frank_wolfe239.py: four cases and 400 independent
whole-vertex score/segment quadratic reference oracles, hand line search,
feasibility, monotone objective, full-step/tie/tolerance equality, all caps and
staged refusals. Independent audit required.

SCOPED, literal PARTIAL. NOT_CLAIMED arbitrary constraints, authentic model,
finite-budget optimum, scalability, runtime integration or external execution.
New native files, namespace imports, no __init__.py. No external effects.
