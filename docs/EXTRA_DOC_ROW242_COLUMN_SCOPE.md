# Row 242 Column Generation
Exact description: "Handles many variables".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact finite-column LP for convex mixtures with unit total weight and one
coordinate equality. Restricted master starts with hull extremes. Enumerates
supporting dual lines, recovers one/two-column primal mixtures, prices every
supplied column by reduced cost and adds the lowest negative one. Full active
menu, primal weights, objective, dual and pricing trace. No implicit column
oracle or large-variable throughput claim. Floats mean Fraction(str(v)).

Caps: 2..80 columns, 1..80 iterations, coordinates/costs/target +-1000. Requires
nondegenerate coordinate hull containing target. Strict schema/nonbool/range
before conversion, huge integer refusals, no mutation/external effects.
Tests: tests/extra_doc/test_column_exact242.py, four cases, 400 independent
all-column primal mixture LP reference optima, per-step primal/dual equality,
feasibility, reduced cost pricing and objective improvement, literal entering
column, budget state, caps and staged refusals.

Own broad mutation survivors: mixture filter conjunction->disjunction, lower
endpoint inclusion, and candidate basis tuple-key index0->1 all remain
UNVERIFIED. No equivalence claim: objective correctness alone does not prove
exact basis/weight tie behavior. No all-mutants-killed claim. Independent audit
required before merge.

SCOPED, literal PARTIAL. NOT_CLAIMED implicit infinite columns, large-variable
scalability, authentic model, runtime integration or external execution.
New native files, namespace imports, no __init__.py.
