# Row 235 Dual Decomposition

Exact description: "Splits large problems".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Standalone exact separable quadratic decomposition:
sum(0.5*a_i*x_i^2-b_i*x_i), with weighted equality sum(c_i*x_i)=total.
Independent block argmins share a dual multiplier. Analytic dual curvature
solves that multiplier, returning point, block costs, primal objective, dual
bound, gap and coupling residual. Signed and zero coupling coefficients are
allowed, with at least one nonzero. Floats are read as decimal literal
Fraction(str(v)): 0.1 means 1/10, not its binary floating-point expansion.

Caps: 1..20 blocks, curvature 1e-6..1000, linear/coupling/total +-1000.
Strict nonbool type and range checks precede conversion, including huge integer
refusals. No caller mutation. Tests use the same tests/extra_doc/ convention as
other native rows: tests/extra_doc/test_dual_exact235.py. Four cases cover 500
independent two-block equality-elimination optima, weighted signed hand KKT,
inactive blocks, caps, schema, types, numeric endpoints and no mutation.

SCOPED exact finite weighted-equality quadratic decomposition, literal PARTIAL.
NOT_CLAIMED arbitrary optimization, distributed infrastructure, large-scale
throughput, authentic model or runtime integration. Coupling coefficients must
use compatible units. No float optimization or external effects. New native
Sugarcode files, namespace imports, no __init__.py. No prior Atlas runtime
placement claim carried over. Independent audit required.
