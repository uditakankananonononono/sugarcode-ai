# Row225 Robust Optimization

Exact description: "Performs well under uncertainty".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Native exact finite-option minimax optimizer for independent coefficientbox
uncertainty. Worstobjective=sum(c*x+radius*abs(x));bestboundandadversarial
coefficientwitness,robustconstraintworstlhs/slack/feasibilitycomputed. Selects
lowestworstobjectiveamongrobustfeasibleoptions,IDties. No probabilityassumption.
Robustperformanceholds only mathematicalsuppliedboxes/menu,notrealworld.

Caps100options8dims20constraints120charIDs/value+-1000/radii0..1000. Types/
schema/rangebeforeconversion/hugeint/capsbeforereads/no mutation. Five tests400
independentuncertaintyvertexenumerationoracles,handdirectedworstcoefficients/
slack/feasibility,minimax,ties/allcaps/nonbool/schema/refusals. Broad58/58ASTkills
afteradversarialwitnesssignboundarypins. Newfilesnative/namespace/noinit.

SCOPED finite robustmenu,literalPARTIAL. NOT_CLAIMED globalcontinuousoptimum,
authenticuncertaintysets/outside-setperformance/realexecution/runtimeintegration.
Objective/constraintunitscallerassumed. No external effects. Audit required.
