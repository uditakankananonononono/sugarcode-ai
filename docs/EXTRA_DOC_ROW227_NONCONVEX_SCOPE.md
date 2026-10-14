# Row227 Non-Convex Optimization

Exact description: "Handles complex landscapes".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact multistart neighbor descent on finite nonconvex quartic landscapes,
sum((x_i^2-1)^2+b_i*x_i) plus adjacent-coordinate couplings. Caller grid,
starts and move budget; every step strictly improves the supplied objective.
Deterministic lexicographic neighbor ties. Local-minimum flag only when
observed, not inferred after budget. No claimed global grid/continuous optimum.

Caps4axes7values/axis20starts100moves and2401vertices; bounds+-10, strict
ascending axes, strict integer indices/nonbool, hugeintbeforeconversion.
5PASS400 independent whole-grid score/adjacency lookup reference oracles,
literal basin/trace/move-budget/tie/caps/refusal/mutation safety checks.
Broad66AST64kills2equivalents: id7 cap2401->2402 is unreachable under4x7
axis guards; id42 addition->subtraction permutes neighbor visitation because
both deltas -1,+1 are visited and selection uses full objective/index key.
Self-audit counts, not independent reviewer counts.

SCOPED, literalPARTIAL. NOT_CLAIMED arbitrary objective/continuous/global
optimization, authentic landscape, throughput or runtime integration. New
native files/namespace/noinit. No external effects. Audit required.
