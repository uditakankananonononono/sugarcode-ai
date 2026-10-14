# Row206 SIR Models, native Sugarcode

Exact description: "Tracks susceptible-infected-recovered".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Native standalone FLOAT synchronous compartment simulation uses constant supplied
hazard rates. Infection=S*(1-exp(-beta*I/N*dt)),recovery=I*(1-exp(-gamma*dt)),
both old-state flows; newly infected do not recover same step. Stable expm1;
returns times/S/I/R/newflows/population/units/assumptions. Approximate discrete
SIR, not exact ODE integration. Prior Atlas behavior ported with added independent
high-precision references and huge-integer/literal-output pins.

Capscompartments0..1million,totalpositive<=1million,beta/gamma0..1000,
dt1e-6..10,stepsinteger0..1000. Strict range/type before finite conversion.
Fifteen tests include350 independent60digit Decimal two-step exponential flow
oracles, asymmetric old-state handreference, mass/nonnegative/extreme/zero
cases,fullcaps/nonbool/schema/hugeintegerrefusals/literalunitsandassumptions.
Broad37/37ownASTkilled. Native namespace import works with no __init__.py.

SCOPED simulation,literalPARTIAL. NOT_CLAIMED exactODE/realepidemicforecast/
authenticrates/fitting/externalexecution/runtimeintegration. Closed homogeneous
population and compatible inverse-time rate units are caller assumptions.
No external effects. Existing nativebase has no extra_doc SIR module; exclusive
206claim parentconfirmed. Independent audit required.
