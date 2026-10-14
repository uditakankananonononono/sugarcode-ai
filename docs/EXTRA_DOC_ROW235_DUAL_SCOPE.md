# Row235 Dual Decomposition

Exact description: "Splits large problems".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Distinct standalone exact Fraction implementation decomposes positive separable
quadratic sum(0.5*a_i*x_i^2-b_i*x_i) with weighted coupling sum(c_i*x_i)=total.
Independent block argmins conditioned on shared multiplier; analytic dual
curvature solves multiplier exactly. Returns rational point/block costs/primal/
dual/gap/coupling residual. Handles signed/zero coupling coefficients (at least
one nonzero). No wrapper of existing float sum-equality decomposition.

Caps1..20blocks,a1e-6..1000,b/c/total+-1000,strictfinite nonbool numbers checked
range before finite conversion. Four tests include500 independent two-block
scalar equality-elimination reference optima, signed weighted handKKT, inactive
block, full caps/schema/type/hugeintegerrefusals/no mutation. Broad42/42own AST
arithmetic/comparison/constants/boolean/all-any mutants killed.

SCOPED exact finite weighted-equality quadratic decomposition,literalPARTIAL.
NOT_CLAIMED arbitrary optimizer, distributed infrastructure or large-scale
throughput, model validity, external effects or runtime integration. Coupling
coefficients must use compatible units. No float optimization. Independent audit
still required. Existing solvers untouched.

Native Sugarcode port: reviewed source/tests, namespace imports, new files only,
no __init__.py. Fresh4PASS500referenceoracles and42AST42kills. No prior Atlas
runtime-placement claim carried over. Earlier touched row, not a new scope count.
