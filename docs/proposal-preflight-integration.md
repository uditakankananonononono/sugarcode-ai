# Registry proposal preflight and refuse-overwrite policy

Stacked on J02 integrated340479a, current published2aefa5a base. Superseding R01
PREP retained; old9130cf20 discarded. Parent policy2026-10-10: same Unicode
alphanumeric/-/_ safe IDs and nonempty generic kinds as J02, no arbitrary128/ASCII/
six-kind limit. Existing rows unchanged. Filesystem PC_NAME_MAX BYTE limit checked
for code and test filenames before mkdir. No unlimited identifier-size guarantee.

save_proposal now holds process-local registry lock: strict raw registry/module
validation and identity/source/path/existing-key/destination preflight BEFORE
mkdir/file writes; records digest rechecked before creation. Both candidate files
exclusive 'xb' create, never overwrite. Existing identical-key retry also refuses,
not successful idempotent replay. Foreign/malformed registry, occupied destination,
observed symlink/nonplain directory and unsafe ID refuse before new candidate IO.
UTF8 encoding strict, invalid source refuses. Normal generic/Unicode caller passes.

On failure before registry replacement remove only candidate files opened by this
attempt; no removal of preexisting destinations. Cleanup failure can leave orphans.
On AtomicDurabilityError(replaced=True), keep files because new registry references
them; caller must read named proposal key before retry. Candidate directory may
remain empty after a later failure. Sources are not AST/safety/quality validated.

NO hostile filesystem race security claim: process lock does not stop external
writers; ancestor/registry reads are lstat+read and have TOCTOU windows. Exclusive
final-file creation protects collision overwrite only, not swapped-directory
containment. Registry digest detects one snapshot change, not authenticity or
future concurrent change. No symlink-proof dirfd chain, cross-process lock,
startup CAS, cross-file crash atomicity, complete cleanup or exactly-once claim.
Hard crash between files and registry can leave orphans; no automatic migration.
Low-level registry remains trusted API, not human consent. Atomic file replacement
is single-file only. Existing candidate corpus/policy compatibility not fully mined.

Peer tests originally encode ASCII/128/six-kind proposals; eight rejected-domain
cases changed/removed according to explicitly approved integration policy,54 remain
and pass. Added10 actual save_proposal tests incl corrupt registry before mkdir,
retry/conflict unchanged, unsafe ID, pre/postreplace failure, Unicode/generic/
filesystem NAME_MAX. Selected480 PASS/no skips (J02 stack416+54+10), not an
independent/full configured-suite verdict. Initial stale-signature edit62 TypeError
failures and filesystem long-name478 PASS/1 FAIL were non-green builder probes.
No tests are presented as peer-run. Independent verdict and J02 dependency required.
