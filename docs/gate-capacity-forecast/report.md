# Gate capacity/headroom forecast - PREP-NORUN

Pinned base: `6e1a42145e529d50751ec3b5cedc6d6ff3105f60`.
All product path references below are relative to `src/sugarcode/self_improve/`
and refer to that exact base. This report is source analysis, not a runtime verdict.
Live usage volume is UNKNOWN. No private snapshot was supplied or inspected.
No capacity relief, cleanup, archive eligibility or installed forecast API exists.

## Admission constraints in actual code

- Raw read: `capped_readers.py:12,32-67` and `gate.py:77-88` admit at most
  4*1024*1024 raw bytes, before strict UTF-8/JSON decoding. Exact cap is allowed;
  cap+1 refuses. Whitespace counts, whether useful or not. Stored duplicate keys,
  NaN/Infinity or overflowing float literals refuse (`gate.py:32-49,80-88`).
- Expanded values: `json_values.py:19-25,40-51` count one visit for root,
  containers and scalar children, NOT dict keys. Keys must be exact strings.
  Aliases count per expansion; active-path cycles refuse. Tuples become arrays.
  Exactly 10,000 visits fit; visit 10,001 refuses. Root depth is zero, visits at
  depth 64 fit and 65 refuse. Custom inputs/nonfinite numbers refuse
  (`json_values.py:26-38`). `{key: scalar}` costs two visits. The offered phrase
  "keys count, not values" was corrected by the coordinator to this semantics.
- Encoded write: `gate.py:90-99` snapshots first, then dumps with indent=2,
  sort_keys=True, allow_nan=False and default ensure_ascii=True, then measures
  UTF-8 bytes against the same 4MiB cap. ASCII escapes count physically; `é`
  is six escape characters inside its quoted token, astral characters use two
  surrogate escapes, and lone surrogate strings are escaped rather than raw UTF-8.
  Tests contain the serializer comparison; no calculation was executed here.
- Read/write asymmetry: `_load` checks raw JSON, not snapshot value/depth limits;
  `_save` checks both. A compact syntactically valid dictionary can load yet block
  all append-only requests and status-only decisions retaining the oversized subtree.
  This is not universal write impossibility: UUID replacement of the offending
  record can produce an admitted smaller state (`gate.py:103-117`). Canonical indent/escaping can also exhaust
  write bytes while raw read bytes fit (`gate.py:77-99`). Negative canonical
  byte headroom means baseline is already unsavable, not extra allowance.

## Request and decision are different semantic operations

`gate.py:101-115` generates `si-` plus 12 UUID hex characters, builds an eight-field
record and calls validate_record; it does NOT call validate_payload or check_binding.
Unknown nonempty action strings/generic dict payloads can pass this envelope check
(`approval_schema.py:81-128` versus separate `131-185`). No binding/authentication
claim follows from successful capacity admission.

`gate.py:124-142` accepts approved/rejected decision arguments, requires an existing
record with pending/approved/rejected status, overwrites status/decided_at, and adds
or overwrites decided_by. A preexisting decided_at scalar replaces a scalar visit;
a newly added decided_by contributes one visit plus its expanded children if a
legacy value is a container. A legacy minimal status-only record gains two visits.
Full records containing action_type receive validate_record; legacy records lacking
that field do not. Full envelopes permit null decided_by but reject empty string,
number or container actors (`approval_schema.py:114-127`); legacy generic decisions
can retain those JSON-compatible values. Tests compare both paths with real gate
methods in synthetic temporary directories when the auditor executes them.

`gate.py:103,106` does not detect UUID-prefix collision: insertion overwrites an
existing ID. A "more approvals" calculation must require distinct generated IDs,
not interpret this replacement as additional capacity. Test seams pin timestamps
to 1000.0 and UUID hex to a declared exact 32-character value; repeat fixtures use
unique fixed-width lowercase 12-hex IDs. No random average or live timing forecast.

## Measurable headroom and exact-shape example

