# H39 two literal GFF Parent-cycle shapes

Exact parent7472e445e30b731e05acf340980a1c43cc2cc2b4.
One grouped test+contract only, no source/old-test edit. Plain record dicts;
no parser, annotation-standard, general graph or biological validation.

## Source gate and sequence (2026-10-10 IST)
Full gff.py1-237/direct tests1-119 read21:03:40, CLI tests1-40 read21:03:48.
Source42babd534fb5f86fa916b162c17d52e34feb4bd3;
direct testcb320d9ff535df9277f6c4ee0c3d8f1564ad0c66;
CLI35bcd82619d0f4cd62d5c479b135b79a8824521e.
Current direct hierarchy fixture acyclic; current CLI tests have no cycle.
Tests authored before execution, contract afterward, documentary self-report.

## Bounded shapes and termination guard
Two-node a Parent=b/b Parent=a returns exactly b once, excluding root a;
self-cycle a Parent=a returns []. Wrapper delegates real children_of but asserts
at most6 calls, so removed seen guard fails instead of hanging. Exact call
sequences a,b and a also pinned, two-node input remains value-equal.
No broad cycle-safe proof or exhaustive coverage claim.

## Author execution and surviving mutant
New1 PASS0.13s; new+bio_gff+cli_gff17 PASS0.34s; self_improve+same3files
1857 PASS/13 XFAIL36.68s, not configured global suite.
Three temporary mutants killed (each1F): root not initially seen, seen guard
removed, empty descendants stub. Fourth mutant removing seen.add(cid) SURVIVED
(1 PASS): these root-returning cycles are stopped by root initial membership,
so general repeated nonroot handling is NOT validated. Reported to parent before
packaging, no quiet test expansion. Source restored byte-exact, new1 PASS0.11s.
Independent audit/EXECUTE required before landing; no push yet.
