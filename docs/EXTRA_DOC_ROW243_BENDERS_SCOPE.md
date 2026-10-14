# Row 243 Benders Decomposition
Exact description: "Separates complicating variables".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact finite capacity/cost master separated from shortage recourse subproblems.
Each demand solves min penalty*y subject to y>=demand-capacity,y>=0. Recourse
dual coefficients generate a supporting affine Benders cut. Master uses all
accumulated cuts, maintains feasible incumbent, reports lower/upper gap and full
shortage/dual/cut trace. Zero gap certifies supplied finite-menu objective only.
Floats mean decimal literals Fraction(str(v)).

Caps: eighty options, twenty demands, eighty iterations, capacity/demand/penalty
0..1000 and fixed cost +-1000. Strict nonbool/range/schema before conversion,
huge integer refusals, no mutation or effects. Tests at
 tests/extra_doc/test_benders_exact243.py: four cases, 500 independent whole-menu
recourse references and supporting-cut validity checks, literal dual/cut/master
trace, monotone lower bounds, budget states, caps and refusals. One own mutation
survivor inclusive incumbent comparison only reassigns identical objective/index.
Independent audit required.

SCOPED, literal PARTIAL. NOT_CLAIMED arbitrary recourse LPs, authentic demands,
scalable master infrastructure, runtime integration or external execution.
New native files, namespace imports, no __init__.py.
