# Predecode state byte admission

Base2aefa5a. Parent design limits2026-10-10: events/ledger16MiB per file and1MiB
per physical LF line INCLUDING terminator; gate4MiB file; registry16MiB file.
These are engineering defaults, NOT usage-proven capacity/feasibility. Existing
J04 gate whole-state10,000 expanded values still applies, whichever fails first.
No implicit archive/retention/truncation/cap increase.

All four real read paths use bounded binary reader BEFORE UTF8/JSON decode,
with one refusal probe byte, short reads not EOF. Gate/registry code retains its
own exception mapping (limit error may be wrapped with cause on those reads),
JSONL limits propagate InputLimitExceeded with scope/physical line metadata.
No partial rows, malformed/oversized history unchanged. Existing process locks
retained; no concurrent filesystem snapshot guarantee or path-authority boundary.

Events/ledger writes serialize/encode first, enforce matching line cap, bounded
read existing byte history and refuse prospective aggregate cap before append.
Gate/registry full prospective encoded UTF8 size checked before atomic writer.
No fresh admitted record alone poisons state beyond declared byte budget. This
is not repair of previously corrupt history; existing invalid JSON is not reparsed
on append. Each JSONL append rereads full bounded history: O(history bytes) per
append, potentially quadratic work over lifetime. No constant-time scalability
claim; capacity failures surface, never silently evict rows.

Physical LF JSONL, CRLF stripped on terminated rows; bare CR and literal Unicode
separators are DATA, not record boundaries. Valid Unicode separators inside JSON
strings now survive. Legacy bare-CR/Unicode-separated concatenated documents may
refuse where old splitlines accepted; no migration. Error row counts physical LF.
Strict UTF8 after caps. Decoding/copies memory O(cap), not exact RSS/process quota.
FIFO/device/slow filesystem can block; no timeout/global CPU/memory isolation.
Read can observe mixed concurrent writes; symlink/external-writer races unclosed.

Builder peer44 authored cases PASS,15 real-wiring cases PASS. Selected369 PASS/no
skips (base310+44+15), covering four readers before decoder, four write caps,
JSONL line/aggregate cap, CRLF/Unicode and legacy-CR refusal. Independent verdict
required. J02/J05/R01 pending branches not included; integration after their
landings must preserve byte paths. Source PREP attribution 'J04 peer-owned' is
historical incorrect text, not authority or current ownership.

Independent VERIFIED caps verdict369PASS reproduced, SCOPED registry reconciliation.
Landed reconciliation preserves J02 strict decoder after capped bytes; R01 raw
preflight/generation reads capped as well. Combined boundary cases exact cap,
one-over, strict duplicate JSON and oversize proposal preflight/no candidate IO.
Registry read cap maps RegistryError with InputLimitExceeded cause; JSONL direct
ValueError subclass. Existing _log can fail after other state mutation (J01 residue).
No RSS/CPU, FIFO timeout, path authority, writer race or corruption repair claim.
