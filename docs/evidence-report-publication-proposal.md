# Evidence report failure-preserving publication proposal

PREP-NORUN, separate UNAPPLIED product proposal. No working/verified claim.
Base: 842e055ed01695f62582c4b0f0327a2944d24f70.
Scope: scripts/evidence_report.py only, plus this contract and authored tests
beside tests/test_drop49.py's script-test convention. No other product edits.

Source defect: base lines 21-26 discard child returncode/stderr and use only
stdout; lines 58-61 then print and overwrite docs/EVIDENCE.md. A failed child
with missing/partial headline output can be followed by successful independent
fixture sections and silently publish an incomplete consolidated report. This
was source reasoning, not a reproduced runtime failure.

## Mandatory contract, no new sections

Exactly one line for each CURRENT pooled_splice_stats.py headline:
- fixtures: N  unique pathogenic: N  unique benign: N
- canonical U2 (GT/GC donor, AG acceptor): N/N called loss
- canonical AT-AC (U12 matrices, drop 27): N/N called loss
- benign specificity: N/N

N is ASCII decimal digits, nonnegative. Ratio numerator must not exceed its
denominator. Zero denominator remains permitted: no new statistics or clinical
validity interpretation is invented. Missing, duplicated prefix, malformed
line or nonzero child exit blocks publication. Extra child detail is ignored as
before. Original order of required lines is preserved. Child is invoked using
sys.executable, absolute script path and explicit repo-root cwd.

Existing remaining section structure is unchanged: GC-donor, VUS, conflicting,
exonic donor/acceptor, cryptic recall and ESRseq. Every section must render before
publication; required key/type/format/fixture read failures abort. This is not
complete fixture schema validation, numeric authenticity or scoring evaluation.
No sections or empirical/clinical acceptance claims are added. Static output
expressions and existing limitation wording remain unchanged.

## Publication and failure stages

Render full content in memory. Write a same-directory temporary UTF-8 file,
flush and fsync it, close it, then os.replace onto docs/EVIDENCE.md only after all
render/write stages succeed. Child/contract/fixture/section failure never opens
the destination. Pre-replace write/fsync/replace failure leaves old bytes intact;
best-effort temporary cleanup never hides the original failure. Stage-specific
EvidenceReportFailure is printed to stderr with exit 1 by script entrypoint.
Print successful report only after replacement, avoiding success output before
publication. Filename paths are rooted to this script's repository.

Limits: same-directory rename relies on OS/filesystem rename semantics. No
parent-directory fsync or post-rename power-loss durability guarantee. No locks,
concurrent-writer arbitration, preserved file mode/owner, symlink policy,
subprocess timeout/output cap or all-platform atomicity guarantee. Successful
rename is the commit point; subsequent stdout failure does not roll it back.
Unexpected errors, MemoryError and KeyboardInterrupt remain unnormalized but
pre-publication render failure does not open the destination. Temp cleanup can
fail and leave a non-authoritative temp file. No service or live state used.

## Authored, NOT RUN

Failure cases: child nonzero (empty and otherwise-valid stdout), partial output,
duplicate headline, malformed ratio/count, inverted ratio, launch failure,
fixture/section failure, temp partial-write, fsync and rename failures. Success
cases: interpreter/cwd/order, exact published bytes, unchanged real-fixture
section rendering against base document. No imports, runtime calls, test
collection or test execution performed by builder. Only static AST parsing and
git whitespace inspection are builder checks.

Peer planned commands, NOT executed here, in disposable worktree only:

    git worktree add --detach /tmp/sc-evidence-review <proposal-commit>
    cd /tmp/sc-evidence-review
    python -m pytest -q tests/test_evidence_report_publication.py tests/test_drop49.py
    python scripts/evidence_report.py
    git diff -- docs/EVIDENCE.md

Peer must check real child success, unchanged content on current fixtures,
actual filesystem failures, supported Python/OS behavior and independent verdict.
The existing test_drop49.py and direct script intentionally write the document;
keep review runs away from main or any authoritative user state. Runtime
execution belongs to peer after approval. Reserved bundle-manifest collision in
report/exporters.py was NOT approved and is NOT part of this proposal.

Repackaged PREP: this commit adds tests/docs ONLY. The product modification
is a separate UNAPPLIED patch based on the same prerequisite. Before executing
the planned tests, peer must explicitly apply that product patch in a disposable
review worktree (git apply --check PRODUCT.patch, then git apply PRODUCT.patch).
Tests without that patch are not an acceptance run of the proposed repair.
Old combined receipts remain historical; selected product path has no base delta.
