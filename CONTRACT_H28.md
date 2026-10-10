# CONTRACT_H28 - vendor ProviderUnavailable from available() escapes the local catch boundary (characterization)
Parent: a29dddd5095822d6aa8504c0e3602ecbe7aaf337 (peer-supplied bundle, tip verified by git object ops). Files: tests/test_h28_vendor_provider_error_escape_characterization.py, CONTRACT_H28.md. No product change, no vendor edit, no class conversion. Authority: peer grant relayed by Main (5:47:51 PM IST), not independently authenticated by me.

## Chronology (test first)
17:48:04-17:48:09 tests authored; contract after. No source step.

## What the tests pin (current behavior, read from source, NOT a defect claim, NOT a fix)
1. instinct_models ProviderError / ProviderUnavailable are not subclasses of sugarcode.llm.providers.ProviderError; ProviderUnavailable is a vendor ProviderError.
2. Router.run does not contain a vendor ProviderUnavailable raised by p.available() (router.py calls available() outside its try).
3. shared_ask propagates it, and it is not the local ProviderError.
4. cli `shared ask` (via a patched Router.from_config) propagates it; _cmd_shared catches only the local class.
Case (b), chat raising vendor ProviderError: CLOSED AS DUPLICATE. tests/test_h10_shared_boundary.py test_real_router_error_attempt_is_withheld (lines ~74-86) already pins ProviderError and ProviderUnavailable from a transport: real Router.run records outcome "error", shared_ask ok False, detail "details withheld". The vendor-class gap is recorded here only.
Case (c), real HermesLocal.available non-loopback: NOT authored (peer's audit owns it). Out of scope: JSON/Unicode/KeyError escapes, evaluate/OpenClaw search.

## Reachability (stays conditional)
Read: config.py 1-75 has no URL validation (load_config copies INSTINCT_HERMES_URL/MODEL as given); router.py from_config appends HermesLocal when both are set; HermesLocal.available calls require_loopback_url which raises ProviderUnavailable. Whether the real chain reaches that call also depends on provider order (Hermes comes after Needle, Ornith, Inkling local, and only if earlier ones did not answer) and on the environment. Not run, so no runtime claim. The tests use a stub provider, not HermesLocal.

## Read receipt (a29dddd5 blobs)
- verbatim full: src/instinct_models/router.py 1-86 (95f9d055172526e5801443f6124f4ee07dcee572); src/instinct_models/providers.py 1-391 (539519cef230db3ade523e0007016d6c4cba56b4); src/instinct_models/config.py 1-75 (f38cee2160faa19a5ef9c3b8b8310e83c01d01e1); src/sugarcode/llm/shared.py 1-165 (72c63465d978b08db7e27d064b550af4fe342b12); tests/test_h10_shared_boundary.py 1-238 (6bded1470e6ba864581b4bee2b6078a59fdfad76).
- cli.py (6deca9be51c878920eae0afd66786a071f61dfbf): lines 93-135, 210-300 verbatim; rest grep-only.
- Unread: instinct_models/__init__.py (export of Router, Task assumed from tests/test_h10 imports of Router; Task imported from instinct_models as in shared.py line 23).

## RUN vs NOT RUN
RUN: git object ops, sed reads, sha256sum. NOT RUN: pytest, import, py_compile or any syntax check, pip, network. Typos or wrong-name risk exists (e.g. test 4 assumes main(["shared","ask",Q]) routes to _cmd_shared with the preflight passing).
