# CONTRACT H09 - pre-existing ERROR-PATH echoes become generic + class (AUTHORED, NOT RUN)

Base: 240b620c5fd65a8ccf4c6218dd52eb91f4a0e81c (public HEAD readback 15:11 IST). Files: cli.py, agent.py, providers.py
(error-string construction only), tests (new `tests/test_h09_error_echoes.py`; 8 existing assertions rewritten), this file.
Authority: peer H09 GO, rulings A-E and the health ruling, relayed by Main; not independently authenticated by me. This file is not authority.
Nothing was run. No provider behavior or logic change. No general name-hiding or privacy claim.

## Policy
Any ProviderError text that is recorded or printed on an error path is `"<ClassName>: model provider error (details withheld)"`
via `providers.error_text(exc)`. Zero exception text. Type or subclass membership is never a message-source proof.
`str(e)` stays at ONE site: the H08 CLI preflight (`_provider_preflight`, audited H04 loader strings). Library-side loader
errors inside `agent.ask` are generic too (ruling D).
Successful-output fields (profile names, base_url, model) are NOT changed. A field may appear in an error row only if the same
command's success output already emits it (ruling A).

## Per-site classification (current lines at base)
| Site (base line) | Reachable raise sources | Class | Now |
|---|---|---|---|
| cli.py models check row (241-242) | resolve(): providers 331 (unknown name, lists known names), 337/339/343 (name, env labels, paid text), loader | UNSAFE | `error_text` |
| agent.py ask --profile (82-83) skipped + error | same as above | UNSAFE | `error_text` for both fields |
| providers.resolve_route skipped (373-374) | resolve() raises as above | UNSAFE | `error_text` |
| agent.py run failures (88-91) | ChatClient.chat 214-233: `{profile} HTTP {code}: {body[:400]}`, `unreachable at {base_url}`, `unreadable response: {str(e)[:200]}`, `no choices: {str(data)[:300]}`, type-name forms; TransformersClient pip hint; _run ToolCallShapeError with `{client.profile}: ` prefix | UNSAFE (no source allowlist) | `error_text` |
| providers.profile_status reason (389-390) | resolve() raises as above | UNSAFE | `error_text` |
| health() /models probe branch (URLError, TimeoutError, OSError, ValueError) | OS/network reason text, host or endpoint capable; json error text | UNSAFE | `unreachable: <ClassName>` |
| health() HTTPError branch | `e.code` int | constant, stays | `HTTP <code>` |
| health() malformed /models, malformed whoami | type names and fixed text only (providers 163-170 region) | constant, stays | unchanged |
| `_hf_token_valid` URLError/OSError/ValueError branch | same as probe branch | UNSAFE | `unreachable: <ClassName>` |
| `_hf_token_valid` HTTP branch | `e.code` int | constant, stays | `HTTP <code>` |
| chat() raise sites themselves | text unchanged; classified at the catch sites above | not an echo site | unchanged |
Not wrapped here: parse_route/unknown-route (H08 CLI catch), instinct_models ProviderError (H10).

## Per-command field table (ruling A)
| Command | Success output fields | Error output fields (this unit) |
|---|---|---|
| models list | per profile: all ModelProfile fields except base_url_env/model_env (incl name, base_url, model) + ready, reason ("configured"), base_url, model, optional health | same key set; ready False, reason = generic. Name/base_url/model and api_key_env (an existing field, an env LABEL kept as in success output) are the profile's declared values, unchanged. Secrecy applies to `reason` only. |
| models check | `profile`, `ok`, `model`, `model_listed`, `models_available` (+`token_valid`) | `profile`, `ok`, `error` (`error` is existing for health errors); error text generic or class-only |
| ask | AskResult dict: answer, profile, modules, tools_offered, tool_calls, skipped_profiles, error | same keys; skipped_profiles / error carry generic text |
| shared ask | unchanged (H08) | unchanged |
The `profile` display field in a models check error row is the name the user typed or the route lists; it is emitted in success rows too.

## Intentional behavior changes
1. AskResult.skipped / .error, resolve_route skipped, profile_status reason, and models check row error lose all detail (profile names, env labels, HTTP codes with body excerpts, endpoints, "start Ollama" hints). Deliberate detail loss (ruling E). A user can no longer tell from the skipped list which profile failed or why; only the class.
2. health() probe and whoami "unreachable" strings: `unreachable: <ClassName>` (was `<reason text>` and `unreachable: <reason text>`).
3. Rewritten existing assertions (8): test_llm_layer 163 (was `"ollama unreachable" in s`); test_h01 127, 135 and test_h02 211, 218 (were `startswith("bad ")`/`startswith("bad")`); test_h07 `test_unreachable_unchanged` (was `error == "refused"`); test_h07a `test_unreachable_stays_a_string` (2 asserts: was `unreachable: refused`, `unreachable: slow`). Peer said five detail/prefix assertions for llm/H01/H02; the three health ones are the extra consequence of the health ruling.

## Chronology (actual)
Existing assertions rewritten and `tests/test_h09_error_echoes.py` written FIRST (15:14-15:15 IST), then providers.py/agent.py/cli.py, then this file. Nothing run.

## Read depth
Verbatim: agent.py (all), providers.py 28-100, 125-392, cli.py models/ask/shared sites and helper region, test_llm_layer, test_h01, test_h02, test_h07, test_h07a, test_h04 160-172, all 21 test_cli_*. Grep-only: the other test files for strings (`unreachable|skipped|reason|needs`), test_h04 outside 160-172, instinct_models.

## Findings (inventory, not changed)
Successful-output names: models list `name`/`base_url`/`model`; models check `profile`/`model`; AskResult.profile. Peer clarified these are normal display, a separate design question.
Other tests that mention these strings (grep): none beyond the 8 above.

## Claim limit
Claimed: the sites in the classification table emit the classified text. Not claimed: runtime behavior, a CLI-wide privacy guarantee, or that anything passes.

## Follow-up (stacked on 1f805f70f17a146f0f2358f708f45c5248ea1658): two test defects found by the peer audit
1. `test_profile_status_reason_is_generic_and_fields_unchanged` asserted the env label absent from the whole row, but `api_key_env` is a retained success field. Now: reason-only secrecy, and `api_key_env`, `name`, `base_url`, `model` asserted present with their declared values.
2. In test_h07a `test_unreachable_stays_a_string` my inline `# H09` comment swallowed `and out["ok"] is False and "error" not in out`. Restored as executable assertions.
Actual chronology: both tests edited FIRST; no source change was needed or made; then this section. Nothing run.
