# CONTRACT_H22: provider-error text characterization (AUTHORED, NOT RUN; tests + contract only)
Base 352ccdc5d25c72c6d45ea11456fdb3ed98c7081f (sole parent). Authority: peer ruling relayed by Main (5:17:07 PM IST), not independently authenticated by me. No product change; no source file touched. Typed ProviderError API repair NOT granted (future unit). Stale old line numbers were not re-fixed.
## Chronology (IST, 10 Oct 2026, self-reported)
tests/test_h22_provider_echo_characterization.py: started 17:18:08, first complete 17:18:40, two small edits 17:19:05 (placeholder cleanup, one monkeypatch added, one over-specific message assertion removed). No source edited at any time. This contract written 17:19:08. Tests before contract; there is no source step.
## What the tests pin (status quo, per the peer's pins i-vi)
- (i) Caught/recorded/printed text is only error_text / setup_error_text output: resolve_route skipped, profile_status reason, ask().skipped/.error, CLI models check parse_route failure, for resolver sites providers.py 346/352/354/358/362, parse_route 376, chat 231-253 (real ChatClient with patched urlopen), ModelProfile 62/64.
- (ii) Raise-site detail STAYS, exact messages pinned (deliberate per H09): HTTP body[:400], unreachable at base_url with reason, shape messages, str(data)[:300], unknown-profile and unknown-route lists with custom names, ModelProfile name echo, ProviderError stays a plain RuntimeError with only args.
- (iii) CLI preflight: unknown FIELD KEY NAMES and missing field names retained; config VALUES, env labels and the profile name are not echoed.
- (iv) shared _run_shared_call malformed-call and unknown-tool text, shared_ask end to end, and tools.call_tool unknown/unexpected/missing text AS IS; model-supplied names stay in repr form; no wrap or quote.
- (v) shared_jev: wrong INSTINCT_PRODUCT raises an uncaught ValueError, not a ProviderError. No CLI caller found by grep (grep-only claim).
- (vi) cli.py build_shared_needle_dataset ValueError: EXCLUDED, unread, no test and no conclusion.
## Read receipt (verbatim = every line read by cat/sed; grep-only = pattern matches only)
Verbatim, full: src/sugarcode/llm/agent.py (95), providers.py (407), shared.py (165), tool_call_shape.py (61), tools.py (188), src/instinct_models/router.py (86), tests/test_h09_error_echoes.py (253), tests/test_h08_cli_provider_errors.py (218), tests/test_h10_shared_boundary.py (238), tests/test_h04_load_profiles_typed.py (213), cli.py 95-300. Partial verbatim: src/instinct_models/providers.py 1-60 (ProviderError, http_json), tool_call_codec.py 85-107 and 148-175 (_walk, decode_tool_arguments, guarded_call). Grep-only: rest of cli.py, tests/test_llm_layer.py (not reused), tests/test_h01/h02/h05/h07 (not reused), repo-wide RuntimeError/ProviderError/shared_config/ChatClient/str(e) greps, shared_jev callers. NOT read: instinct_models config.py (load_config) beyond H10's own test statements; cli.py build_shared_needle_dataset path.
## RUN vs NOT RUN
NOT RUN: pytest, any import of sugarcode or instinct_models, any test. RUN: git, sed/cat/grep, sha256sum, text writing, and python3 -m py_compile on the new test file (syntax only; it does not import the module's imports). Every assertion below is derived from reading source, not from execution.
## Unverified (limits)
- Exact message strings were derived by reading and may not match at runtime: HTTPError.read with BytesIO, URLError.reason, OSError str, dict repr ordering in "returned no choices", ModelProfile KINDS/TRANSPORTS tuple repr, and the shared_jev ValueError origin (load_config versus shared_config line 46: only isinstance ValueError is asserted).
- Peer-run results decide; a failing assertion means my reading was wrong, not that the product changed.
- test_shared_ask_end_to_end uses the real router and catalog like H10 does; its runtime is the peer's.
- No mutation proof and no claim that the tests detect any specific regression.
## Claim limit
Characterization of today's behavior only. No new privacy property, no coverage claim beyond the listed sites, no benchmark claim.
