# H05 call_tool result-shape characterization (TEST ONLY, AUTHORED, NOT RUN)

Parent/base: exactly 9a69fb5cc1af2c8f157576c407e6589b70869078 (H04 FINAL3 landed). Adds two files, edits none; NO source change.
Authority: peer H05 GO relayed by Main 2:35:46 PM IST (not independently authenticated by me; this file is not authority).

Pins, from tools.py 184-188 and 115-138 (read verbatim at 9a69fb5c; nothing run):
- exactly 12000 chars of json.dumps(out) -> {"result": out}, no flag, no preview key (len > 12000 is the test).
- 12001 or more -> exactly {"result_truncated": True, "result_preview": text[:12000]}; no "result" key; preview is EXACTLY the first 12000 characters of json.dumps text (a prefix, not equal to the full text); deterministic across calls; holds for dict and list results.
- Length counts the escaped JSON text (ensure_ascii escapes "é" to 6 chars).
- NaN, Infinity, -Infinity (dict values, nested lists, top level) become the strings "nan", "inf", "-inf" via _jsonable (line 123); output is valid strict JSON (json.dumps allow_nan=False succeeds); finite floats and ints unchanged; the string forms count toward the limit.
NOT asserted (peer exclusions): set ordering, tuple-key collision, and also not the depth>8 str() fallback, vars() of objects, numpy handling, or non-str dict key coercion.
Method: same fake-catalog / fake import_module pattern as tests/test_g03_call_tool_no_execution.py (monkeypatches T.catalog and T.importlib.import_module), so no real module runs.

Read depth, fact (at 9a69fb5c): tools.py 115-139 and 155-188 verbatim (the file is unchanged from b6333171 by diff, and was read whole verbatim earlier at 4015755c; the diff of tools.py between b6333171 and 9a69fb5c is empty); tests/test_g03_call_tool_no_execution.py 1-56 whole verbatim; test_llm_layer.py 74-79 and test_tool_argument_gate.py whole verbatim (earlier pass at 4015755c, not re-read at 9a69fb5c; llm tests were not changed by H04a/H04 beyond new files). Collision gate: `ls tests | grep -i "h05|truncat|jsonable|call_tool|result_shape"` returned only test_g03_call_tool_no_execution.py (different name); git grep for result_truncated, result_preview, _jsonable and test_h05 in tests/ returned no hits. New path tests/test_h05_call_tool_result_shape.py is free.
Nothing run: no pytest, import or compile. The sizes in the tests are computed from json.dumps in the tests (padding assertions), not hard-coded, but the arithmetic is by reading. The peer's earlier audit counts are not ours.
