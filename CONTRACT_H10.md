# CONTRACT_H10 - shared ask boundary (AUTHORED, NOT RUN)

Parent: 12a9bc7a55843b990d1b0337cf08f063616c50be (public HEAD readback 15:24 IST, equal). Authority: Main's relays of peer rulings, not independently authenticated by me.
Nothing was run: no pytest, import, compile or runtime. No env values or credentials used. Vendored src/instinct_models untouched.

## Files
- tests/test_h10_shared_boundary.py (new), src/sugarcode/llm/shared.py, src/sugarcode/llm/providers.py (+`setup_error_text`), src/sugarcode/cli.py (`_cmd_shared` ask branch), this file.

## Chronology (actual, IST)
1. 15:24:07 base readback, checkout h10.
2. 15:24:55 tests/test_h10_shared_boundary.py written FIRST (no source change yet).
3. 15:25:15-15:25:23 shared.py, providers.py, cli.py edited. A same-minute test edit (drop one test that would have run real providers, use dynamic provider names) happened at 15:25:15 before the source edits.
4. 15:25:27+ contract. A later sed corrected two line numbers (see line-number note) in a source comment and the test docstring.

## Attempts detail: five exact pairs (vendored router.py, read verbatim at base)
| pair | file:line, verbatim |
|---|---|
| ("skipped","not a tool-calling task") | router.py:67 `out.attempts.append(RouteAttempt(p.name, "skipped", "not a tool-calling task"))` |
| ("skipped","private task never goes to a hosted route") | router.py:70 `out.attempts.append(RouteAttempt(p.name, "skipped", "private task never goes to a hosted route"))` |
| ("unavailable","") | router.py:73 `out.attempts.append(RouteAttempt(p.name, "unavailable"))`; default detail router.py:33 `detail: str = ""` |
| ("escalated","no tool call") | router.py:81 `out.attempts.append(RouteAttempt(p.name, "escalated", "no tool call"))` |
| ("ok","") | router.py:83 `out.attempts.append(RouteAttempt(p.name, "ok"))` |

LINE-NUMBER NOTE: the relay cited 74 and 82 for unavailable and ok. In this clone 74 and 82 are the `continue` lines after those appends; the appends are 73 and 83. Pairs and text are unaffected. Flagging, not deciding.
Not allowlisted: every "error" outcome (router.py:78 `RouteAttempt(p.name, "error", str(exc)[:300])` - str(exc) text), and any unknown pair or changed detail. These get the fixed text `details withheld` ALONE (no class, no str-derived text). Wording `details withheld` is my choice (matches H09 phrase); not relayed - veto welcome. Filter is at the shared_ask boundary only (`_safe_attempt`); provider/outcome fields and order kept.

## Config try (shared.py `shared_ask`, only when router is None)
Wraps exactly `Router.from_config(shared_config(env))`. Catches `(ValueError, OSError, KeyError, TypeError, AttributeError)`; returns `{"ok": False, "config_error_class": type(exc).__name__}`.
| site | class | receipt |
|---|---|---|
| P1 shared.py `shared_config` product check | ValueError (echoes INSTINCT_PRODUCT); also config.py:47, 56, 58 ValueError/JSONDecodeError | shared.py ~line 45-47; config.py:47 |
| P2 lexical file read/parse | OSError, JSONDecodeError (ValueError), UnicodeDecodeError | lexical.py `from_jsonl` (read_text, json.loads); router.py:57-58; config.py:51 read_text |
| P3 `LexicalToolModel.fit` | KeyError (r["query"], ["name"]), TypeError, AttributeError (`.items()`) | lexical.py `fit` |
`router.run` and `chat` are NOT inside the try. A passed router bypasses config.

## Shapes
- API config failure: `{"ok": False, "config_error_class": "<ActualClass>"}` only. Success and no-answer payloads keep keys and the fixed `error` sentence.
- CLI: stdout `{"error": "<Class>", "message": "<Class>: provider setup error (details withheld)"}`, exit 1, via new `providers.setup_error_text`. H09 `error_text` ("model provider error") unchanged.

## Behavior changes
1. Config failures that used to propagate as tracebacks from `shared ask` now return the class shape (API) / JSON + exit 1 (CLI).
2. Attempt `detail` is withheld for error and unknown pairs.
3. `router or ...` became `if router is None`: a passed router object that is falsy no longer triggers config load (edge change).
4. `shared ask` behavior for a caught config error now exits 1 with stdout JSON.

## Findings only (NOT fixed, no catch-all)
- P4 providers.py ~84-85 `_OpenAICompat.chat`: msg.get AttributeError, tool_calls iteration TypeError, c["function"]["name"] KeyError/TypeError, json.loads arguments ValueError.
- P5 providers.py ~44 `http_json`: non-JSON/non-UTF-8 body ValueError/UnicodeDecodeError; http.client HTTPException (IncompleteRead, BadStatusLine) not caught.
- P6 providers.py ~101-105 `require_loopback_url` via HermesLocal.available (~112) via router.py:72, outside Router.run's try (urlsplit / .port ValueError).
- P7 NeedleLocal.chat providers.py ~262-265 (tuned weights, third-party, class unknowable); U1 NeedleLocal.available ~244-250 (import/AttributeError, third-party not read).
- U2 LexicalLocal chat/predict: no reachable raise found (read, not proven). U4 OpenClawOwner not in any chain.
- Router.run catches only vendored ProviderError (router.py:75-79); a vendored ProviderError escaping shared_ask is not handled by the CLI `except ProviderError` (that imports sugarcode's class) - NOT asserted or tested here, unverified.

## Read depth
Verbatim: router.py, providers.py (all 391), lexical.py, config.py, shared.py 30-135, cli `_cmd_shared`, tests h02/h07/h07a/test_shared_layer 1-70. Grep-only: tests/test_h08 shared_ask lines. Not read: instinct_models catalog.py, health.py, training/, VENDORED.md, third-party needle.

## RUN vs NOT RUN
RUN: git/diff/sha tooling only. NOT RUN: all tests, imports, compilation. Test assumptions unverified: InklingLocal/InklingHFRouter availability with a transport, provider `.name`, directory read error class, INSTINCT_PRODUCT env path through load_config.

## Claim limit
Authored only. Not tested, not working, not a general privacy claim. Covers only the listed sites and the shared_ask attempts detail.
