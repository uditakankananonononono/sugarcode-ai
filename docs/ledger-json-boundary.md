# Engine ledger strict JSON boundary

Base: published 35998c7efc977a4682abb5e2e410d62ee4a4e3fd. SC-J01 changes only
engine.py _log()/ledger(), new tests and this contract. Not all state readers.

Fresh ledger records snapshot exact builtins using snapshot_json and encode with
allow_nan=False before opening append. None/string/bool/int/finite-float/list/
tuple/dict supported; tuple becomes array, exact string keys, no custom coercion.
Cycles, subclasses, nonfinite numbers, depth>64 and expanded values>10,000 refuse
with InvalidLedgerValue; encoder ValueError/TypeError/RecursionError retains cause.
Limits are PER RECORD, not accumulated history. Foreign module override refuses
before append; module field must be exact string matching this engine.

Historical rows reject duplicate decoded keys including escaped equivalents at
any object depth; snapshot refuses nonfinite/unsupported/out-of-bound values.
Top level must be object with this engine's module. Bad row raises indexed
InvalidLedgerValue, preserving original bytes and stopping the whole read; blank
physical lines count toward the error index but produce no record. Legacy strings
are not reinterpreted; optional event/at/other-field schema not newly enforced.

Fresh invalid serialization leaves existing file unchanged and does not create
new ledger file. Caller mutation after return cannot alter stored bytes. Valid
lifecycle remains functional. No content authenticity, authority, completeness,
chronology or tamper-proof claim: local edits can still replace valid records.

No full-file/line-byte/total-record cap before read_text or JSON decoding. Traversal
limits are postdecode. IOError/MemoryError/OverflowError not normalized. Append
can be partial on filesystem crash/failure; per-process lock not multiprocess.
Engine operations may mutate other state BEFORE _log fails: this is not atomic
transactional operation+ledger or guaranteed complete logging. Registry, isolated
result and other JSON paths unchanged. Old non-JSON/custom default=str history
cannot be recovered semantically; no migration or filtering.

Builder25 new PASS; exact base with only new-error-import adaptation to generic
ValueError expectations:23 FAIL/2 PASS. Source of baseline failures includes bad
values accepted, duplicate/nonfinite/foreign rows accepted, wrong errors and
encoder failure creating an empty file, not missing-import canaries.
Broader self_improve + shared-layer + router-asset selection223 PASS, no skips
(198 prior +25 new), not independent/full configured-suite/CI/science acceptance.
Raw/JUnit and adapted baseline test are supplied for independent verification.
