# H57 one equality-zero primer concentration guard

Parent2ca81a8a88598595d44ca29e33aef325c36ad06c.
One test+contract additions only, no source/old-test edits.
Guard, equality-zero boundary and exact diagnostic only. No thermodynamic,
model, biological or successful-Tm claim.

## Visible gate (2026-10-10 IST)
Full primer1-278/bio_primer1-118/cli_primer1-33 read22:23:15 at e6e8216.
CLI790-825 and repository tm_nn references inspected22:23:23;
full primer_oracle_nn4 (including two individually skipping tests)22:23:31.
Sourcec3ed94425d608251728a7f5e14c81fc218c76a2f;
directd8e12560d0ecdef8d08c9b8b5ee00aa7176b1f97;
CLI5f8801ef4a4e13ebbd281d22181d64aee9aa9ded.
Ratified22:23:28. H56 landing preempted authoring. After landing,
fresh public fetch verified exact parent2ca81a8; source/direct/CLI blobs
unchanged and relevant69-110 visibly re-read before test22:24:45.
Test first, execution next, contract afterward; documentary chronology,
not independent comprehension proof.

## Exact pin and overlap
Direct tm_nn('ACGT',primer_nm10,template_nm20) raises exact ValueError
and exactly primer_nm must exceed template_nm / 2.
Default non-selfcomp k=(10-20/2)*1e-9=0, guarded by <=0.
Existing10/40 rejection is strictly negative and regex-only; same guard
path partly duplicates adjacent coverage. No selfcomp/table/formula claim.

## Author execution and skipped scopes
New1 PASS0.18s; new+bio_primer+cli_primer+primer_oracle_nn4:4 PASS/3 SKIP1.20s;
self_improve+same4files1844 PASS/3 SKIP/13 XFAIL38.98s, not global suite.
New independent test imports product directly and actually executes.
Bio module-level importorskip skips ENTIRE old bio_primer module,
including pre-oracle tests; independent CLI three tests execute. Two
primer_oracle_nn4 tests skip individually for missing Bio/primer3.
Parent's initial statement new direct test self-skips was corrected
before author. No skipped-test coverage claim.
Four temporary mutants each1F: strict-negative-only; guard removed;
diagnostic changed; k subtraction omitted. Source restored byte-exact,
src diff clean, restored new1 PASS0.11s. Audit/exact EXECUTE before landing.
