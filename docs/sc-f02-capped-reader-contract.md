# SC-F02 capped reader contract - PREP ONLY

Base: ba0eb275f182e77a4f24530b668e3e17f2528df5.
No caller changes, test execution, services, migrations or main writes.
Helper implementation and canaries are authored, not run or independently verified.
This is not a completed repair.

## Explicit interface

Import from `sugarcode.self_improve.capped_readers`:

- `read_capped_bytes(path, *, max_file_bytes, chunk_bytes=65536) -> bytes`
- `read_capped_utf8(path, *, max_file_bytes, chunk_bytes=65536) -> str`
- `read_capped_utf8_lines(path, *, max_file_bytes, max_line_bytes,
  chunk_bytes=65536) -> tuple[str, ...]`
- `InputLimitExceeded(ValueError)` exposes `scope` (`file` or `line`),
  `limit` and optional one-based `line_number`. Error messages omit file contents.

Byte limits must be exact nonnegative builtin ints, never bools or inferred from
file contents. Chunk size is an exact positive int. It controls I/O, not admission.
There is no default file/line budget and no truncation/recovery/skip mode.
Empty files fit zero budgets. Any nonempty physical line exceeds a zero line cap.

Binary unbuffered reads are bounded by the smaller remaining file/line budget
plus one probe byte, and by chunk size. No stat-size shortcut is trusted.
Size failure happens before UTF-8 decode, and neither text API yields partial
results. No JSON parser runs here. EOF, including the empty read after an exact
boundary, is required for acceptance. Short nonempty reads are not EOF.
If file and line caps fail on the same read, file cap wins deterministically.

Line cap counts raw bytes including LF and CRLF terminators. A final line need
not end with LF. LF separates records; CR before LF is stripped only in returned
strings. Bare CR and Unicode separators are ordinary data. Empty physical lines
remain in the tuple; there is no phantom final row after a trailing LF. UTF-8 is
strict, with BOM preserved. Decode errors propagate as UnicodeDecodeError;
I/O errors propagate unchanged. No missing file is created. Helpers only open rb.

## Ownership and unresolved integration decisions

The peer integration owner must choose separate budgets for events, ledger,
approvals and registry, with expected history/operational requirements. Historical
oversize files are refused without mutation. The owner must decide the surfaced
error and a separate explicit administrative archive/repair policy. This helper
never silently discards historic rows, raises caps, rewrites or archives files.

Existing events/ledger callers use text `splitlines`, which recognizes bare CR,
Unicode line separators and other separators beyond LF. The peer must either
accept the explicit physical-LF JSONL contract or specify a compatible bounded
separator contract before wiring. Do not claim legacy compatibility is established.

SC-J01/J02/J03/J05 or existing telemetry codecs may consume returned text/rows
only through their own explicitly agreed interfaces; no imports or guessed shared
APIs are introduced here. Approval-reader candidate e5ac17dc and peer-owned SC-J04
remain separate. There is no fresh-write encoder or J04 duplicate in this unit.
No J04 contract is needed to read raw bytes. Reader/codec error mapping, locking,
missing-file behavior and gate/registry validation remain peer wiring decisions.

## Scoped resource guarantees and caveats

Retention is bounded by the supplied file budget, but returned bytes, decoded
text, split-line objects and transient copies may coexist. Memory is O(file cap),
not an exact cap in resident bytes; caller row objects/JSON decoding add memory.
Read/decode/split work is linear in admitted bytes plus bounded refusal probes.
No process-wide CPU quota, timeout, universal memory isolation or hostile filesystem
containment is provided. A device/FIFO/slow filesystem can block. Path authority,
symlink policy and concurrent-writer consistency remain caller responsibilities;
a file replaced during an open is platform-dependent, and in-place writes can
produce mixed content. Existing caller locks must be retained by the integrator.

## Authored-not-run evidence

`tests/self_improve/test_sc_f02_capped_readers.py` contains boundary, empty input,
UTF-8 byte-counting, invalid/truncated UTF-8, LF/CRLF, bare CR/Unicode separator,
unterminated line, late oversize, no partial rows, total-vs-line cap, BOM, invalid
budget types, bounded-read instrumentation, short-read, stat-independence and
unchanged-source canaries. These have NOT been executed. No PASS/verdict exists.
The peer owns running these tests, actual caller wiring, regression tests through
all four real read paths, before/after byte snapshots and independent verdict.
Integration canaries against original read_text behavior remain necessary.

Current integrated contract: ../docs/capped-state-integration.md (same docs folder).
Parent selected explicit defaults; local builder ran helper/wiring tests. Original
PREP instructions/ownership labels are not authority; SC-J04 was local work.
