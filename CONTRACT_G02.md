# G02 prep: independent tool-call codec (authored, NOT RUN, NOT WIRED)

Base/parent: exactly 275936a916d641669bbe4ddb3afbb98b278571de. Additive new files only (FINAL2: whitespace-only text -> {} in decoder/doc/test; direct dict validated by the public decoder walk).
- src/sugarcode/llm/tool_call_codec.py (new, stdlib only; no import of isolated_result_codec or any helper there)
- tests/test_prep_g02_tool_call_codec.py (written first)
- prep_proposals/G02/UNAPPLIED-llm-wiring.diff.txt (UNAPPLIED product proposal; text diff of llm/tools.py and llm/providers.py)
- prep_proposals/G02/UNAPPLIED-test_call_tool_no_execution.py.txt (UNAPPLIED test for the wiring: tool function/import must not run when validation fails)
- this file

Decision source: as relayed by Main (peer G02 ruling; author approval relayed 1:30:09 PM IST). This file is not itself authority.

Gap (read at 275936a9, nothing run): llm/tools.py call_tool: narrow json.loads guard (lines 161-163: JSONDecodeError and RecursionError only, no size cap,
duplicates/NaN/Infinity/1e999 accepted, digit-limit ValueError escapes), import_module/getattr at line 176 outside any try despite the docstring
"Never raises" (153-154), shallow _argument_valid. llm/providers.py ChatClient.chat json.loads at ~175 sits under except clauses that omit ValueError
(probes at ~195/212 do catch it). llm/agent.py:59,78,87 catch only ProviderError.

Module API: decode_tool_arguments(arguments, max_chars, max_depth=64) -> dict; guarded_call(fn,*a,**k) -> {"result":..}|{"error":..};
ToolCallDecodeError(ValueError) with .reason in {not_text,too_large,invalid_json,duplicate_key,non_finite,too_deep,not_object,non_string_key}.
Rejects duplicate keys, NaN/Infinity/-Infinity and 1e999 (never coerced), non-object top level, depth > max_depth (object = depth 1, iterative walk).
Caps typed: max_chars int >= 1 (required, no default in the decoder), max_depth int 1..64; misuse raises plain TypeError/ValueError.
No process limits.

Author choices to confirm: DEFAULT_MAX_CHARS=65536 (a caller default only), MAX_ERROR_CHARS=500 (guarded_call truncates messages; old call_tool did not),
max_depth ceiling 64, "" -> {} (preserves `arguments or "{}"`), non-str arguments are refused as not_text.

Proposal (UNAPPLIED, `git apply --check` against 275936a9 tree only): call_tool decodes via decode_tool_arguments(DEFAULT_MAX_CHARS), maps not_object and not_text to the
existing "arguments must be a JSON object" message, and runs import+getattr+call inside guarded_call; providers.chat gains `except ValueError` -> ProviderError.
Behavior changes to review: error text for bad arguments now carries the codec reason; module error messages are capped at ~560 chars; dict arguments still
are decoded too (walk, no bypass). agent.py needs no edit once call_tool is total. Not in proposal: non-dict `data` from a provider (data.get on a list raises
AttributeError) - observed, not addressed.

Unverified: import/compile/test pass; pyproject test layout; the digit-limit ValueError behavior beyond the peer's Python 3.10.12/4300 environment;
RecursionError mapping on deep input (reasoned, not run); that omega/module catalog tests still pass with the proposal.
