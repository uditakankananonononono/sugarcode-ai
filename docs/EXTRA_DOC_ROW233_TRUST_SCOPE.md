# Row233 Trust Region Methods

Exact description: "Constrains step size".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact scalar quartic trust-region optimizer. Exact derivative/Hessian quadratic
model minimized over [-radius,radius] using boundary/zero/interior stationary
candidates. Actual/predicted reduction ratio governs accept/reject and radius
shrink/expansion. Full decision trace and actual objective history.
Caps30iterations, initial/tilt+-10,radius.001..10, no nonbool/hugeinteger
conversion or external effects. Supplied model only, no global optimum.

5PASS400 independent expanded-polynomial derivative/model/reference traces,
literal negative-curvature reject/shrink and accept/expand, exact .1/.25/.75
threshold witnesses and .23 shrink gap, stationary/caps/type/refusals.
Broad68AST64kills4survivors: ids24 h>0->h>=0 equivalent because rational x
cannot satisfy12*x*x-4==0; ids25/26 strict interior endpoints equivalent to
already included identical boundary candidate. Id63 expansioncap10->11 remains
UNVERIFIED survivor: no natural admitted witness identified, but no equivalence
claim made. Independent review needed for this guard. Counts are self-audit.

SCOPED, literalPARTIAL. NOT_CLAIMED arbitrary multivariate optimization, global
minimum, authentic model, convergence, numerical scale or runtime integration.
New native files, namespace imports, noinit. Audit required.
