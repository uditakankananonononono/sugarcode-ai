# Row228 Gradient Descent

Exact description: "Follows steepest descent".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Actual iterative steepest descent for supplied SPD quadratic
0.5*x^T*A*x + b^T*x. Negative full gradient direction, exact quadratic line
search alpha=(g^T*g)/(g^T*A*g), objective/point/step history, Euclidean gradient
stopping norm, explicit budget-exhaustion state. Symmetry and exact rational
LDL positive pivots validate the supplied quadratic before iteration. New native Sugarcode standalone files; namespace import, no __init__.py. NOT_CLAIMED docstring retained.

Caps1..8 dimensions,100iterations,coefficients/initial+-1000,tolerance1e-10..1,
LDL pivots at least1e-6. Strict nonbool numbers, square input, caps before scan,
no caller mutation. 12 pytest cases include250 independent Decimal first-step and
closed-form2x2optimum references, asymmetric hand trace, zero-gradient/tolerance
boundary/budget/non-SPD/near-pivot/type/schema/cap refusals,3D Schur reference.
Numerical-fault injection pins defensive curvature/iterate refusals; these do
not establish that natural inputs can reach those numerical failures.

BroadAST58mutants:57killed; one retained equivalent range(i+1,d)->range(i-1,d)
only writes unused upper/diagonal entries in lower dictionaries while all
strict lower entries used by subsequent LDL pivots remain identical. No claim
that every generated mutant is killed. Initial real test gaps were pinned.

SCOPED supplied SPD quadratic solver, literalPARTIAL. Floating iteration not
exact arithmetic; no arbitrary nonlinear/global-model claim, external execution,
provenance/authentication/persistence/runtime integration. Objective units and
axis scaling supplied by caller. Independent audit still required.

v2: FLOAT docstring states IEEE754 descent and computed-norm tolerance contract
plainly. Exact rational arithmetic is limited to the supplied-input LDL gate,
not optimization. Bounds/type checks precede isfinite/float conversion; huge
positive/negative integers are refused at every matrix, linear, initial and
tolerance input. Synthetic defensive fault checks establish only branch behavior,
never reachability or unreachability for naturally admitted data.

Native port re-tested:12PASS,250 independent Decimal references, fresh58AST
mutants57kills1equivalent. No prior Atlas runtime placement claim is carried over.
