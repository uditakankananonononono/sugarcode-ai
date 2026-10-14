# Row210 Monte Carlo Tree Search

Exact description: "Explores decision trees".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Native standalone actual UCT tree search: expand first untried child, select
expanded children by mean reward+exploration*sqrt(log(parentvisits)/childvisits),
rollout using caller supplied bounded draws, backpropagate terminal reward to
selected/expanded path only. Final recommendation by visits/mean/childorder.
ExactFractionrewardaccumulation, FLOATtranscendentalUCTscores honestlylabeled.
No globalfinitebudgetoptimalitypromise. Rollout histories/counts/sums returned.

Caps100nodes/8children/depth8/100iterations,draws exactly8periteration in[0,1),
exploration0..10,terminalreward+-1000,unique1..80charIDs. Tree schema,parent/
connectedness/root/depth/types/ranges validated before search. Newfilesonly,
namespaceimport/noinit. Seven tests250independenttwo-armUCTvoteoracles,hand
expansion/rollout/backprop,distinctdrawatdepth/round,explorationeffect,ties,
terminalroot,exact100nodefixture,allcaps/schema/hugeints/type/refusalpaths.
Broad85AST84kills1equivlen(menu)-1->len(menu)+1 clampbound: admitted draws<1,
menu<=8ensure int(draw*menu_size)<menu_size,so min neveruses clampbound.
Initialreal test gaps for drawindex/childcap pinned; no caller mutation.

SCOPED supplied finitetree MCTS,literalPARTIAL. NOT_CLAIMED environmenttruth,
unbiasedrolloutpolicy,equilibrium/globaloptimum/exactUCTscore or external/runtime
execution. Constantterminalrewards suppliedbycaller. No external effects.
Independent audit required. Parentexclusive210claim,other205207211leftlane1.
