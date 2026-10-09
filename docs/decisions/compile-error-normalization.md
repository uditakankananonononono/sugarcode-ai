# Generated source compile errors

New candidate based on public main 54d35492. Fresh source inspection reproduces
raw SyntaxError for top-level return, break and continue: ast.parse succeeds,
compile fails. This candidate was implemented from current source, not from a
lost peer archive, and makes no claim to recover the old repair's exact bytes.

Contract: SyntaxError from either parse or compile becomes SafetyViolation,
with the original SyntaxError as cause. Non-SyntaxError compiler exceptions
still propagate. Existing import/name/AST restrictions are unchanged. This
normalizes a public validation boundary; it does not prove code containment,
repair cycle-level exception handling, or make generated features safe.
