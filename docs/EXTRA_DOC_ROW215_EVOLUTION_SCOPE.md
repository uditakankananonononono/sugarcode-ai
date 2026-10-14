# Row215 Differential Evolution

Exact description: "Optimizes continuous functions".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Existing randomizedDE/rand/1/bin unchanged. New exact synchronous generation on
squared-distance target,caller donorindices/draws/forcedcoordinate. All donors
from oldgeneration,three distinctnonselfindices,mutantboxclipping,draw<CR(strict),
forceddimensionevenCR0,strictimprovementselection retainingoldpointties.

Caps4..20points/8dimensions/coords+-1000/F0..2/CR+draw0..1. Independent asymmetric
handgeneration,crossoverequality/forced/tie/clipping/nonzerotargetreferences,
allcaps/types/shapes/donor/forced/bounds/refusals,no mutation. Broad AST comparison,
arithmetic andconstant mutations run,53/53killed after five discoveredtestgaps pinned.

SCOPED supplieddraw DEgeneration/PARTIAL literalfeature. No generalobjective or
globaloptimalityproof,randomsamplingverification,auth/persistence/runtime integration.
Squaredloss comparableonly under compatibleaxisunits. No external effects.
