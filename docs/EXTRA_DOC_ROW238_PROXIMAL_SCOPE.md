# Row238 Proximal Methods

Exact description: "Handles non-smooth objectives".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact rational proximal gradient for positive diagonal quadratic plus L1.
Smooth forward gradient step at1/max(diagonal), nonsmooth soft-threshold prox,
full trace/objective and coordinate KKT residuals. Tolerance-based stopping is
not a global optimum claim. Caps8dimensions50iterations/values+-1000,
curvature>=1e-6/penalty0..1000/tolerance1e-9..1. Strict type/range checks
before conversion, no bool/hugeint/no mutation or external effects.

5PASS400 independent piecewise scalar prox minimization/fulltrace oracles,
literal forward/threshold/KKT/objective test, exact tolerance equality/caps/
nonbool/schema/hugeinteger refusals. Broad54AST52kills2equivalents: strict
threshold> or< changed to inclusive gives exactlyzero at equality, matching
existing zero branch. Own audit counts, independent audit still required.

SCOPED,literalPARTIAL. NOT_CLAIMED arbitrary nonsmooth optimization, authentic
model, all-budget convergence, scalability, external execution/runtime integration.
New native files, namespace imports, noinit. No purchase or communication.
