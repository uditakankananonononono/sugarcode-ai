# Row226 Convex Optimization

Exact description: "Solves tractable problems".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact strictly convex positive diagonal quadratic minimizer on nonnegative
sum-equality simplex. Enumerates active sets of increasing cardinality and
checks primal/dual/complementarity KKT in the supplied model. Unique solution,
objective, multipliers, support and checked-set count returned. Eight dimensions
maximum, coefficients at most1000, positive curvature/total at least1e-6.
Schema and numeric range checks precede conversion and scan where applicable.

4PASS500 independent sorted-breakpoint waterfill reference oracles, hand KKT,
active sets/counts, bounds, nonbool, huge integers, no mutation. Broad51 AST
mutants45 killed6 equivalent within admissible domain: ids10,21,22 alter final
KKT checks that always hold for constructed optimum; id16 n+1->n+2 includes an
empty extra combination level never reached after solution; ids29/39 relax
positivity guard. A set containing zero/negative coordinates cannot be the first
accepted set because its smaller positive support was already enumerated and
accepted. This argument relies on strict positive diagonal, positive total,
increasing support cardinality and independent inactive-dual guard. Counts are
self-audit only, not independent reviewer counts.

SCOPED, literalPARTIAL, NOT_CLAIMED arbitrary convex optimization, authentic
models/constraints, external execution or runtime integration. New native files,
namespace imports, no __init__.py. No external effects. Audit required.
