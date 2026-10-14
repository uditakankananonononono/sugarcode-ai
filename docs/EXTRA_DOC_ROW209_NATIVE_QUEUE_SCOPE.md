# Row209 Discrete Event Simulation, native Sugarcode

Exact description: "Models queuing systems".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Exact rational finite multi-server FCFS discrete-event queue,heap of server
availability,arrival-IDties/lowestserverfreeties,start/end/wait/sojourntrace,
meanwait/meansojourn/utilization/timeaveragequeuelength. Horizonmaximumfinal
servercompletion from timezero,includingidlecapacity. Zero-timealljobs case
ratiosundefinedNone. Native port of priorAtlashelper with added500independent
linearserverscanoracles and hugeinteger/literalcontractpins. No packageinit.

Caps1..1000uniquejobs/1..20servers/1..120nonblankID/time0..1million. Strict
numericrange/type beforeconversion/schema/capsbeforeeventmaterialization.
26tests500independent exactscheduleandmetricoracles,asymmetrichandtrace,
unequalserverhorizon,idletimes,fractional/zero/caps/types/refusals/no mutation.
Broad33/33ownASTkills. Unique nativefilename,no otherextra_docqueue atbase.

SCOPED finite supplied queue simulation,literalPARTIAL. NOT_CLAIMED authentic
arrival/services, fittedstochasticprocess,realqueueforecast/realexecution/runtime
integration. IDlabelsfree text except length/nonblank contract. No external
effects. Timeunitscaller-supplied;utilization dimensionless. Audit required.
