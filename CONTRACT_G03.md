# G03 wiring integrator (AUTHORED, NOT RUN)

Base/parent: exactly 8722231aca692faab497431630c2f4b15cb6a74b. This unit EDITS existing product files under the
peer's application exception (relayed by Main 1:47:46 PM IST; not authority by itself). Nothing was run.

## G02 half: the landed UNAPPLIED diff, applied unchanged
`git apply prep_proposals/G02/UNAPPLIED-llm-wiring.diff.txt` against the 8722231a tree (the file landed with G02 FINAL3). No hand edits to those hunks.
- src/sugarcode/llm/tools.py: import from .tool_call_codec; call_tool decodes EVERY arguments value through decode_tool_arguments(arguments, DEFAULT_MAX_CHARS)
  (not_object/not_text -> "arguments must be a JSON object"; other codec errors -> "arguments are not valid JSON: <codec reason>"); import+getattr+call run inside guarded_call.
- src/sugarcode/llm/providers.py ChatClient.chat: `except ValueError` -> ProviderError after the URLError/OSError clause.
The proposal diff file itself is left in place (record of what landed); the no-execution test moved out of it (below).
Tests moved into default discovery: prep_proposals/G02/UNAPPLIED-test_call_tool_no_execution.py.txt -> tests/test_g03_call_tool_no_execution.py
(git rename; only the module docstring changed from "UNAPPLIED ..." to a G03 line; test bodies byte-unchanged).
Caller-owned aliasing: a direct dict is validated by a walk but returned as the SAME object (no deepcopy); aliasing/mutation afterwards is the caller's responsibility; no concurrency claim.
Read of existing callers/tests at 8722231a (not run): tests/test_tool_argument_gate.py (nonobject cases '[]','null','42','true',[],None,42 all still map to "arguments must be a JSON object";
monkeypatched classify_points still resolved at call time), tests/test_llm_layer.py:79 ("{not json" -> error), cli.py:215, shared.py:86, dataset.py:95/107 pass str or dict; agent.py unchanged.
Known behavior changes: bad-args wording now carries the codec reason; module error text from guarded_call is capped at ~560 chars; dict arguments deeper than 64, with non-str keys, or over 65,536 nodes are now refused.

## G01 half: NEW minimal hunk (peer audits it as new code, not an approved proposal)
File: src/sugarcode/self_improve/codegen.py. Function: _assemble. Region: import block (new line after `from .domain_source import ...`) and the return statement at original line 49.
Change: `module_text, gap_text = render_header_fields(plan.module_slug, plan.gap_signature)` then `_HEADER.format(module_slug=module_text, gap_signature=gap_text, ...)`. _HEADER text is unchanged.
Why this point: grep of src and tests at 8722231a shows _HEADER is defined once (line 22) and formatted once (line 49); `_assemble` is the single function every builder in _BUILDERS goes through, and
synthesize_code is the only public path to it. FEATURE metadata and _PARAMETERS already use repr() and are untouched. No other generator writes an "Auto-generated"/"Module:"/"Gap:" header (grep).
No second defensible callsite found, so no adjudication stop.
Header output change: `Module: m1` becomes `Module: "m1"`; `Gap: gap sig` becomes `Gap: "gap sig"`; non-ASCII appears as JSON \uXXXX escape text in the docstring; code_sha256 of every generated module changes (no golden hash found in tests/self_improve; stored approvals/ledger rows
carrying an old code_sha256 will not match a regeneration: NOT investigated beyond that grep).
Tests (new): tests/self_improve/test_g03_codegen_header_wiring.py.

## Unverified / NOT RUN
pytest, import, compile, exec of anything; real test collection; interaction with approval/ledger rows holding old code_sha256; pyproject discovery beyond reading testpaths=["tests", ...].
