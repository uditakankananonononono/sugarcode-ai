# SC-P01 parameter domains, candidate contract v1

PREP ONLY. Tests authored, not run. Base: ba0eb275f182e77a4f24530b668e3e17f2528df5.
No existing path changed. No integration, repair verdict, model or quality claim.

## Explicit helper API

`validate_parameters(kind: str, params: dict, overrides: dict | None = None) -> dict`
returns a fresh full normalized parameter set or raises `ParameterDomainError`.
The kind and all keys must be exact builtin strings. Supplied parameters and
supplied overrides must be exact builtin dicts. Unknown keys are errors.
`None` alone means no overrides; an empty mapping means no field replacements.
Overrides replace named fields, including whole nested mappings, never merge
nested keys. The base is validated before overrides so an override cannot hide
invalid stored defaults. Output mappings/lists do not alias caller inputs.

`validate_runtime_items(kind: str, items: list, effective: dict) -> None`
preflights the exact builtin list and revalidates effective parameters. Numeric
and group checks apply to aggregator and threshold_alert only. No IO, services,
registration, J04 dependency, or proposed shared API binding. Diagnostics expose
paths/reasons only, not values. No custom coercion or repr hooks are used.

## Six domains and matching defaults

| Kind | Fields and domains |
| --- | --- |
| keyword_filter | keywords: exact list of nonempty exact strings, distinct under `lower()`; default []. mode: keep/drop, default keep. Empty list matches nothing. |
| scoring_rule | weights: exact dict of nonempty exact string keywords to finite exact int/float, excluding bool; distinct under `lower()`. default {}. Negative/zero weights allowed. Sum of absolute float-converted weights must stay finite, bounding every subset/prefix. threshold: finite exact int/float, default 1.0. |
| text_transform | pattern: exact str, compilable Python regex, default whitespace pattern. replacement: exact str, valid substitution/backreference grammar for that pattern; default single space. Empty pattern/replacement allowed. |
| aggregator | group_by/value_field: nonempty exact str (literal dictionary keys, not paths), defaults category/value. op: count/sum/mean, default count. |
| threshold_alert | field: nonempty exact str, default value. threshold: finite exact int/float, default 0.0. direction: above/below, default above. Bounds remain inclusive as current templates. |
| field_extractor | fields: exact dict of nonempty exact string names to compilable exact string regex patterns, default {}. Empty mapping/pattern allowed; first capture if any, otherwise full match, as existing code. |

Integers too large to convert to finite float are errors. Numeric strings are
not parameter numbers. Tuples, compiled regex objects and builtin subclasses
are intentionally refused. These are narrowed compatibility choices, not
claims of compatibility with every historically coerced input.

## Runtime numeric/grouping domain

Aggregator/threshold rows that are not dicts retain ordinary skip behavior,
but dict subclasses are refused. Accepted row keys must be exact strings.
Aggregator group values are exact str/int/float/bool/None, finite when numeric.
Present vs missing and typed value are tracked. Two distinct group identities
that render to the same current string label fail, including missing vs the
literal `<missing>`, integer 1 vs string "1", None vs string "None". This preserves
ordinary scalar labels without silently merging different identities.

For sum/mean, exact finite int/float values are accepted, bool/numeric subclasses
refused, other nonnumeric values skipped. Each group's sequential sum is checked
for overflow in input order before any result is produced. Count ignores values.
Threshold accepts finite exact int/float and finite numeric exact strings;
missing/None and nonnumeric strings skip; bool/custom values and nonfinite
numeric strings fail. No item is changed by this helper.

## Mandatory integration seams (peer-owned, not implemented here)

1. Validate post-refiner plan parameters, then validate again before synthesis.
2. Generated modules must carry a self-contained equivalent of this validation,
   or a separately reviewed explicit import dependency. No automatic import or
   registration is invented by this prep. Validate effective runtime overrides
   before regex compilation, scoring, item iteration or result construction.
3. Call runtime preflight on the same stable list/parameters subsequently used
   by the template. Caller must own the list or prevent concurrent mutation.
4. Fix scoring's `weights = weights or _WEIGHTS`: an explicit empty override
   must stay empty, not silently reactivate default weights. This helper accepts
   {} as intentional. Existing score_item bypass remains an integration hole.
5. Require the same validation on every public entry, including score_item.
6. Author/run integrated adversarial tests against the actual generated modules
   and original behavior, then obtain an independent verdict.

## Open decisions and limits

The integration owner must accept or revise the exact builtin-only narrowing,
empty override semantics, lower()-duplicate policy, literal-field policy and
collision-failure policy before wiring. These are candidate v1 decisions, not an
agreed shared API freeze. No change to plans/planner/codegen has occurred.
The six output tests use real synthesize_code and exec only inside authored test
functions; they cover ordinary behavior, not integrated invalid-input refusal.
Regex compilation/substitution validation is not runtime containment: hostile
regexes can be expensive and cancellation/time budgets are separate work.
Input/output text coercion hooks in other existing templates are outside this
numeric/domain prep. Arbitrary item counts, allocation budgets, custom iterable
containment and runtime mutation prevention are not claimed.
