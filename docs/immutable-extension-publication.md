# Immutable POSIX extension publication and read-only evidence

Base e36fb2a. Destination must be absent, including final symlink/FIFO/directory.
Matching bytes do NOT permit adoption/retry/overwrite. Existing next-version
orphan blocks activation, SourcePublicationError directs reconciliation.

Protocol under cooperating registry lock: source snapshot admitted; complete
prospective registry+consumption schema/cap validated; private 0600 temp written
with short-write loop, file fsync; exclusive hardlink name publication (EEXIST
refusal, no overwrite rename fallback); directory fsync; temp unlink; directory
fsync. Published bytes re-read/hash-verified before registry commit. Only then
F01 atomic registry replacement. Direct low-level API still trusted, engine gate
coordination/consumption unchanged. No all-files-atomic, no exact-once, no tamperproof
registry. POSIX supported link/fsync only; unavailable operation fail-closed.

Typed failure carries published,destination,candidate_key,registry_committed.
Publication failure before link published=False; after link True. Registry
postreplace durability failure committed=True (visible but durability uncertain);
other commit exceptions committed=None (unknown, inspect authoritative JSON).
No blind retry. Published source ALWAYS retained on failure, no automatic orphan
repair/adoption/version skip/journal replay. Temp retained before successful unlink;
if final directory sync fails AFTER unlink, only the complete final file remains.
This is not all-failures temp retention. Crash can leave unreferenced file or partial hidden
temp; source final name never exposed by this protocol until complete file fsync.
No ownership/ACL/xattr preservation. Later logger failure remains separate.

reconcile_extensions holds same lock, reads strict registry snapshot/fingerprint,
compares ALL referenced versions including inactive ones against actual extension
directory. Bounded raw1MiB descriptor hash, no execution, reports referenced,
missing/mismatch, unreferenced,publish_temp,nonregular,read_refused with reason type.
10,000 total output and distinct reference entries bound, refuses oversized dir;
enumeration/ref scanning still filesystem/CPU cost, not global deadline/RSS quota.
Fingerprint describes read bytes; evidence NOW not permission/reservation. Sidecar
lock may already exist; routine never changes artifacts/registry. Earlier unsafe
files remain unsafe, no inferred cold-history/deletion eligibility.

Exclusions: cross-file journal/automatic recovery, source/authorship authority,
host-effect rollback, noncooperating writer/ancestor/sidecar/hardlink races, Windows,
distributed transaction, system IO hangs, crashproof storage beyond POSIX fsync
contract. Directory link can become visible before directory fsync; failure is
retained for inspection. After publication external actors can still replace bytes.
No all-files-atomic, no exact-once, no tamperproof registry.

21 new parameterized cases PASS. Actual subprocess SIGKILL cutpoints with event
handshake: temp_fsynced, name_published, published_dir_fsynced,
temp_removed_fsynced, before_registry_commit, registry_committed. Fresh object
restart uses strict JSON/report: before registry cut old state + retained source
(or temp-only), after commit new state + complete referenced source. Kills model
process crashes, NOT power loss/fsync correctness proof. Partial visibility test
pauses INSIDE short-write call after first3 bytes, main reader inspects ABSENT
final path while writer held; not a mere start-barrier. Cooperating concurrency
lock/consumption tests remain in broad selection, not reraised as new coverage.

Mutation: oldbase overwrite1FAIL/candidatePASS (pure helper copied for import,
production old registry unchanged). Exclusivepublish->overwrite1FAIL; skip file
fsync1FAIL; premature JSONcommit5FAIL/1aftercommitPASS; destructive report1FAIL.
Candidate counterparts PASS. Early destructive mutant1PASS because cap probe
refused before hitting temp; added ordinary full report unchanged-tree assertion,
reran mutant1FAIL. Initial partial-write test incorrectly assumed pathlib.glob
hides dot files1FAIL, fixed assertion preserving forced interleaving, no production
change. Historical incomplete temp/fsync proof not expanded to physical crashproof
claim. No full configured-suite claim; independent auditor before landing.

Bounded audit corrections: 10,000 maximum is now NON-relaxable through max_entries;
values above 10,000 refuse. Typed publication error preserved when close fails:
descriptor ownership cleared before close, cleanup close errors never mask primary
status, no unsafe double-close. Temp unlink can succeed before final dir fsync fails;
in that case final file retained, temp absent (not all-failure temp retention).
25 new final-source cases PASS, selected 1,176 PASS = 1,151 prior + 25, no skips.
Initial packet unit XML was stale at 20 cases vs 21 source; corrected final unit
receipt regenerated. Git bundle supplies candidate commit provenance for recheck.
