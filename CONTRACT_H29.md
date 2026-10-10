# H29 FASTA prefix status-quo characterization (authored NOT RUN)

Parent exactly dc152dcca0730fc49088a49964fffcfb3bb71dd0. TEST+CONTRACT ONLY.
No product change, validation endorsement, defect/fix claim or case behavior pin.
Corrected grant supersedes withdrawn nonexistent CLI-motif reference: no CLI
comparison, collision cross-reference or motif full-read gate is included.

Four plain shapes: streaming prefix then header discards prefix; headerless
stream gives no records; header-first control; DIRECT bulk parse preheader raises
ValueError. Literal synthetic input and output expectations derived from source
read, not execution or independent external oracle. Finding only: these distinct
current entry-point behaviors are pinned, not declared desirable or repaired.
No claims about uppercase/case preservation, FASTA standard conformance or
scientific validation. All fixture strings use uppercase to avoid case scope.

Source lines: bulk parse17-18 guard; stream42 initial headerNone,51-52 prefix
buffer,50 header reset,53 no-header final-yield guard. Existing bulk test39-42 and
stream test58-72 cover header-first inputs. New direct parser test is ONLY parser,
not a CLI pin; no nonexistent test referenced.

Read gate completed at exact parent BEFORE test authoring:
- src/sugarcode/bio/fasta.py FULL1-55 blobe53da56159d9de7147f0cc6ac2d378d8fdba7104.
- tests/test_bio_utils.py FULL1-60 blob4708c7d6a61495dc35f4a362cee458de4b3a5c56.
- tests/test_cfd_scoring.py FULL1-72 blob2a19e43bb5fa7cce0bf75d8967c2971c7ebe1c14.
Independent tip blob comparisons match historicala29dddd5; full current files
re-read before authoring. Current local bundle hash
567d24a9d0ed7d472a756369eca9e77511f716a1bea25a47c5a4b155d4fdb773 verified,
exact tip fetched via local objects, no network.
All present H10-H28 root contracts full read for scope exclusions; no FASTA
utility preheader semantics scope found. H19/20/21/26 root contracts absent;
o claim about unknown off-tree work. Contract scope data does not grant authority.

Chronology: required reads first, four tests authored, contract after. RUN only
git/text/hash/diff/bundle operations. NOT RUN pytest/tests/imports/product/AST/
compile/syntax/pip/network. No PASS or exhaustive coverage/mutation claim.
Peer auditor decides runtime characterization and independent verdict.