For an admitted explicit snapshot: raw headroom = 4MiB minus source bytes;
value headroom = 10,000 minus expanded visits; depth headroom = 64 minus deepest
visit; canonical byte headroom = 4MiB minus canonical UTF-8 bytes. These four
metrics cannot substitute for one another. Depth headroom is available nesting
levels, not approval count. A prospective operation must rebuild/remeasure its
actual resulting whole state and report the first applicable refusal.

Under ONLY the test's exact unique ID, empty payload, fixed module/action/summary,
timestamp 1000.0, pending envelope, no actor, and no initial records, the root
consumes one visit and each request consumes nine visits. Tests author 1111 versus
1112 record boundary checks including encoded byte admission. This is not a generic
approval guarantee. Other payloads/actors/statuses/escaping/history change the result.
Numeric timestamp ranges do not alone determine string lengths: the report schema
must declare exact values or conservative enumerated serialization bounds.

Terminal status and old age grant ZERO archive eligibility. No read code supplies
archive/TTL/deletion authority (`gate.py:77-165`); no files are deleted by this unit.
Lower limits, reserve margins, administrative policies and cap changes would be
proposed decisions, not current installed policy. Forecasting capacity does not
predict disk space, atomic durability or lock availability; `state_lock.py:33-105`
is cooperating POSIX advisory locking, not protection from external editors.

## Auditor reproduction, not executed by builder

From an isolated checkout of the pinned base plus this delta, Linux/POSIX with
Python >=3.10 and pytest >=7 (repo pyproject.toml project/dev settings):

```
PYTHONPATH=src python3 -m pytest -q tests/self_improve/test_gate_capacity_forecast_prep.py
```

Synthetic fixtures only, no secrets, private data, services or live gate paths.
Exact point timestamp/UUID seams are declared in the test source. Parameterized
product comparisons cover raw/write caps, expansion/depth, statuses/envelopes,
null actors, domain refusal causes and wrong-reference mutant sentinels.
All tests are AUTHORED NOT RUN. No syntax/AST checks or product imports/execution
were performed. Source-based analysis can be wrong; independent auditor execution,
mutation validation and landing remain outstanding. Runtime errors such as lock,
filesystem or serializer implementation limits must not be reclassified as capacity
success. Other Python versions/implementations may need reproduction review.

## Repair-round qualifications and mutation reproduction

Source refusals now return baseline unavailable_reason and prospective refusal
with stage=source/provenance gate.py:77-88. Raw over-cap, duplicate/nonfinite,
nonobject, invalid UTF-8 and malformed JSON cases are authored against real _load.
Real _save comparisons are added for both exact repeat boundaries, including
unchanged bytes on rejection. Fixed-shape encoded assertions use 225*n+2,
derived from the declared pretty-printed envelope layout, not measured by builder.
The peer reported initial independent execution success; revised tests remain NOT RUN.

Reference traversal prevalidates dictionary key types before child descent and
checks count before depth. Product visits dictionary entries in order, checks
count/depth together, and can encounter an earlier child-domain failure before a
later invalid key (`json_values.py:21-45`). Thus mixed-invalid-domain reference
reason is diagnostic, not guaranteed identical first-error priority. Auditor must
use single-fault probes for reason equality and actual gate cause for mixed inputs.
Baseline unsavability never proves all mutations refuse; collision repair is tested.

Actual function-source mutant reruns are reproducible by the auditor only:

```
for m in count_keys deduplicate_alias utf8 drop_indent drop_sort; do
  if GATE_FORECAST_MUTANT="$m" PYTHONPATH=src python3 -m pytest -q \
    tests/self_improve/test_gate_capacity_forecast_prep.py -k wrong_reference_mutants; then
    echo "surviving mutant: $m"; exit 1
  fi
done
```

Each selected mutation rewrites the reference function source inside its test,
executes only that synthetic mutated function, and must fail unchanged fixed
count/byte oracle assertions. Unselected standard suite should pass. Auditor must
confirm failure is the oracle assertion, not collection/import/setup failure.
No mutant or test execution occurred here. Bundle exports HEAD; commit identity,
not transport of a named branch, is verified. Local branch is only local metadata.
