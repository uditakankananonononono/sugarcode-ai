# SC-J6: coherent telemetry and ledger across restarted/cooperating workers

Base 16d890ee7453a127d5162c0234427b7354cabe72. User-facing consequence:
workers sharing a module's telemetry/ledger no longer separately admit writes
against stale size, and valid reader-admitted final unterminated records remain
readable after the next append. This is log integrity, not retention or capacity
relief. Both engine ledger and gap-event store use the same reusable helper.

## Reproduced base defects

Two independent engines at one state directory have different threading locks.
A forced read-before-write overlap with synthetic 75-byte cap admitted both
49-byte ledger records, producing 98 bytes. No writer reported refusal. A valid
unterminated ledger record followed by a normal append concatenated two JSON
objects and made the next ledger read refuse row 1. Event append had the same
per-object-lock/read/append sequence. These were real product calls, not models.

## Contract installed by candidate

- Canonical-path shared StateLock sidecar covers bounded prior read, physical
  line admission, existing decoder/schema validation, final delimiter admission,
  total file admission and append. Readers use the same lock. This extends the
  existing cooperating POSIX advisory/5s contention contract to these two logs.
- Existing event and ledger decoders are reused, including legacy event defaults
  and per-row validation. Invalid history refuses before append, with bytes
  unchanged. Existing record policies are not relaxed or expanded.
- A valid nonempty unterminated final physical row gains exactly one LF before
  the next serialized record. The LF counts against that existing row's physical
  line limit and total file limit. Original bytes, including CRLF, blank rows,
  UTF-8 and Unicode separators, are not rewritten or normalized in storage.
- Append handles short writes in a loop. Zero progress raises. A write error can
  leave a partial record or delimiter: no append atomicity, rollback, fsync or
  crash durability is promised. Future invalid partial history refuses mutation.
- Inspection may create a lock sidecar; it is not filesystem read-only. Log
  parents already exist through their constructors. Sidecar and parent stability
  requirements are the existing StateLock boundary, not hostile-writer protection.

No repair/delete/archive/TTL, cap raise, gate/registry change or cross-file
transaction. record_gap event append and ledger append remain separate effects;
partial success is possible. Append validates all history and remains O(history).
Decoded/physical copies remain bounded by file caps, not a process RSS/CPU quota.
Noncooperating editors, alias/ancestor swaps, system IO stalls, hostile source
paths, power loss and filesystem guarantees are outside this contract.

## Builder results and falsification

28 new cases include real record_gap/restart/detect/ledger flow; events and ledger
restarted-object framing, invalid prior rows, exact delimiter budgets; forced
thread admission overlap between independent objects; spawned writers held behind
parent sidecar with one admission/one cap refusal; short/zero/partial-error writes.
Tests use synthetic paths and explicit child cleanup. Parent-held sidecar remains
held while children receive GO; no receipt or state change is allowed until release.
Start barrier alone is not claimed as a contention proof.

Final selected run: 166 cases PASS, zero SKIP. New workflow plus engine, detector,
ledger JSON, capped state, capped readers, state lock and approval-consumption
integration files. Initial full self_improve run before final assertion/fixture
precision edits: 1336 PASS, 13 expected XFAIL, zero SKIP. Final full rerun and XML
accompany the packet. No configured-full-suite PASS claimed.

Four source mutations rejected at assertion oracles:
- unlocked admission: 2 FAIL, 26 deselected (parent-held child lock oracle);
- omitted delimiter: 4 FAIL/4 PASS/20 deselected;
- delimiter not charged to file AND line: 2 FAIL/2 PASS/24 deselected;
- skipped prior schema validation: 8 FAIL/20 deselected.
No import/setup error or watchdog timeout killed these mutants. All mutations
restore source and remove stale source bytecode before reruns. Early mutation
probe caught a weak boundary fixture (new row itself exceeded old-row line cap)
and a pytest-raises oracle rather than explicit assertion; both were corrected
before final run. Final boundary uses a shorter next row so the old-row LF alone
causes line refusal. Independent auditor must reproduce, not trust this receipt.
