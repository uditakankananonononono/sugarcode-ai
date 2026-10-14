# Row 253 Contextual Bandits
Exact description: "Uses side information".
Source: https://docs.google.com/document/d/1kCtzves_4OGVKUdFUPC0bkvY3jQGnfpeeEJWe1mQ3xY/edit

Context-stratified Bernoulli posterior policy. Uses supplied context as side
information by filtering history to that exact category. Independent Beta(1,1)
prior per context/arm; exact posterior means rank arms, input-order ties. Returns
context successes/failures, matched count and all-context counts. Other context
rewards do not change this context's policy. No cross-context generalization or
stochastic exploration claim; no actual arm execution.

Caps: twenty unique arms, one thousand observations, identifiers 1..80 chars,
strict integer rewards 0 or 1, no bool coercion/huge integer reward. Caps before
scan, exact schemas, no mutation/effects. Tests at
 tests/extra_doc/test_context_bandit253.py: four cases, 500 independent context
subset/Beta pseudocount references, literal side-information choice reversal,
unseen prior/ties, caps, schemas and staged refusals. One own mutation survivor
updates the other total-count bucket, preserving returned all-context count;
buckets are not used in policy. Independent audit required.

SCOPED, literal PARTIAL. NOT_CLAIMED arbitrary context generalization, authentic
rewards, regret guarantees, actual execution or runtime integration. New native
files, namespace imports, no __init__.py.
