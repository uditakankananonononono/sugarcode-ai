# Unit C: orphan recovery journal design, candidate v1

DESIGN ONLY / PREP-NORUN. Public inspected base:
6e1a42145e529d50751ec3b5cedc6d6ff3105f60. No recovery helper,
product imports, filesystem experiments, deletion, adoption or integration.
An authored model is not a repair or evidence of durable recovery.

## Source observations and mismatches

- immutable_source.publish_source writes a private exclusive temp, fsyncs its
  bytes, hardlinks an absent destination, syncs directory, unlinks temp, syncs
  directory. Publication errors preserve residue rather than overwrite/adopt.
- registry.activate computes version = len(versions)+1 and publishes BEFORE
  registry replacement. A complete orphan at that name blocks the next attempt
  with EEXIST. Allocating a higher number or selecting newest by mtime is unsafe.
- registry.activate pre-encodes the prospective JSON, including consumption when
  engine_gate_identity is supplied. _save atomically replaces ONE registry file.
  AtomicDurabilityError indicates replacement visible, directory durability not
  confirmed. Other exceptions after publication set registry_committed=None.
- Checkpoint registry_committed occurs only after _save returns successfully.
  Postreplace directory-sync failure therefore skips this checkpoint even though
  registry and consumption have changed. Exception flags are not read authority.
- Reconcile reads every version reference, including inactive versions, but is
  an evidence snapshot only. It confers no adoption or deletion permission.
- Engine holds gate then registry locks and checks approval binding. Direct
  registry.activate without engine_gate_identity is a documented trusted bypass.
  It does not add consumption. Never infer coordinated approval from a filename.
- Stable sidecar locks are cooperating POSIX advisory locks. Hardlinks, ancestor
  swaps and noncooperating edits remain outside containment. No journal exists;
  no monotonic generation is present in current registry. Journal/generation
  fields below are proposals and require independently audited implementation.

## Notation and crash matrix for existing behavior

R0 = exact preactivation registry JSON; R1 = prospective complete JSON with new
version reference, active pointer and proposal activated. C0 = prior consumption
map; C1 = C0 plus bound engine consumption record. Bypass path: C1=C0.
D = destination; T = source temp; A = registry replacement temp. All preexisting
referenced files, including inactive versions, remain unchanged at every cut.
Old active version is effective under R0; newly referenced version under R1.
The matrix assumes initially absent D and normal cooperating POSIX operation.

| Last checkpoint / cut | Visible registry JSON | D / T | Consumption | Recovery classification |
| --- | --- | --- | --- | --- |
| temp_fsynced | R0 | D absent; T complete, file-fsynced, directory entry not synced | C0 | temp-only evidence, no activation |
| name_published | R0 | D and T hardlinks to complete bytes; directory publication not synced | C0 | published orphan, uncertain name durability |
| published_dir_fsynced | R0 | D and T complete; publication directory synced | C0 | published orphan with completed publication barrier |
| temp_removed_fsynced | R0 | D complete, T absent; removal directory synced | C0 | published orphan without temp |
| before_registry_commit | R0 | D complete, T absent; source publication returned | C0 | published orphan before JSON write |
| registry_committed | R1 | D complete, T absent; registry replacement and directory sync returned | C1 | committed reference and consumption; never reactivate/reconsume |
| during registry temp write/fsync, before replace | R0 | D complete; T absent; A may remain after hard kill | C0 | orphan + untrusted replacement temp |
| after registry replace, before/failed directory sync | R1 visible in current process environment | D complete; T absent; A renamed away | C1 visible | replaced, durability uncertain; read authoritative state, no blind retry |

SIGKILL terminates a process, not kernel/page cache or hardware. After a kill at
these handshaked checkpoints on a normal running OS, expect the visible states
above; kill does not validate successful fsync persistence. Power loss before a
name's directory barrier may lose/reorder that name. Even after completed fsync,
claims depend on filesystem, OS, device and mount honoring barriers. Following
reboot, inspect exact JSON/file bytes: do not infer R0/R1 from last journal stage.
Missing/corrupt JSON or referenced file means HOLD, not a guessed older/newer
state. R0/C1 and R1/C0 are impossible for the same coordinated registry snapshot
under ordinary single replacement; detecting them means mismatched observations,
legacy/bypass path, corruption or outside edits, requiring HOLD.

Final source directory-sync failure can happen AFTER unlink T: published=True,
D exists, T absent, registry still R0/C0. Temp absence is not proof of registry
commit or proof the source operation fully succeeded. Ordinary prepublication
errors may leave partial T; never treat it as an admitted source snapshot.

## Finite state machine (proposed, not implemented)

States: INTENT, TEMP_EVIDENCE, PUBLISHED_EVIDENCE, SOURCE_SYNCED,
SOURCE_FINALIZED, REGISTRY_PENDING, REPLACED_UNCERTAIN, COMMITTED,
HOLD, QUARANTINE_PENDING, QUARANTINED, REMOVAL_PENDING, REMOVED.

