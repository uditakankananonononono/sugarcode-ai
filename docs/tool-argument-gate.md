# Tool argument JSON shape and declared-type gate

python -m sugarcode.cli tool acmg_bayesian__classify_points null

Returns a structured error, exit1, instead of uncaught non-object failure.
The existing call_tool path now validates declared JSON types before invoking
module code. Bool is not integer/number. Nonfinite floats are refused.
Declared items and dictionary value schemas recurse with depth16 cap; nullable
schemas allow None. Valid calls retain existing result/error behavior.

This is only the catalog's declared schema coverage, not full JSON Schema,
semantic correctness, containment, authorization or size/time budgets. Untyped
list/dict nested contents are not recursively constrained without a declared
items/value schema. No module algorithm modified or model acceptance claimed.

Not full JSON Schema, no auth/semantic/sandbox/size/time proof; untyped object nested custom values accepted (declared limit); typed top-level dict fields only, no universal JSON recursion claim.
