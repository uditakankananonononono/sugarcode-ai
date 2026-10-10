# H01 providers.ChatClient.chat response-shape errors (AUTHORED, NOT RUN)

Base/parent: exactly fef2b37faaf2dc01979a4c16c170fcac52d92008 (G03 landed). Edits one existing file under the peer's application GO
(relayed by Main 1:55:29 PM IST; not authority by itself). Nothing was run.

Gap (read at 8722231a, unchanged at fef2b37f): src/sugarcode/llm/providers.py chat(), after the JSON parse, did
`data.get("choices") or []` and `choices[0].get("message") or {}`; valid JSON of the wrong shape raised AttributeError/KeyError (not ProviderError),
so agent.ask (`except ProviderError`, agent.py 87) raised instead of falling to the next profile.

Policy implemented (peer rulings relayed by Main 1:53:47 and 1:55:29 PM IST):
- body not a dict -> ProviderError ("returned a <type> body, expected an object")
- missing or falsey choices -> the existing "returned no choices" ProviderError, unchanged
- truthy non-list choices -> ProviderError ("choices of type <type>")
- first choice not a dict -> ProviderError ("first choice of type <type>"); only the first is inspected
- message missing or None -> {} (compat, kept); message present and not a dict, INCLUDING falsey ("", 0, False, []) -> ProviderError; not normalized, no fabricated empty reply
- message a dict (including {}) is returned as before
Only chat() changed; health() and the other probes untouched. ProviderError is the existing RuntimeError subclass; no new exception type.

Files: src/sugarcode/llm/providers.py (M), tests/test_h01_providers_chat_shape.py (A), CONTRACT_H01.md (A).
Tests (new, stubbed urlopen, no network): valid message unchanged; missing/None/{} message -> {}; extra keys ignored; non-object bodies (list/str/int/bool/null/float); truthy non-list choices; falsey choices keep "no choices"; non-dict first choice; only first choice checked; present non-dict message incl. falsey; invalid JSON still "unreadable"; ask() falls back to the next profile and records the shape error in `skipped`; ask() with only a malformed profile returns error, not an exception.
Not changed: H02 (agent._run / shared_ask tool_call shapes) and H03.

Unverified / NOT RUN: pytest, import, compile; whether the ask() tests need the real router/catalog data at collection (they call route_modules like tests/test_llm_layer.py does); behavior of any real provider.
