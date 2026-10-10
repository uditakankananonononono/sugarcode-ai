# H40 one literal nonroot GFF Parent cycle

Exact parentd8d189b5e7eb1db02f079b4e01d92d71056da9ab.
One test+contract only, source and old tests unchanged. H39 contract/survivor
record untouched. No parser, standards, general graph or biological validation.

## Source gate and sequence (2026-10-10 IST)
Full current gff.py1-237, bio_gff1-119, cli_gff1-40 and H39 test1-25 re-read
21:07:22 before proposal/authoring. Source42babd534fb5f86fa916b162c17d52e34feb4bd3;
bio testcb320d9ff535df9277f6c4ee0c3d8f1564ad0c66;
CLI35bcd82619d0f4cd62d5c479b135b79a8824521e;
H39 tested8431eb45feddf21afd98052c7bebe1a2207482.
Tests first, execution afterward, contract last; documentary self-report only.

## Distinct bounded shape
Plain record dictionaries root a, b Parent=[a,c], c Parent=[b], a->b->c->b.
Exact descendants [b,c] once, exact calls[a,b,c], input deep-value equality.
Wrapper delegates real children_of, refuses after6 calls to prevent mutant
infinite loops. No broad graph/cycle proof. Existing direct fixture acyclic;
H39 root-returning shapes allow removed seen.add(cid) to survive. This unit
pins that distinct nonroot revisit, not a retroactive change to H39's verdict.

## Author execution, independent audit still required
New1 PASS0.12s; new+H39+bio_gff+cli_gff18 PASS0.63s; self_improve+same4files
1858 PASS/13 XFAIL37.85s, not configured global suite.
Three temporary source mutants killed (each1F): seen.add(cid) removed,
seen guard removed, empty descendants stub. Source restored byte-exact,
new1 PASS0.10s. These narrow kills do not erase H39's historical survivor or
establish arbitrary graph correctness. Independent audit/EXECUTE before push.
