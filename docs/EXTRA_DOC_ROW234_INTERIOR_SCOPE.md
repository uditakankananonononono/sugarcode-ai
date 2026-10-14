# Row234 Interior Point Methods

Exact description: "Handles inequality constraints".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

FLOAT separable positive quadratic optimization under supplied strict box
inequalities. Positive decreasing log-barrier path, diagonal Newton derivative/
Hessian, fraction-to-boundary cap and bounded Armijo backtracking. Tracks each
barrier objective/gradient/Hessian/direction/step and primal slacks. No exact
optimum/convergence claim. Supplied inequalities only, not arbitrary constraints.

Caps8dimensions10barriers20Newtonsteps/barrier40backtrackingattempts,
values+-100/curvature>=.001/boxwidth>=.001/barriers1e-6..100. Strict nonbool,
shape, bounded numeric/hugeintbeforeconversion, no mutation/external effects.
5PASS250 independent Decimal firststep derivative/Hessian/direction references,
hand literal gradient/Hessian, positive/negative boundarylimited steps/points,
stationary/feasibility/objective decrease/caps and staged refusal tests.

Broad87AST73kills14survivors. IDs8,45,46,58,76,77 affect redundant strict
interior checks: fraction-to-boundary .99 should keep points strictly inside,
but floating rounding can affect this argument, so no unconditional equivalence
claim. IDs25 stopping equality,42backtrack budget,43Armijo conjunction,
44backtrack divisor,54positive-direction threshold,56Armijo dot arithmetic,
59Armijo comparison,67Armijo bound arithmetic remain UNVERIFIED. Natural
reference fixtures accepted initial cappedstep and do not exercise backtrack
or failure guard. These are disclosed test coverage limits, not equivalent
claims or independent review counts. Independent audit required before merge.

SCOPED, literalPARTIAL. NOT_CLAIMED general inequality optimization, authentic
constraints, full convergence/global optimum, scalability, runtime integration.
New native files, namespace imports, noinit. No external effects.
