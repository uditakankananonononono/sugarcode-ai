# H07 health(): typed error result for a malformed /models body (AUTHORED, NOT RUN)

Parent/base: exactly 0c0d491bd1946fbff142157fab9bf36c93df7dca (H05 landed). Files: src/sugarcode/llm/providers.py (M, ChatClient.health only), tests/test_h07_health_malformed_models.py (A), CONTRACT_H07.md (A).
Authority: peer H07 GO relayed by Main 2:40:30 PM IST (not independently authenticated by me; this file is not authority).

Gap (providers.py health, read verbatim at 0c0d491b): `ids = [m.get("id","") for m in data.get("data", [])]` ran after the try. For a valid-JSON /models body that is not an object, a non-list "data", or a non-object member, that line raised AttributeError/TypeError out of a method documented "Never raises".
Change: three checks before that line, each returning the existing error-result shape {"profile","ok": False,"error": <str>} (no new field): body not a dict -> "malformed /models response: body is <typename>, expected an object"; data not a list -> "...data is <typename>, expected a list"; a member that is not a dict -> "...data has a member that is not an object". Only type names appear; the body is never echoed.

CONTRACT DISTINCTION: health() RETURNS an error result and never raises for these shapes. chat() is UNCHANGED and still RAISES ProviderError for a wrong-shaped body (H01: "<profile> returned a <type> body, expected an object"). A test pins both on the same body.

Unchanged and pinned: well-formed body result (exact dict); model not listed; a MISSING "data" key is still ok with models_available 0 (not an error); an empty list is ok; invalid JSON, HTTPError and URLError results are as before; the HF base_url branch returns the malformed error BEFORE the token probe (one urlopen call).
No other health policy, refusal or field change. Not touched: _hf_token_valid, chat, TransformersClient.health.

NAMED GAPS (not changed, flag for the peer):
- _hf_token_valid (providers.py ~253-261): `json.loads(...).get("name")` raises AttributeError if the whoami body is a valid-JSON non-object, and it is reached from health() on a huggingface.co base_url after a well-formed /models. Its except clause catches ValueError/OSError only. health() can therefore still raise there. Out of the H07 spec (the /models body); candidate for a later unit if the peer wants it.
- Member id values are not type-checked (a non-str id is accepted, as before).
- The CLI callers (cli._cmd_models_check/list) are untouched (H08 later).

Read depth, fact (at 0c0d491b): providers.py health 235-251 and _hf_token_valid verbatim (providers.py whole at b6333171 verbatim, diff to 0c0d491b is tests/contract only); test_llm_layer.py 96-140 (the fake server and test_health_probe) verbatim; test_h01_providers_chat_shape.py 1-75 verbatim (stub pattern reused, not imported); collision gate: ls tests | grep -i "h07|health" returned only test_registry_health_search.py (unrelated name), git grep "test_h07" and "health" in tests/ found test_llm_layer.py:134-138 and unrelated bioimage/evidence hits. The new path is free.
Nothing run: no pytest, import or compile. No PASS inherited.
