# Row237 Coordinate Descent

Exact description: "Optimizes one variable at a time".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Distinct standalone exact Fraction cyclic coordinate minimization of supplied
SPD quadratic0.5*x^T*A*x-b^T*x. Each step solves one scalar quadratic slice,
uses already-updated coordinates, leaves others unchanged. Exact rational
point/objective trace, gradient infinity norm and tolerance stopping state.
Exact rational LDL input gate, not wrapper of existing float L1 coordinate code.

Caps1..8dimensions/30sweeps/matrix+linear+initial+-1000/tolerance1e-9..1,
LDL pivots>=1e-6. Strict types/ranges before finite conversion, hugeinteger
refusals, no caller mutation. Four tests include350 independent scalar slice
reference sequences, asymmetric hand two-step objective/gradient, monotonic
objective, tolerance equality, closed-form optimum, all cap/type/schema/SPD/
symmetry/hugeinteger refusal stages and3D Schur gate checks.

Broad49AST48killed1equivalent extra-unused-LDL-write survivor: i+1 to i-1
adds only upper/diagonal dictionary entries never read by strict-lower pivots.
A timed-out mutation run left a mutant; restored formula, baseline PASS, reran
all49 in smaller batches with restoration and PASS baseline gates.

SCOPED exact finite SPD quadratic coordinate solver,literalPARTIAL. NOT_CLAIMED
arbitrary objective, finite-budget exact global optimum, authentic model,
real-world/distributed execution or runtime integration. Tolerance applies
only exact supplied-model gradient infinity norm. Units/scaling caller-supplied.
No external effects. Independent audit required.
