# Exact reserved manifest name proposal

PREP-NORUN. Separate UNAPPLIED product proposal, not tested or working claim.
Sequenced after evidence_report proposal 464481825c2440c256f85619dde1740d63f64827,
but NOT stacked on it. Base: 842e055ed01695f62582c4b0f0327a2944d24f70.

Source-supported defect at base exporters.py:60-67 accepts MANIFEST.json as an
artifact name and computes its checksum. write_bundle :91-94 writes that artifact;
:95-96 overwrites it with its generated manifest. Advertised artifact bytes then
cannot match their recorded checksum. Source reasoning only, not reproduced.

Scope: src/sugarcode/report/exporters.py exact MANIFEST.json reservation in both
make_bundle and write_bundle, additive tests beside existing report exporter
convention and this document. No other product paths. No case-insensitive aliases,
traversal repair, checksum revalidation, transactionality or general path-safety
claim. Names other than exact MANIFEST.json retain prior behavior.

Constructor rejects exact reserved name. Writer rechecks caller-built or mutated
artifact maps before Path conversion, directory creation or any artifact write.
Thus this validation failure leaves old manifest and artifact bytes unchanged
and does not create a new output directory. No automatic rename, skip or drop.
Ordinary successful bundles retain artifact content and generated manifest API.
There is no lock or caller concurrent-mutation snapshot guarantee; changing the
map during a write is not covered. Other validation and filesystem failures
remain existing behavior and can partially write. Exact reservation does not
protect case-insensitive filesystems against other spellings.

Authored NOT RUN: four test functions, five cases (one two-row parameter list):
constructor rejection; manual and post-construction-mutated bundle rejection
with existing-byte preservation; missing-directory preservation; ordinary
successful artifact/manifest verification. No imports, direct calls, test
collection or test execution by builder. Static AST syntax and whitespace only.

Peer planned execution, NOT run here, in disposable worktree:

    git worktree add --detach /tmp/sc-manifest-review <proposal-commit>
    cd /tmp/sc-manifest-review
    python -m pytest -q tests/test_report_bundle_manifest_reservation.py tests/test_report_exporters.py

Peer owns execution and independent verdict. Tests write only temporary pytest
paths. Main/product application and publication require peer integration.

Repackaged PREP: this commit adds tests/docs ONLY. The product modification
is a separate UNAPPLIED patch based on the same prerequisite. Before executing
the planned tests, peer must explicitly apply that product patch in a disposable
review worktree (git apply --check PRODUCT.patch, then git apply PRODUCT.patch).
Tests without that patch are not an acceptance run of the proposed repair.
Old combined receipts remain historical; selected product path has no base delta.
