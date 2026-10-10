# H122: three-field GFF literal characterization

Exactly two additions: this contract and
 tests/test_h122_gff_three_fields_characterization.py.
One parse_gff('chr1\ta\tgene') call pins exact builtin ValueError and
'line 1: GFF record has 3 fields, need 9'. Current gff.py84-85 rejects before
indexing87. Source-derived diagnostic, not independent parser oracle.
Ordinary direct test107-109 uses SAME row with newline and need9 regex;
incremental exact identity/full-text ONLY, no validation novelty. H90 one-field
and H113 two-field pins share guard; H111 ten-field reservation shares guard
but was absent at read base. No general width/line-number/conformance,
successful parse, consumer, biological or repair claim.

Base/live before authoring: ce6d644e42fe596a0f760074579f3b8f35375594,
matching peer last tip, no anchor delta. Full source237/direct119/CLI40 reads,
H90/H113 contracts/tests and scoped collision search before test authored.
Exact diagnostic not found within scope; no exhaustive absence claim. H111
read gap disclosed. No source/existing-test edits, pushes or merges.

Tests first, no new install: prior user-site pytest. python3 substituted for
missing python before parent's00:55:36 explicit confirmation arrived during
wider run; chronology states ordering, not retroactive approval/timing. Parent
then explicitly said continue four mutants/restore. No alias/symlink/install.
Actual separate selections, raw stdout/stderr plus JUnit retained:
- New1 passed/0.10s.
- New+test_bio_gff+test_cli_gff17 passed/0.41s.
- Same+tests/self_improve with strict XFAIL: exit1,38 failed,1819 passed,
  13 xfailed/25.70s. ONE wider run, scoped not global and NOT PASS.
Observed missing isolated /usr/bin/python3 pytest matches prior H116
symptom; not every failure independently diagnosed. No corrective install.
Restored-adjacent17 passed/0.39s. Counts distinct, never additive.

Four isolated one-at-time mutants, new-only all exit1:
returnNone1failed/0.11s and fulltext1failed/0.11s DID NOT RAISE;
RuntimeError1failed/0.12s wrong class escapes;
countguard removal1failed/0.12s IndexError f[3], NOT accepted record.
Every pytest invocation prints LOADED_MODULE proving isolated gff.py path.
Byte-exact original restore after EACH and SHA256
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb.
Driver captures exact commands/timestamps/JUnit and full raw errors. No
exhaustive mutant adequacy claim. No syntax-only checks or separate literal
probe. Peer audit/landing outstanding; scoped characterization not repair.
