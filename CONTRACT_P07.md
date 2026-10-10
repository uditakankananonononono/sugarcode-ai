# P07 find_orfs ambiguous-middle-codon characterization (authored NOT RUN)

Parent exactly 7c0b13dab133d9c6a87cfc1de8ae9f21ddecc216 (H48; tree 945ce5089f4b0059533091b79a98ad8d498f7ca0; parent a7518de7f00c373c58cd56d799337652dcf111c9).
Test+contract only. ONE test, ONE full-list equality. No source or old-test edit.
Authority: peer P07 literal grant relayed by Main (9:58:40 PM IST), not independently authenticated by me.

## What is pinned (derived by reading src/sugarcode/bio/orf.py, NOT observed)
find_orfs("ATGNNNTAA", both_strands=False) is expected to equal exactly one dict:
strand "+", frame 1, start 0, end 9, length_nt 9, length_aa 2, gc 0.166667,
start_codon "ATG", stop_codon "TAA", truncated False, protein "MX".
Derivation: forward frame offsets 0/1/2 give codons [ATG,NNN,TAA], [TGN,NNT], [GNN,NTA].
Only offset 0 has a start (ATG, l.177-178) and a stop (TAA in table 1, l.179).
NNN is neither start nor stop, so the open start survives it (l.176-183).
emit: end_rc 9, len_nt 9, len_aa 9 // 3 - 1 = 2 (l.151-152). protein from translate("ATGNNN") = "MX"
(l.155-157; translate maps a non-ACGT codon to X at bio/orf.py l.88-89). gc: _gc (l.103-107) counts only
ACGT bases of ATGNNNTAA: A,T,G,T,A,A = 6, G is the only GC, round(1/6, 6) = 0.166667 (implementation rounding, not biology).

## Overlap and exclusions
Partial overlap with forward fixtures: test_bio_orf.py:48-57 pins a forward ORF with gc 4/12 and no ambiguous base.
translate("ATGNNNTAA") == "MX*" is already pinned at test_bio_orf.py:22; that is translation, not the scanner, and is not repeated.
New here: scan continuation and emission across an ambiguous middle codon, and the ACGT-only GC denominator.
No claim about the reverse strand, nested, truncated policy, other tables, general IUPAC, alternative starts, CLI, clinical use, or standards.
No existing contract H34-H48, P02-P06 covers bio.orf.

## Reads at this tip (visible, 2026-10-10 IST, workspace clock)
orf.py 1-189 (blob 31e5e490544135398ede2c2d133cae0d4313f468), tests/test_bio_orf.py 1-108 (fa9db266ecb4fd9167e0226dc1e20c15690deba0),
tests/test_cli_orf.py 1-32 (aaee44f723bad13ee3ae096aff21e6e2bf977b8d), tables.json table 1 entry in full (forward map, starts ATG/CTG/TTG, stops TAA/TAG/TGA)
via a json.load of the data file only (no SugarCode code run), cli.py 1059-1085 and 1240-1259 (blob 6deca9be51c878920eae0afd66786a071f61dfbf, 1672 lines;
my earlier 1609 figure was from an older base, 1672 is correct at this tip), contracts H34-H48, P02-P06 in full, wrapped at 200 columns, no cuts.
orf.py 103-189 re-read visibly at 21:59:31, tip verified at 21:59:38 immediately before the test write.
find_orfs hit bodies read: cli.py _cmd_orf_find (passes sequence through, no N handling) and tests/test_bio_orf.py (no non-ACGT find_orfs input).
NOT read: rest of cli.py, bio/sequence.py reverse_complement (not needed: both_strands False), other modules.

## Network (existing clone /tmp/sc, same public HTTPS repo only, fetch only, no push, no credentials)
git fetch origin at 21:55:35 (a7518de), 21:58:46 (to 7c0b13d), 21:59:31, 21:59:38 (no change). git remote -v: origin https://github.com/uditakankananonononono/sugarcode-ai (fetch) and (push), no other remote.

## Test file
tests/test_p07_orf_ambiguous_codon_characterization.py, one function test_find_orfs_scan_continues_through_ambiguous_codon_forward_only, blob 04ae9e3c03c16be57c4aa932006d1d2c5155fe31, written by quoted-heredoc cat (no scripted edit).

## RUN vs NOT RUN
RUN: git fetch/checkout/hash-object/format-patch/bundle, sed/cat/grep reads, one json.load of tables.json. NOT RUN: pytest, import of SugarCode, py_compile or any syntax check, pip. No PASS or landing claim.
