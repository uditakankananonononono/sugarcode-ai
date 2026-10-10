# H117: one literal negative-start GFF characterization

Exactly two additions: this contract and
`tests/test_h117_gff_negative_start_characterization.py`.
One literal parse_gff('chr1\ta\tgene\t-1\t9\t.\t+\t.\tID=g') call
pins exact ValueError identity and full diagnostic:
`line 1: invalid coordinates -1..9`.

Base: a7dddddc61e3ec8b64f470682260b7999c158b73.
Source provenance: src/sugarcode/bio/gff.py:87-91. Nine fields and both
integer conversions pass; start<1 rejects, end<start does not. This is a
source-derived diagnostic, not an independent coordinate/format oracle.
H92 zero-start literal exercises the same clause; tests/test_bio_gff.py
uses reversed 9..5 with substring matching. Negative-start literal ONLY,
no guard/diagnostic novelty or broader validation/conformance/biology claim.

## Read gate and chronology

Fresh public clone/fetch initially read tip 05fc2a60. Full gff.py, direct/CLI
GFF tests, H92/H109 tests/contracts, pyproject and remaining GFF
characterizations were read before writing. Scoped collision search found
H92/shared guard and reversed-coordinate overlap, no same literal in scoped
files; not an exhaustive absence claim. Prewrite fetch moved to a7dddddc;
paused and reported, then parent ruled re-anchor rather than stop. Entire
delta (H114 BED contract/test only) read; scoped search repeated. No GFF
product changes in that delta. Tests-first file authored after reads.
Measured command timestamps, original pause and correction of one unmeasured
chronology label are preserved in external receipt chronology, not retimed.

## Environment and actual selected checks

First authorized `python -m pip install pytest` failed127, python unavailable.
Additional parent-authorized `python3 -m pip install --user pytest` succeeded0:
pytest9.1.1, pluggy1.6.0, iniconfig2.3.1 in user site. Required final pip-show
and pluggy-import receipts succeeded; no uninstall/retry/corrective broad install.
No standalone syntax/AST checks. Real product imports and pytest calls ran.

- New-only: 1 passed in 0.10s, exit0.
- New + test_bio_gff + test_cli_gff: 17 passed in 0.54s, exit0.
- Same + tests/self_improve, strict XFAIL: 38 failed, 1819 passed, 13 xfailed
  in 25.23s, exit1. Wider result is FAIL, unexplained; no cause claim.
  Parent reports identical counts seen on H111 by SC-J05, a reported fact only,
  not proof of shared cause or baseline equivalence. Selected, never global suite.
- After temporary mutations: restored-adjacent 17 passed in 0.49s, exit0.

Wider failure triggered STOP/report; parent explicitly ruled scoped mutations
may continue and wider failure must remain disclosed. No wider repair attempted.

## Isolated mutation evidence

Four independent temporary gff.py parse_gff mutations; no repo source edits:
return None, return full diagnostic string, RuntimeError, remove ONLY start<1
retaining end<start. Each new-only run had 1 failed/exit1. First, second and
fourth failed DID NOT RAISE; RuntimeError escaped with literal diagnostic.
Each started from original bytes, used isolated temporary package/PYTHONPATH,
and finally restored byte-exact bytes plus SHA256 verification before cleanup.
Repo gff.py remained byte-exact unchanged. Original/restored SHA256:
`c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb`.
Raw logs and mutation reproducer supplied externally. These four failures are
not an exhaustive mutation adequacy claim. Independent audit/landing remains
peer-owned. No push, merge, services or source/existing-test edits.
