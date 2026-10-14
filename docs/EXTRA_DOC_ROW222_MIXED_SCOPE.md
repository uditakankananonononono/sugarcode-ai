# Row222 Mixed-Integer Programming

Exact description: "Combines continuous and discrete".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Standalone exact rational finite-box linear MILP with1..3integeraxes andone
continuousaxis. Enumeratesintegerassignments, intersects rationalcontinuous
intervalwith<=/>=/==constraints, chooses correctendpointforlinearobjective,
returns optimum/infeasibilitywithinbox. Includesnegative/zerocontinuousconstraint
coefficients. Increasingintegerenumeration preserveslexicographicties;zero
continuousobjectivechooseslowerendpoint. Not integer-rounded candidate search.

Caps1000integerassignments/integerbounds+-50/continuous+coefficients+-1000/
20constraints,strictnonbooltypes/schema/rangesbeforeconversion/hugeintrefusals.
Five tests500independentline-intersectionendpointoracles,handfractionalaxis,
asymmetriccount,exact1001overcapvalidfixture,fullcaps/refusals/no mutation.
Broad88AST85kills3equivprotectedzero-signcomparisons: a>0/a<0strictness not
observableaftera==0separatebranch;objective>0strictnessnotobservableafterexplicit
zeroobjectivebranch. Removedunusedtiebreakconditionalbeforefinalbattery.

SCOPED finiteone-continuous-axisMILP,literalPARTIAL. NOT_CLAIMED generalMILP/
unboundeddomain/nonlinearobjective/constraintauthenticity/runtime/realexecution.
No external effects. Objective/constraintunitscaller-supplied. Native newfiles/
namespace/noinit,exclusive222claim. Independent audit required.
