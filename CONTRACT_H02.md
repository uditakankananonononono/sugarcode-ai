# H02 typed errors for malformed model tool calls (AUTHORED, NOT RUN)

Base/parent: exactly 102ed8d540c0f8ccfa2da43c51c6f5a2496515fc (H01 landed). Edits existing files under the peer's application GO
(relayed by Main 2:01:12 PM IST; not authority by itself). Nothing was run.

Gap (read at 8722231a, same code at 102ed8d5): agent._run did `msg.get("tool_calls") or []`, then `c.get`, `fn.get` on provider-supplied entries: a non-dict entry or
non-dict/None `function` raised AttributeError, a truthy non-list container was iterated (keys/characters), and an unhashable `name` made call_tool raise TypeError.
shared.shared_ask did `c["name"]`/`c.get` over r.tool_calls with the same exposure. Neither failure was a ProviderError, so ask() raised instead of falling back.

Files: src/sugarcode/llm/tool_call_shape.py (A), src/sugarcode/llm/agent.py (M, _run only), src/sugarcode/llm/shared.py (M, shared_ask + one private helper),
tests/test_h02_tool_call_shape.py (A), CONTRACT_H02.md (A).

Policy implemented (peer rulings relayed 1:53:47 and 2:01:12 PM IST):
- ToolCallShapeError subclasses ProviderError (not plain). ONE helper module, used by both consumers.
- Entry must be a dict; `function` must be present and a dict; name must be a str (empty str passes the shape check and is then an unknown tool); id must be a str when present (missing -> "").
  `arguments` is not judged by the helper; call_tool still validates it (text/dict, strict codec).
- Container: missing/None/falsey -> no calls (existing `or []` behavior kept); a TRUTHY non-list raises ToolCallShapeError (no key/char iteration).
- agent._run: container and EVERY entry are validated before any tool runs. Any failure raises ToolCallShapeError("<profile>: ..."), which ask()'s existing `except ProviderError` catches, records in `skipped`, and falls back to the next profile. No partial execution of a batch.
- shared_ask: a malformed individual call yields `{"error": "malformed tool call: ..."}` at that position; valid siblings still execute; one result per call, order kept; unoffered names keep "model called ... which was not offered". A truthy non-list tool_calls container raises ToolCallShapeError and nothing runs. With execute=False nothing is validated or run (unchanged).

DECISION THE PEER MUST CONFIRM (my reading, not stated in the relayed policy): shared_ask's calls are the FLAT shape produced by the vendored instinct_models provider
(`{"name", "arguments"}`, src/instinct_models/providers.py:85; tests/test_shared_layer.py transport), with no `function` key. Applying the OpenAI-style "function must be a dict" rule there would reject every valid call
and break test_ask_executes_real_tool_via_local_inkling. So the ONE helper has two entry modes: tool_call_fields(call) (OpenAI style, used by _run) and tool_call_fields(call, flat=True) (used by shared_ask). Same name/id/dict rules in both.
Missing `function` or missing `name` in OpenAI style is now a shape error (previously name "" -> an "unknown tool" error result). My reading of "function is dict, name is str".

Not changed: instinct_models (vendored; its provider still indexes c["function"]["name"] and json.loads arguments inside the provider, outside this unit), cli.py (a ToolCallShapeError from shared_ask's container check would propagate out of `_cmd_shared`; not handled here),
providers.py, tools.py, H03.

Unverified / NOT RUN: pytest, import, compile; interplay with the real router/catalog beyond the reads above.
