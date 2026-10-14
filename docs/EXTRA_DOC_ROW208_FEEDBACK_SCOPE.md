# Row208 System Dynamics

Exact description: "Models feedback loops".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Standalone exact rational synchronous stock recurrence x_next=x+dt*(A*x+u),
with all rates from old state. Enumerates simple directed nonzero coefficient
cycles, positive product reinforcing/negative balancing; canonical smallest
index anchor removes rotational duplicates. Self feedback and both directed
orientations supported. Reports exact time/stocks/rates/loops and signs.

Native Sugarcode new files only, namespace import, no package init. Caps8stocks,
30steps,A/initial/forcing+-100,dt1e-6..1. Strict types/ranges before finite checks,
hugeintegerrefusals/shapes validated before cycle enumeration. Four tests350
independent augmented-transition exact oracles, asymmetric synchronous handtrace,
complete3-nodecyclemenu,self/signloops,caps/schema/nonbool/hugeintrefusals.
Broad47AST46kills1equivalent coeff>0->>=0: admitted cycles contain only nonzero
edges, so exact rational cycle product cannot be0. Not counted killed.

SCOPED finite linear feedback dynamics,literalPARTIAL. Exact discrete recurrence
not exact continuousODE/stability proof. NOT_CLAIMED authenticphysicalmodel,
arbitrary stability/control/runtime integration. Coefficient signs don't prove
whole-system stability. Stock/rate units caller-supplied. No external effects.
Independent audit required.
