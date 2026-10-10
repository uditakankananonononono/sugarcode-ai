# H89: literal empty GFF rejection

Runtime-characterized, audit/publication pending. Two additions only.
Authoring live-tip re-anchorbc77bfa5d05703b6708aa58de1046f975b0e38de
matched local HEAD, no replay. Fresh full GFF237/direct119/CLI40 reads before
writing; source blob42babd534fb5f86fa916b162c17d52e34feb4bd3.
Scoped parse_gff/diagnostic coverage search found header-only substring
rejection '##gff-version 3\n', no direct empty exact identity/text pin found;
not exhaustive coverage absence. Final guard105/raise106 before return107-109.
Empty literal probe exact ValueError/'no GFF records found'. Parent assigned
and ratified H89 after H87 landing; no production or old-test changes.

One direct parse_gff('') call, exact ValueError identity and diagnostic.
No directives/comments/attributes/general-input/GFF conformance/successful
parsing/consumer/model/biology claims. Source-derived rejection only, no
external format oracle. Source comments/provenance not independently verified.

## Author runtime

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1 passed/.31s.
Adjacent new+tests/test_bio_gff.py+tests/test_cli_gff.py:17 passed/1.05s.
Wider selected same+tests/self_improve:1857 passed/13 xfailed/39.62s.
Not global suite; XFAILs not implemented repairs.
Restored new1 passed/.14s.
Four independent new-only mutants from original bytes:
- Remove no-record guard:1 failed/.21s (accepted dictionary returned).
- Guard returnNone:1 failed/.17s.
- Diagnostic 'no records':1 failed/.16s.
- Exception RuntimeError:1 failed/.16s.
Source byte-restored after each attempt, final SHA256:
c3650708b855eb251c45fbcf8511a1b0e154295eb2b8eac622f952440f859feb.
XMLs/full mutant log included, per-receipt hashes in manifest.
No exhaustive mutant adequacy claim. No push; separate publication required.
