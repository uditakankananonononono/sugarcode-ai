# Row230 Adam Optimization

Exact description: "Adapts learning rates".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Actual FLOAT Adam iterative solver for supplied positive diagonal quadratic
sum(0.5*a_i*x_i^2+b_i*x_i). Analytic gradient, first/second exponential moments,
step-indexed bias correction, per-coordinate effective rates, epsilon outside
square root, point/moment/gradient/rate/objective trace. Both beta zero paths
supported; state starts at zero each call. No warm-start moment API. Existing
finite-difference Adam method unchanged. Fixed caller budget, no convergence flag.

Caps1..8dimensions/100iterations/initial+linear+-1000/diagonal1e-6..1000,
rate+epsilon1e-10..1,beta1=0..0.99,beta2=0..0.999. Type/range checks before finite
conversion, including huge +/-10**400 refusal at every numerical input. FLOAT,
not exact arithmetic. No caller-input mutation. Supplied units/scaling affect
coordinate rates; model and measurement compatibility not verified.

Five tests include350 independent60-digit Decimal full traces (all moments,
bias corrections, rates, points, objective histories), asymmetric first step,
zero gradient/betas, final-gradient and initial-objective pins, full cap/type/
schema/refusal/huge-int menus. BroadAST59/59 own comparison/arithmetic/integer
constant/boolean mutants killed after final gradient-sign test gap pinned.

SCOPED supplied diagonal-quadratic Adam solver,literalPARTIAL. NOT_CLAIMED
arbitrary objective, general/global convergence, authentic model/gradients,
real-world execution, runtime integration or exact arithmetic. Adam losses need
not decrease every iteration. No external effects. Independent audit required.
