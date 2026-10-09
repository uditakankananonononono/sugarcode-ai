# Strict gap telemetry and sample values

Candidate based on main 54d35492c5746901885ec9cde19086037c5c052f.
This is a new repair, not a reconstruction or rerun of lost review packets.

Contract: gap exemplars and generated-test samples accept exact Python builtins
None, string, bool, integer, finite float, list, tuple and dict. Tuples become
JSON arrays. Dict keys must be exact strings. Numeric subclasses, Decimal,
numpy scalar values and arbitrary objects are refused without calling their
conversion methods. This deliberately replaces default=str coercion, including
coercion of otherwise finite custom values. Maximum nesting depth is 64;
maximum expanded values is 10,000. Shared acyclic containers are allowed;
cycles are refused with InvalidTelemetryValue, not RecursionError.

Event text fields must be strings and timestamps finite int/float, excluding
bool, with absolute value at most 1e12 seconds to keep detector recency
arithmetic bounded. Validation happens before any append. Invalid input leaves the file
unchanged. Fresh writes use strict JSON without NaN/Infinity. Sample validation
also applies to direct test-synthesis calls, not just the telemetry path.

Historical files are not rewritten or silently filtered. Malformed JSON,
nonfinite numbers, bad timestamps or wrong module identities stop reads with
an indexed InvalidTelemetryValue. The original file stays intact. This is a
fail-closed repair requirement, not a migration or quarantine service. A stored
string such as "NaN" remains a string; its former numeric meaning cannot be
recovered. Existing missing optional fields keep their former defaults.

Scope limits: no cross-process locking, file-size/line-size cap, authenticity,
activation permission, model quality or scientific acceptance is claimed.
Depth/value limits bound traversal after JSON decoding, not decoding memory.
JSON serialization may still refuse excessively large integers under the
interpreter's own limits. Old activation/synthesis defects are separate work.
