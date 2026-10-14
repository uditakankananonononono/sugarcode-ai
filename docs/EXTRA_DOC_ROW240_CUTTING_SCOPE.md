# Row 240 Cutting Plane Methods

Exact description: "Iteratively refines approximations".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact constraint generation on supplied convex scalar max-affine objectives.
Starts with one plane, solves the restricted epigraph LP using endpoints and
active-plane intersections. Full-menu separation adds the worst omitted plane.
Reports each lower bound, true objective, gap, separating cut and active set.
Zero gap certifies the optimum of the supplied interval/model. Budget exhaustion
is not certified. Floats mean decimal literals Fraction(str(v)).

Caps: forty planes, forty iterations, slope/intercept/bounds +-1000. Strict
nonbool, schema and range checks before conversion, no mutation or effects.
Tests: tests/extra_doc/test_cutting_exact240.py, four cases, 500 independent
full-plane pair-intersection LP references, literal separating-cut refinement,
monotone lower bounds, budget state, ties, caps and staged refusals. Two own
mutation survivors excluding endpoint intersections are equivalent because
both endpoints are already included unconditionally. Independent audit required.

SCOPED, literal PARTIAL. NOT_CLAIMED arbitrary continuous cutting oracle,
authentic model, scalable LP infrastructure, runtime integration or execution.
New native files, namespace imports, no __init__.py.
