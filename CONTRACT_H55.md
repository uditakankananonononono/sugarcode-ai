# H55 one invalid-k guard before low-Jaccard saturation

Parent8cb0b503a220718c656949099a1dc9dfaba04e05.
One test+contract additions only, no source/old-test edits.
Guard and precedence only, no mathematical-model or scientific claim.

## Visible gate (2026-10-10 IST)
Full kmer1-261, bio_kmer1-118, cli_kmer1-43 and P04 test visibly read
22:19:40. Full module includes helper and wrapper bodies. CLI compare
consumer1102-1120 read22:19:48; repository mash references inspected.
Source72b99d673e251a219d4d5d945a23fdc49a75076d;
direct7b472b8956e57fac0191a9c3665bcbaa7cb8195c;
CLI87499aeb1f75df1ff05ebd5719b06608e55ebb59.
Ratified22:19:57; fresh public fetch and relevant205-216 visibly re-read
before test22:20:01. Test first, execution next, contract afterward.
Documentary self-report, not independent proof of comprehension.

## Exact scope and overlap
mash_distance(-1.0,0) raises exact ValueError type and exactly
k must be >= 1, got 0
k guard precedes low-j saturation return. Existing (.5,0) loose exception
partly duplicates k rejection, existing (0,21) infinity covers low-j on
valid k; combined precedence/exact diagnostic not found in inspected tests.
No high-j, valid finite distance, formula parity, sketch or CLI claim.

## Author execution
New1 PASS0.15s; new+bio_kmer+cli_kmer+P04:20 PASS0.89s;
self_improve+same4files1860 PASS/13 XFAIL37.07s, not global suite.
Four temporary mutants each1F: low-j checked first; guard removed;
zero k allowed; diagnostic changed. Source restored byte-exact, src diff
clean, restored new1 PASS0.14s. Independent audit/exact EXECUTE before landing.
