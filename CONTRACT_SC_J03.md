# SC-J03 prep: strict child-result decoder (authored, NOT run, NOT wired)

Reconciled by reading (not running) src/sugarcode/self_improve/isolated_dispatch.py at main 35998c7
(archive sha256 8659a493...a1ac verified).

Files (new only):
- src/sugarcode/self_improve/isolated_result_codec.py
- tests/test_prep_sc_j03_isolated_result_codec.py (import: sugarcode.self_improve.isolated_result_codec; check against pyproject layout, not verified)
- this file

Findings in real code:
- Cap constant: 1_048_576 BYTES. Parent reads stdout bytes with read(1_048_577), refuses if len > 1_048_576 (line 46-47), raising RuntimeError. Codec default max_bytes=1048576 matches and is a redundant second check.
- Bytes vs text: line 48 is json.loads(raw) on BYTES. json.loads on bytes auto-detects UTF-8/16/32 and tolerates a BOM; the codec is stricter (strict UTF-8, no BOM). Launcher prints json.dumps(..., allow_nan=False) with default ensure_ascii, so legitimate output is ASCII; no expected behavior change.
- Line 49 already checks top-level dict and keys=={'result'} and raises ValueError('invalid result protocol'). ResultProtocolError subclasses ValueError, so existing ValueError handlers stay compatible.
- Gap closed by codec: line 48 bare json.loads permits duplicate keys at any depth (incl. inside result), nested NaN/Infinity, 1e999 -> inf, huge-int and deep-recursion errors (RecursionError is not ValueError).
- max_depth=64 matches json_values.snapshot_json depth limit. max_int_digits=64 is an author choice; the launcher's allow_nan=False dumps permits big ints, so confirm 64 does not reject a legitimate feature result (Python's own default limit is 4300 digits).
- Does not duplicate json_values.snapshot_json (that copies in-memory builtins); the codec validates untrusted bytes. Walk only re-checks the already-parsed tree.

Proposed wiring (NOT applied; integrator owns): replace lines 48-50 with
    result = decode_child_result(raw)   # raw already capped at line 46-47
    return result
and add the import. Lines 46-47 stay. Error mapping: ResultProtocolError(ValueError).

Unverified: import/compile/test pass; pyproject test layout; that real isolation ran (this helper never implies containment PASS); the lone-surrogate and deep-nesting test expectations were reasoned, not executed.
