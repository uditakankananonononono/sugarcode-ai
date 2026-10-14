# Row232 Quasi-Newton Methods

Exact description: "Approximates Hessian".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact rational Hessian-BFGS solver on supplied positive diagonal quadratics.
Starts Hessian approximation at identity, solves B*p=-g and takes exact
quadratic line-search step; applies rank-two BFGS secant update. Full gradient,
direction, displacement, gradient-change, before/after Hessian and secant trace.
Does not call approximation the true Hessian. Four coordinates, ten iterations,
values+-100/curvature>=.001, strict nonbool/range before conversion, no mutation.

5PASS250 independent inverse-BFGS fulltrace reference oracles, analytic optimum,
literal rank-two Hessian/step pins, stationary/mixed stationary axis, cap/type/
nonbool/hugeinteger refusal tests. Broad55AST54kills1equivalent: secant all->any
always true because exact BFGS update satisfies every secant coordinate with
positive curvature. Self-audit counts, not independent review counts.

SCOPED, literalPARTIAL; NOT_CLAIMED arbitrary nonlinear optimization, authentic
model, unknown Hessian learning, scalability, runtime integration or external
effects. New native files, namespace imports, noinit. Audit required.
