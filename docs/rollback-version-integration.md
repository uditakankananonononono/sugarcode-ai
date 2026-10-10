# Mandatory engine rollback version pin

Stack base948d9bd (J05 pending integrated candidate, not main). Parent selected
mandatory version pin2026-10-10. J05 already owns action/module/feature binding;
A01 adds version target binding, not a duplicate claim for J05's repair.

request_rollback requires active feature, KeyError before gate mutation otherwise,
and stores feature + positive builtin int active_version_at_request. Engine
rollback validates J05 approved binding, mandatory pin, A01 pure target helper,
then passes expected_active_version to registry.rollback. Comparison and state
write occur within SAME registry object's in-process lock. Pin mismatch raises
PermissionError before registry mutation. Missing/inactive request refused;
legacy unpinned engine commits refuse (deliberate compatibility narrowing).
Generic request/status/full-record API remains generic. J05 known engine payload
validator accepts feature alone as legacy shape or feature+positive int pin;
engine commit alone requires pin. Exact auto gate decision bypass never bypasses
pin. Low-level registry.rollback without expected pin remains trusted legacy API.

No once-only consumption record. Sequential reuse for earlier version is refused,
but manual restoration of same version permits replay. NO cross-process CAS,
no locking across separate FeatureRegistry instances, gate+registry transaction,
local editor authenticity, permission cryptography or immutable active generation.
Version number alone not code hash pin; manually rewriting same version content
is not detected by this check. Request reads active snapshot without lock held
through gate save: stale request can issue but commit refuses changed version.
Postreplace durability/logging failures can follow committed rollback; no retry
claim. Existing atomic file semantics unchanged.

55peer authored cases actually PASS on J05 base. First integration466selected:
5FAIL/461PASS, including exact J05 payload schema omission (fixed to accept typed
optional pin), nonexistent foreign active feature fixture, and two tests asking
for inactive rollback approval contrary to chosen active-request boundary. Fixed
fixtures assert refusal at request; foreign fixture now has real active feature.
478selected PASS (411J05+55peer+12new), no skips. Actual new cases cover pin/readback,
new activation and between-check/commit race, sequential reuse, absent/bool/zero/
negative/string/float pin, correct newer rollback, missing request/no gate mutation.
Independent verdict required, J05 dependency still pending.

Independent VERIFIED version-pin verdict478PASS reproduced; replay after manual
restoration of same active version confirmed possible by verifier probe. No
consumption store, version drift protection only, not once-only authorization.
