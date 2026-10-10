# H41 Newick prune missing/mixed-length merge findings

Parenteb32087ffe4855f8c6f3a73c84249ce9dfa87946 (composed peer P02).
One test parameterized over3 literal cases+contract only. No source/old-test
edit, numeric+numeric merge, standard/phylogenetic/biological validation claim.

## Reads and re-anchor, 2026-10-10 IST
Full newick.py1-248 and direct tests1-87 visibly read21:11:01; all three phylo
consumer test files visibly read21:11:09, before tests. Proposal on904e48c,
then P02 landing interrupted. At21:13:17 source/test blobs checked identical
on new parent; redirected source read to /dev/null was NOT model-visible and
is not claimed as a fresh full-read gate. Actual visible reads were on H40,
identical blobs: sourceb197a383ae651b611cad8115d681161146f90f9c;
direct test1fb25d33c12459b559fad12958d27ffda2d4d75f.
Tests authored on P02 before execution, contract afterward. Documentary
chronology only; no retrospective compliance claim if fresh-visible-at-parent
is required. Independent auditor must retain this gate caveat.

## Distinct literal branch findings
Drop B in ((A,B:1)I,C:4)R: merged A lengthNone (both missing).
Drop B in ((A:2,B:1)I,C:4)R: A length2 (child-only length).
Drop B in ((A,B:1)I:3,C:4)R: A length3 (parent-only length).
Exact full nested result and original input deep equality. Existing prune
fixture has numeric lengths on both merged edges; it does not cover these
missing/mixed branches. Source-derived expectations, no external oracle.

## Original FAIL and author runs
New3 PASS0.12s; five-file adjacent30 PASS1.04s. Original self_improve+same5:
1869 PASS/1 FAIL/13 XFAIL41.43s, unchanged same-group descendant canary:
terminal False/state None/ProcessLookupError/elapsed4.9375001253793016e-05.
Original XML/console retained and sent, no proc snapshot/root-cause claim.
No-edit H27 trio40 PASS1.72s; full recheck1870 PASS/13 XFAIL36.79s.
Four temporary mutants killed: both-missing converted zero1F/2P,
parent length dropped1F/2P, child length dropped1F/2P, input mutated3F.
Source restored byte-exact, new3 PASS0.12s. Not configured global suite.
Independent audit/EXECUTE before landing; no candidate push yet.
