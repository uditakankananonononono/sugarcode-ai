# H121 incremental reversed-coordinate identity and full text

Test-first, exactly this contract and
 tests/test_h121_gff_reversed_coordinates_characterization.py added.
Tested base ce6d644e42fe596a0f760074579f3b8f35375594.
One parse_gff('chr1\ta\tgene\t9\t5\t.\t+\t.\tID=g') call pins exact
ValueError identity and 'line 1: invalid coordinates 9..5'.
Direct test already rejects the SAME row plus newline with substring regex.
This is incremental identity/fulltext ONLY, no novelty claim. Start9 is
positive; only end<start rejects. H92 zero start differs; H117 negative
start is peer-scoped adjacency, not present at tested base or locally read.
No general coordinate policy, successful parse, GFF conformance or biology.

## Visible read and command chronology (2026-10-11 IST)
Public ls-remote and independent clone00:54:47-48: ce6d644e, no delta
from reported base. Full gff/direct/CLI-test read00:54:48. Source blob
42babd534fb5f86fa916b162c17d52e34feb4bd3; direct
cb320d9ff535df9277f6c4ee0c3d8f1564ad0c66; CLI
35bcd82619d0f4cd62d5c479b135b79a8824521e.
Full H92 test/contract and H113 test read00:55:10, CLI consumers432-475
and parser1513-1540 via awk, CSV tail473-486 completed00:56:36.
Scoped collision search tests/contracts for parse_gff, invalid coordinates,
end<start, H121; literal full text repository search empty before writing.
Not exhaustive semantic coverage search. Full source includes helper body.
Fresh public receipt00:55:10 same base before test written00:55:11.
Read claims documentary, not independently certified.

Initial python3 import pytest probe failed; ONE permitted
python3 -m pip install --user pytest00:54:56-59 exit0, pytest9.1.1.
Exact scope 'python' command attempted00:55:11, shell command-not-found127,
zero tests executed then. Parent instructed literal python3 substitution
00:55:36, no alias/symlink/install retry. Python3.10.12. All runs use
PYTHONPATH=src python3 -B -m pytest -q.

## Actual receipts, wider failures preserved
New1 passed0.11s00:55:40-41; adjacent new+bio_gff+cli_gff17 passed0.53s.
ONE wider SAME+tests/self_improve00:55:42-00:56:07:
38 failed,1819 passed,13 xfailed24.50s, exit1. Not global. Failures raw
preserved, not repaired/retried or claimed baseline. No XPASS in summary;
strict-XFAIL policy was not independently audited by this unit.
Four independent temporary parse_gff mutants00:56:28-31 each new1 failed
exit1: returnNone no raise; fulltext changed to bad coordinates (identity
passes/text fails); RuntimeError escapes; remove ONLY end<start, retaining
start<1, accepts record/no raise. Python mutation script exact unique
replacement and finally restore, byte comparisons after each, full hashes
in raw receipt. Source restored byte-exact SHA256
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb.
Restored adjacent17 passed0.44s, source diff empty. No mutants committed.

## Moving tip and handoff
Public main moved to1572faf76e4eb0db4a9c6255f214b1a81bb9d7fa00:56:36.
Fetch00:56:42-43; only H110 contract/test additions, full read, BED count
branch disjoint. No source/old-test edit. Tested base and commit parent are
recorded in manifest, not silently equated with current main.
No push, merge, broader install or unrelated product edit. Raw receipts
and executable reproducer scripts delivered separately. Peer audits/lands;
no independent audit or landing claim by author.