Normal observed edges: INTENT -> TEMP_EVIDENCE -> PUBLISHED_EVIDENCE ->
SOURCE_SYNCED -> SOURCE_FINALIZED -> REGISTRY_PENDING -> COMMITTED.
Replacement visible but final durability unknown -> REPLACED_UNCERTAIN.
Every state can -> HOLD upon stale/different/missing authority, generation,
digest, identity, references, unsupported durability or malformed journal.
Restart begins authoritative inspection, NOT automatic replay of the last edge.
Exact R1 and matching D/consumption -> COMMITTED observation, even with stale
journal. Exact R0 and matching D -> orphan HOLD with owner decision requested.
Unknown JSON -> HOLD. COMMITTED is not reopened by later rollback/inactive state.

Decision edges (owner-authorized, later implementation only):
- HOLD -> REGISTRY_PENDING forward adoption ONLY if exact orphan identity,
  R0 generation/digest, candidate snapshot, admission evidence and current
  approval binding all match and owner selects adoption. Revalidate under gate
  then registry lock; commit full reference/proposal/consumption in ONE JSON.
- HOLD -> QUARANTINE_PENDING -> QUARANTINED: preserve original in place by
  logical quarantine/deny-dispatch record by default. If physical isolation is
  requested, record source/destination digests and every intermediate copy/name
  state; never overwrite originals or a referenced path. Journal authority alone
  cannot move a file. Physical move requires separate approved mechanics.
- HOLD/QUARANTINED -> REMOVAL_PENDING -> REMOVED ONLY with explicit owner
  authorization naming exact artifacts, after fresh full reference check and
  preservation/export evidence. No deletion is approved by this design.
- COMMITTED rollback uses a new approved pinned rollback request and records new
  consumption, preserves every version/file and existing consumed record. It is
  a compensating state transition, never an erase/retry of the original commit.

## Journal schema proposal

Strict UTF-8 JSON envelope with exact types, duplicate/nonfinite/unknown fields
refused; bounded bytes/records/depth budgets must be owner/auditor-set before
implementation. Version=1; transaction_id random nonempty identifier; module
identity, canonical registry/gate identities, expected feature/version/candidate,
action and bound approval_id; base_registry_sha256; proposed_registry_sha256;
base_generation and proposed_generation (exact nonnegative ints, successor only);
source_sha256/bytes; candidate snapshot digest; relative destination/temp names;
all-version reference snapshot digest; consumption key and expected prior/new
record digest; stage enum above; event sequence exact positive int; previous
journal digest; selected decision and owner authorization reference (or null);
observation kind (syscall_return/SIGKILL_readback/reboot_readback/model_only);
durability status (unknown/visible/barriers_returned); expected and observed
artifact digest/regular-file/name states; recovery result; updated timestamp as
informational only. No source secrets, credentials, executable source or raw
exception text embedded. Timestamps never decide newest authority.

Separate optional evidence archive stores exact R0/R1 bytes and source snapshot
with digests, private permissions and an agreed retention policy. Do not record
absolute owner paths or raw approval payloads beyond necessary scoped identities.
Metadata/hashes do not authenticate a human, establish consent or resist malicious
rewriting. A self-consistent attacker rewrite of journal/JSON/digests still lies.

## Journal's own commit ambiguity and generation checks

Journal writes would be separate atomic replacements with their own temp/fsync/
replace/directory-sync failures. Journal stages may lag actual source/registry.
Never make file deletion dependent solely on a journal saying COMMITTED.
Partial journal temp, missing journal, duplicate sequence/transaction identity,
invalid checksum/schema or postreplace sync failure -> preserve originals/HOLD.
Journal COMMITTED with R0, or journal INTENT with R1, requires authoritative
readback and identity comparison; the latter can be legitimately lagging.
No atomicity across journal, registry, source, gate and ledger is promised.

Current registry has no generation. Proposed epoch must be stored in the SAME
registry replacement as state and consumption and validated on all cooperating
writes, including rollback/dispatch counters/proposals. Never invent a generation
from mtime or len(versions). Until such integration exists use exact raw registry
digest and HOLD on any change. Compare raw bytes plus decoded semantic refs under
lock, recheck before effect; any differing generation/digest makes decision stale.
Sidecar/advisory locks cannot stop noncooperating writers; final checks reduce
ordinary races but are not CAS/security containment. Hardlink alias/ancestor swap,
symlink/nonregular source, malicious edits, digest mismatch or observation cap
exhaustion -> HOLD, no deletion/adoption. Missing referenced inactive versions
are repair incidents, not dispensable garbage. Reference set must cover EVERY
version and any explicitly agreed external references before removals.

## Explicit owner decisions before eventual implementation

Choose forward-adopt vs preserve/quarantine vs explicit removal per transaction;
no automatic default that spends an approval or deletes data. Decide whether
prior unconsumed activation approval can authorize delayed adoption or requires
fresh approval, and how revocation/expiry works. Select physical vs logical
quarantine and retention/export/location/access limits. Approve schema budgets,
generation migration/legacy behavior, stable identity policy, journal storage,
recovery approver role and filesystem durability support matrix. Existing direct
registry bypass should remain explicitly trusted or be retired by a separate
approved API change. Independent audit and actual implemented recovery tests
required before any real artifact changes.
