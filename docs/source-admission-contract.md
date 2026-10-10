# Bounded source admission preparation

Base published4b70845f912eaf044ba033d3eb86b74d3c4811ac, new files only.
This unit is helper + contract + tests. It does NOT change any existing caller,
close production unbounded reads, migrate active features, or choose production
source budgets. Proposed1MiB code and1MiB tests match isolated dispatch's existing
post-read code ceiling; explicit caller caps always required, no hidden defaults.
Six new P01-generated default templates fit the proposal, NOT general feasibility
proof. No PRIDICT/model/research artifact changes.

## Actual current seams from source inspection

- engine.evaluate passes an in-memory Candidate to sandbox.run; evaluate itself
  does not read code/test files. sandbox and IsolatedRunner write strings before
  running tests. source strings can already be large before any admission.
- registry.activate reads candidate using read_text(UTF8), hashes re-encoded text
  with universal-newline normalization, then copyfile rereads the path. Snapshot
  integration would change CRLF checksum semantics and copy behavior, a future
  deliberate compatibility decision, NOT repaired here.
- registry.dispatch hashes unbounded read_bytes then importlib loader rereads path.
  isolated_dispatch reads unbounded code first then checks its1MiB limit. Both
  need future wiring to consume approved immutable bytes, not re-read same path.
- R01 proposal preflight encodes supplied source strings, candidate hash properties
  also encode strings; no source admission integration there today.

## Helper API

SourceLimits(code_bytes, test_bytes): exact nonnegative builtin ints, two independent
UTF8/raw byte ceilings. Empty source admitted as bytes, no syntax/run claim.
SourceSnapshot frozen(content bytes, text str, sha256 hex), original raw bytes are
hashed before strict UTF8 decode, no newline rewrite. BOM kept. Expected digest
optional but if supplied must be lowercase64hex and match. Hash integrity relative
to supplied digest is not identity/authorship/approval or source safety.

read_source_snapshot(path, max_bytes, expected_sha256=None): POSIX/Linux open
O_NOFOLLOW|O_NONBLOCK, fstat regular descriptor, bounded reads with at most cap+1
bytes consumed. No pre-stat size shortcut; short reads continue; zero cap valid.
Final symlink/device/FIFO refuses, descriptor closed success or error. Ancestors
not contained; trusted pathname/source selection belongs to future caller.
Regular files can change concurrently during reads; no immutable generation/CAS.
read_candidate_sources returns both code/test snapshots only after both pass,
not atomic two-file capture. No partial result or file writes on refusal.

admit_source_text validates exact builtin string then character-length lower bound
and chunked UTF8 byte admission, rather than encode entire huge string first.
At most16,384characters encoded per chunk (up to65,536bytes transient); copies
bounded by admitted cap plus chunk. Caller string already allocated, cannot undo
that memory use. Surrogate/nonUTF8 refused; source subclass hooks not executed.
admit_candidate_text returns both only after successful independent admission.

## Error and compatibility boundaries

InputLimitExceeded(ValueError) propagated with source scope/cap. Invalid limits,
string types/digest mismatch/nonregular descriptors ValueError. Invalid UTF8 or
surrogate encoding native Unicode errors. Final symlink/missing/permission/read
failure OSError; no error normalization. MemoryError/overflow/system IO unwrapped.
Bounded bytes not exact process RSS/CPU/timeout guarantee. O_NONBLOCK avoids FIFO
blocking but slow regular filesystem IO can still block. No ancestor symlink or
path authority containment, file locking, cross-process transaction or hostile
filesystem snapshot guarantee. No signature/authentication, AST safety, regex
budget, loader execution isolation, test trust, or result-validation claims.

Future wiring must use snapshot.content for copy/write/execute/hash and not let
loader or copyfile re-open old path. Production cap policy and CRLF hash change
need review before wiring. No approved existing behavior change in this unit.

## Evidence

33 new cases actually run, covering exact/one-over incl actual1MiB, UTF8 ordering,
CRLF/BOM preservation, hashes, FIFO/final symlink refusal before read, short reads
cap+1, descriptor closure on limit and IO error, custom strings, independent pair
caps, no partial output, snapshot survives later path replacement, and six real
P01-generated code/test pairs with proposed limits. Normal code paths remain
unwired. Test suite results/denominators in packet; independent verdict required.

Production caller integration is now described in source-snapshot-wiring.md.
Historical base/unwired/proposed-only statements above describe original helper
landing, not the later integration. Approved caller code/test caps are 1 MiB each.
