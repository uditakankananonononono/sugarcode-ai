# CONTRACT H08 - CLI typed provider errors (AUTHORED, NOT RUN)

Base: ab1542455bd3065c5c41dd054c44c25a6736d67c. Files: `src/sugarcode/cli.py`, `tests/test_h08_cli_provider_errors.py`, this file.
Authority: peer H08 rulings relayed by Main; not independently authenticated by me. This contract is not authority.
Nothing was run (no pytest, import, compile or runtime). No provider edits.

## Authoring order (factual record)
`src/sugarcode/cli.py` was drafted FIRST, then `tests/test_h08_cli_provider_errors.py` and this contract, in the same sitting.
This unit is NOT test-first. Nothing was run. No retroactive test-first claim is made. Chronology adjudicated by the peer
(relayed by Main) as a deviation: unit proceeds, independent mutation testing is the constraining evidence, no precedent.

## Purpose
An expected `ProviderError` (family, incl. `ToolCallShapeError`) that reaches the CLI becomes a clean typed message and exit 1,
not a raw traceback. Unexpected bugs keep behavior: only `ProviderError` is caught, no catch-all, no retry, wrapping only.

## Exit and output (no new codes, no new uniform shape)
- Provider-runtime failure: exit 1. argparse usage stays 2.
- JSON commands (`models list`, `models check`, `ask`, `shared ask`): stdout `{"error": "<text>"}`, return 1, same as the
  existing `tool` / `shared dataset` / `models check` convention.
- `models check` config failure is a top-level `{"error"}`, not a per-profile row.

## Disclosure rule (same as H04)
Echoable: field names, missing-field names, built-in constants, item index, exception CLASS name, codec reason.
Never: profile or route names, custom names, endpoints, env labels, body excerpts, secret values.

## Per-site classification (wrapped escape sites)
| Site (cli.py) | Reachable sources | Class | Text emitted |
|---|---|---|---|
| `_provider_preflight()` (load_profiles) | providers.py loader raises 137,141,147,150,153,166,168,174 (H04 loader boundary) | SAFE | `str(e)` |
| `models list` after preflight | `profile_status` catches per-profile resolve errors itself; only a load_profiles failure can escape (config changed after preflight) | UNSAFE-by-ambiguity | `ProviderError: model provider error (details withheld)` |
| `models check` parse_route | providers.py 361 (lists custom names), loader (re-read) | UNSAFE | generic + class |
| `ask` (resolve_route/parse_route/resolve) | 331, 337, 339, 343, 361, 217-239 style endpoint/body text, env labels | UNSAFE | generic + class |
| `shared ask` container | `ToolCallShapeError` (tool_call_shape.py 36: constant + type name), subclasses | SAFE | `ClassName: str(e)` |
| `shared ask` any other ProviderError | unknown | UNSAFE | generic + class |
Ambiguous source = unsafe. `str(e)` never defaults.

## Caveat: preflight vs command
Preflight and the command each read `os.environ`. If config changes between them, the result is at worst the generic message
instead of the loader message. The distinction is message-only; it is NOT a provenance claim. Cost: one extra `load_profiles()`
(env/file read, no network) per wrapped command, including `models check <profile>` and `ask --profile`.

## Behavior changes (explicit)
1. Loader failure in `models check` (with or without a profile) is now top-level `{"error"}` instead of a per-profile row.
2. Loader failure in `ask` (incl. `--profile`) is now top-level `{"error"}` exit 1 instead of an `AskResult` dict.
3. `ask --route <unknown>`, `models check` unknown route, `models list` load failure, and `shared ask` container shape errors no longer traceback.

## Static enumeration of the module-import surface (no execution)
Method: source inventory at ab154245. Read pyproject `[project.scripts]` (only `sugarcode.cli:main` and
`splice-vus-triage`; no entry-point plugin groups; no setup.py/setup.cfg); `src/omega/registry.py` REGISTRY (a literal `_MODULES`
list, `module_slugs`); `llm/__init__.py` imports; every `importlib.import_module` / `__import__` / `spec_from_file_location`
site found by grep over `src` (tools.py 93 and 180, omega/health.py 12, enterprise_bio/core.py 255, ecosystem/core.py 25 import only
`sugarcode.modules.<slug>`; self_improve registry/isolated_dispatch load snapshot files and are not referenced from cli.py);
word-bounded grep of `src/sugarcode/modules`, `src/omega`, `src/sugarcode/tools`, `src/sugarcode/self_improve` for
`llm|providers|load_profiles|ProviderError|instinct_models`: zero hits. Files referencing providers/ProviderError:
cli.py, llm/{__init__,agent,providers,shared,tool_call_shape}.py, instinct_models/{__init__,providers,router}.py.
Conclusion: `route`, `tool`, `ailibrary` do not reach load_profiles by any static path found.

## Out of scope (ledger, not a durable todo)
- `models check` per-profile row `str(e)` (cli.py ~198 at base): pre-existing echo, UNCHANGED (can echo profile names for an unknown
  `models check <name>` or env labels).
- `AskResult` `skipped`/`error` = `str(e)` (agent.py 83, 92): pre-existing echo, UNCHANGED.
- `instinct_models.providers.ProviderError` is a different class from `sugarcode.llm.providers.ProviderError`; errors from
  `Router.from_config` in `shared ask` are NOT wrapped here.
- `tool`, `ailibrary`, `route` commands untouched.

## Claim limit
Claimed: the wrapped escape sites above emit the classified text and exit 1. Not claimed: any general CLI privacy guarantee,
runtime behavior, or that anything passes (nothing was run).
