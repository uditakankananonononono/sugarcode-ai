# Row236 ADMM

Exact description: "Alternates between subproblems".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Distinct standalone exact rational ADMM minimizes positive diagonal quadratic
plus L1 penalty via x=z split. Each iteration solves independent quadratic x
subproblems, soft-threshold z subproblem, updates scaled dual u. Full rational
x/z/u/primal/dual residual trace, final objective and KKT infinity norm returned.
Absolute primal/dual infinity residuals <= tolerance give explicit stopping
state, not an exact optimality claim. Existing numpy full-matrix ADMM untouched.

Caps1..8dims/30iterations,diagonal/rho1e-6..1000,linear/initial+-1000,
penalty0..1000,tolerance1e-9..1. Strict range/type checks before finite conversion,
including huge integers; no caller mutation. Rational fractions preserve
supplied decimal values. Small iteration cap bounds fraction growth/work.
Six tests include300 independent scalar piecewise subproblem trace oracles,
asymmetric two-axis hand step/objective/KKT, threshold equality/zero penalty,
residual-equality stopping pins, all caps/types/shapes/hugeinteger refusal paths.
Broad65AST:63killed,2equivalent soft-threshold > to >= and < to <= survivors:
at equality both branch formulas and zero branch return exactly0. Recorded,
not falsely counted killed. Independent audit still required.

SCOPED diagonal quadratic L1 ADMM,literalPARTIAL. NOT_CLAIMED arbitrary convex
solver, distributed infrastructure, model truth, finite-budget convergence
or real-world execution/runtime integration. Unit compatibility caller-supplied;
no external effects. This is not a wrapper.

Native Sugarcode port: reviewed source/tests, new files/namespace imports/noinit.
Fresh6PASS300referenceoracles and65AST63kills2threshold equivalents. No Atlas
runtime-placement claim carried over, no new touched-row count for this port.
