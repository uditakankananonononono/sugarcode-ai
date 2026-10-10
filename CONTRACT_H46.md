# H46 one direct SAM MAPQ filter boundary

Parent2619d32b82f84588c8870c9940d319c8fc269973.
Test+contract additions only, no product source/old-test edits.
One supplied-record literal, no parser, flag decoding, SAM standard,
mapping quality accuracy, biological or general filter validation claim.

## Visible gate (2026-10-10 IST)
At fa0f83f full sam.py1-221 read21:45:04-08, full bio_sam and cli_sam
read21:45:08, full unmapped-end and H43 tests21:45:18. CLI consumer539-571
read21:45:18. Repository min_mapq/filter_records coverage search also read.
After ratification21:45:30 and H45 landing, public fetch verified exact
parent2619d32; relevant sam190-209 visibly re-read before test21:47:02.
Sourceblobbe61e9d737deadd50a451bc4c50d2c31c1d9d416 unchanged;
bio_sam41a13a937001445f19309970f750068d00a31e47;
cli_sam80d10c87e758122bedcd24a6a1d86909d662429a.
Test first, execution next, documentary contract after. These are
self-reported chronology receipts, not independent comprehension proof.

## Exact finding and overlap
Minimal supplied dictionaries: below mapped24, equal mapped25, high
unmapped60, input order preserved. min_mapq25 returns qnames ['equal'].
Equality is inclusive; an unmapped record is excluded even with MAPQ60.
No parse_sam or decode_flags used. Existing min_mapq30 fixture tests have
60/25/0/10, not equality; mapped_only tests already cover unmapped
exclusion through a different option. Below-threshold exclusion duplicates
some adjacent coverage. No empty/preservation/identity or other options claim.

## Author execution
New1 PASS0.19s; new+bio_sam+cli_sam+unmapped-end+H43:16 PASS0.84s;
self_improve+same5files1856 PASS/13 XFAIL47.36s, not global suite.
Four temporary mutants killed each1F: exclusive <=; min_mapq unmapped
check removed; keep append suppressed; numeric threshold ignored.
Source restored byte-exact, git src diff clean, restored new1 PASS0.12s.
Independent audit and exact EXECUTE remain required before landing.
