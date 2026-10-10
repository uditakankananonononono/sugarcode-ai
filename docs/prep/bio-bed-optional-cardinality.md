# BIO-BED-OPTIONAL-FIELD-CARDINALITY preparation

PREP-NORUN. Additive helper, fixtures and authored tests only. No edits to old
product files or integration; no runtime/import/test result. Peer owns integration
and independent verification. Base 2bc7f7d9951b8d73be37e1e9ef0979c28c482e62.

## Precise partial-width model

BedPrefixRow is a frozen dataclass containing tokens and values, exact tuples of
length field_count (3..12). Tokens retain input spelling, values contain typed
integers and tuple block arrays. All columns correspond to FIELDS[:width].
Absent fields are absent, not null/default. as_record converts arrays to fresh
lists for existing product key conventions. Parsed rows are immutable; caller
forgery is revalidated at write. No fields added to existing product records yet.

- BED7 has thick_start alone; no thick_end, no complete thick interval.
- BED10 has block_count alone; no sizes/starts and no block geometry.
- BED11 has block_count and block_sizes; count/positive sizes checked locally,
  but no block_starts or spatial placement inference.
- Full thick group only exists at width >=8; full block group only at width 12.

Writer complete-group requirement is interpreted precisely: full groups are
emitted only when complete, while partial widths emit their individual present
prefix columns, never substitute complete-group semantics or synthesize fields.
Rejecting all partial emission would contradict the approved all-width roundtrip
requirement. Integration must preserve explicit width/tokens in its chosen model;
passing partial dictionaries to the original writer still loses fields/crashes.

## API

parse_bed_prefix_line(line: str, *, line_number: int) -> BedPrefixRow
write_bed_prefix_line(row: BedPrefixRow, *, line_number: int) -> str
No newline returned by writer. Parser accepts one LF/CRLF ending or a bare trailing CR, not embedded
boundaries. Caller owns blank/header classification and file/text reads. Numeric
errors and malformed present fields raise ValueError with line context.

Existing start/end constraints and strand domain preserved. Score must be a lexical ASCII INTEGER 0..1000: the exact grammar is [0-9]+,
with no sign, whitespace, decimal point, exponent, underscores or Unicode digits.
Leading zeros are admitted and their exact lexical spelling is preserved.
50.0, fractional values and out-of-range integers refuse with line-context
ValueError. Typed score is an exact int, never float. thick_start is checked against interval
already at BED7. Complete thick pair additionally checks ordering. Count positive;
BED11 sizes must match count and be positive <= span; BED12 adds starts count,
first zero, nonnegative offsets and end containment. item_rgb remains text, as in
old parser. Overlap/order-of-block policy is not expanded. Semantic defaults,
coordinate algorithms and scientific accuracy claims are outside scope.

## Source-supported defect and compatibility

bed.py:23-27 allows 3..12; :46-50 drops BED7 thick_start; :53-58 accesses indices
10/11 on BED10/11 and catches only ValueError. :88-95 writes only full groups.
Existing tests/test_bio_bed.py has BED6/12 fixtures and no partial-width canaries.
Original product remains unchanged, so defect remains until peer integration.
New fixture compares old valid BED3/6/8/9/12 outputs. Writer retains admitted integer lexical
spelling while old writer normalizes score; equality holds for existing fixture,
not every arbitrary lexical representation. Old parser admits floats and values
outside 0..1000; those are now explicitly rejected by the settled score policy. Complete block_count=0 historically
fails on empty sizes/starts; new positive-count policy must be reviewed against
legacy corpora. BED7 bounds and BED11 sizes are newly meaningful validation.

No predecode byte/line or CPU bounds, no streaming-memory guarantee, no universal
security boundary. Broad optional-prefix standards conformance is not claimed.
No imports of old product code in the helper. Existing parser/writer imports in
authored tests are for later peer execution only; none were executed here.

## Peer integration and planned verification (not executed here)

Apply patch on verified base, choose how explicit prefix presence survives
product parse and write, adapt both old product functions, preserve header logic.
Original-source canary tests deliberately expect old faults and should stay tied
to a pristine base comparison, not run unchanged against repaired production.
Suggested separate prep checks: pytest -q tests/test_bed_prefix_schema_prep.py
Suggested production regression after appropriate integration/canary adaptation:
pytest -q tests/test_bio_bed.py tests/test_bed_prefix_schema_prep.py
Peer must run before/after width7/10/11 failure/loss canaries and each admitted
width3..12 roundtrip, malformed line-context cases and real-corpus compatibility.
These commands are plans, not permission to bypass PREP-NORUN or claims of results.

## Score-policy correction delta

Parent prep commit 4c1237793670c46a1bf280dfdff5c792afc0ee40; public base
2bc7f7d9951b8d73be37e1e9ef0979c28c482e62. Earlier float/isfinite prep is historical
and superseded. This correction touches only schema, tests and this contract.
Positive block_count and blocks inside chromEnd remain enforced; all malformed
present values refuse with line context. No product wiring or tests run.
