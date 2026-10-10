# H31 FASTQ blank-line status-quo characterization (authored NOT RUN)

Parent exactly153665dbe0d1c73c00f257b06e4ff83c33a0ff73. TEST+CONTRACT ONLY,
no product edit, semantics endorsement, defect/fix or validation claim.
Case behavior and quality-score math excluded; all inputs uppercase with literal
quality fields, no score assertions. Finding wording only.

Gate chronology, workspace-clock observed on10Oct2026 IST:
- Required read start18:14:51, end18:14:52.
- src/sugarcode/bio/fastq.py FULL1-183, including all parse/stream functions,
  blob2f21e3f56624c945ee90a13168c50b283dd82ec7.
- tests/test_bio_fastq.py FULL1-100, including test_parse_errors32-42,
  blob77cbcd0eba47e5bbffaeb865fda27482bbfb9b7d.
- Exact tip independently rev-parsed, blobs confirmed during that read.
- Author start18:14:54, test author end18:15:00. This contract afterward.
Earlier source reads are not substituted for this gate. Test-first, no source step.

Three literal shapes only: ordinary four-line record bulk/stream control; one
leading blank bulk accepts while stream raises ValueError; two records with one
separator blank bulk accepts both, stream yields first then ValueError on next().
Partial progress asserted explicitly, iterator closed finally. Expectations from
source read, not execution or external oracle. Bulk21-23 skips blank lines before
records; stream53-58 frames physical four-line blocks before parsing. Pins current
entrypoint behavior as a finding, not a desired policy or standard-conformance
judgment. A future behavior change requires re-review of these characterizations.

Existing test_parse_errors blank-only rejection41-42 is adjacent, NOT overlapping:
it pins no-record bulk refusal; these new literals contain valid records plus
optional blank separators and exercise streaming partial progress. Existing normal
bulk roundtrip is a control; no old test changed. No CLI or FASTA scope added.

Tip obtained from local H30 bundle SHA044f2f0c18a43c326662191ae1ed7392aef68046ed872521e8b98682e01078a7,
requires H29 4fb00691 already present. Hash matched, bundle verify/local fetch
and exact153665db resolved, no network. H10-H30 areas excluded by assignment;
no off-tree exhaustive ownership or coverage claim.

RUN git/text/hash/diff/bundle and date receipt operations only. NOT RUN tests,
pytest, imports, SugarCode/product, AST/compile/syntax, pip/network. No PASS,
working or mutant-kill claim. Peer auditor owns execution/independent verdict.
