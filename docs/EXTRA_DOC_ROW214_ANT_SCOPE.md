# Row214 Ant Colony Optimization

Exact description: "Solves routing problems".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Native standalone exact rational ant-colony Hamiltonian tours with supplied
roulette draws. Transition pheromone/edgecost, strict cumulative threshold,
ascendingnode ties; directedrouteclosedatstart,exactlength; synchronous
pheromone evaporation and deposit/cost on traversededges. Reports tours,
bestant/route,cost,newpheromone. No optimum guarantee or automatic sampling.

Caps2..8nodes/20ants/cost0..1000(diagonal0offdiagonalpositive),pheromone1e-6..1000,
evaporation0..1/deposit0..1000/draw[0,1). Shapes/types/rangesbeforesearch and
numericconversion includinghugeints. Five tests300independent60digitDecimal
routing+pheromoneoracles,strictthresholdhandroutes,allcaps/schema/types/hugeint/
nonbool/stagedrefusals,no mutation. Broad62/62ownASTkills. Zeroevaporation/
fullevaporation/zerodeposit supported;futuregeneration requirespositive input
pheromone so entirelyzero outputcannotbe reusedwithout callerrestart policy.

SCOPED supplieddrawonegenerationrouting,literalPARTIAL. NOT_CLAIMED optimal
routing,authenticcosts/randomness/realjourney/runtimeintegration. Costunitscaller
supplied;pheromoneweightsrelative. Newfilesonly/namespaceimport/noinit. Native
basehadnoantmodule,parentexclusive214claim;213215leftlane1. Audit required.
