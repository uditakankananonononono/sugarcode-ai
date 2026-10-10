# H43 two literal CIGAR consuming-op shapes

Exact parentbd5f089b98f7690239d4b0e2a07444ab7e813fd0 (peer P04).
Two tests+contract only, no source/old-test edits. No SAM parse-standard,
physical alignment accuracy, clinical or biological validation claim.

## Visible read gate (2026-10-10 IST)
Full sam.py1-221 and bio_sam1-105 read21:27:03; CLI/pileup consumers read
21:27:14, coverage rg across tests21:27:20. P04 preempted authoring.
Visible re-anchor FULL source/direct/CLI files at current parent21:33:56,
then tests written, executed, contract afterward. Documentary self-report.
Sourcebe61e9d737deadd50a451bc4c50d2c31c1d9d416;
direct41a13a937001445f19309970f750068d00a31e47;
CLI80d10c87e758122bedcd24a6a1d86909d662429a.

## Literal scope and overlap check
1H2P3=4X -> exact tuples[(1,H),(2,P),(3,=),(4,X)], query/ref sums7 each.
1H2P -> exact tuples and both sums0. Expected arithmetic from op sets in
current source, no external oracle. Direct old fixture covers M/I/D/N/S,
not H/P/=/X length arithmetic. Broad rg found no stronger relevant pin;
low-relevance matches were unrelated protein names/math. No exhaustive
coverage claim. H/P-only control reinforces exclusions; no general CIGAR
validity endorsement or downstream alignment_end/to_bed behavior added.

## Author execution, independent audit still required
New2 PASS0.12s; new+bio_sam+CLI sam+bio_pileup+CLI pileup23 PASS0.50s;
self_improve+same5files1863 PASS/13 XFAIL36.22s, not global suite.
Five temporary source mutants killed: ref drops=, query dropsX, ref includes
H/P, query includesH/P, parser empty-list stub. Source restored byte-exact,
new2 PASS rerun. No source mutation committed. Audit/EXECUTE before landing.
