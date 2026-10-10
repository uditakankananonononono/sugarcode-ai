# Parameter-domain integration

Base2aefa5a, parent explicit domain policy2026-10-10. This is template validation,
not widening/restricting generic registry identity/kinds or human authentication.
Peer206 authored cases actually passed. Real integration57cases pass; selected
573 (310baseline+206peer+57integration), no skips. Initial two failures found an
unnecessary plan-default normalization and changed accepted hostile invalid mode;
planner now validates but preserves refined params, injection test keeps hostile
keyword and valid mode, explicit invalid mode refused by real tests. Initial three
fixture failures used nonexistent CapabilityGap.examples, corrected to source API.

Caller paths: FeaturePlanner.plan validates AFTER refiner identity check, preserving
refined parameters. codegen.synthesize_code validates/normalizes to fresh plan params
again before builder. All six generated run functions validate params/overrides,
then preflight SAME items before results. Generated scoring score_item also validates
weights. Embedded validator source self-contained math/re only, no new package import.
Exact source parity test catches later helper/source drift. Source size increases by
about9KiB per generated module. Existing saved/active versions are NOT migrated or
rewritten: these fixes govern newly synthesized code, not retroactive runtime repair.

Deliberate compatibility narrowings:
- builtin-only params dict/list/string, known keys; tuples/custom/numeric-string
  params/bool numbers/nonfinite refuse, False/0/empty-string override not absence.
- duplicate lowercase keywords refuse, finite absolute score weight sum, regex and
  replacement grammar validated even if empty items; replacement empty stays empty.
- exact runtime list; numeric/group rows builtin dict/string keys; finite grouping
  scalar values, rendered-label collisions refuse instead of silently coalescing.
- aggregator nonnumeric values skip, bool numbers refuse; threshold numeric strings
  still accepted but nonfinite refuses; finite ordered group sums preflight.

Discovered defect repaired: explicit empty scoring weights used to fall back to
_WEIGHTS in score_item. Both run(weights={}) and score_item(weights={}) now yield
zero, no restored defaults. None alone keeps defaults. This is not a new spec policy.

Not claimed: regex CPU/cancellation, arbitrary item counts/allocations, text coercion
hooks of keyword/scoring templates, preventing caller/thread mutation between
preflight and execution, custom iterable containment beyond refusing input list
subclasses. Static source safety scanner retained, not a security sandbox proof.
Preflight and repeated score_item validation add runtime work; no performance claim.
Snapshot validator does not retain a live import dependency; future edits must update
it and parity test. Default _PARAMETERS remains module-visible mutable state, though
revalidated every public entry; not tamper-proof. Low-level candidate/registry APIs
remain trusted, no forced domain validation of handwritten candidates here.
Independent verdict required, no landing claimed.
