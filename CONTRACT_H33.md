# H33 Stockholm orphan GS characterization (authored NOT RUN)

Parent exactly e3d84dc92949fd21331dbc29531a9278b33cafdf.
Test+contract only. Two source-derived current-behavior findings, no product
or old-test changes. Case, A3M and CLI behavior excluded. No desired-policy
or standard judgment; a future behavior change calls for characterization review.

Fresh gate completed at the exact parent, 2026-10-10 IST:
Read start18:29:14, end18:29:15, full ranges and committed blobs:
- src/sugarcode/bio/stockholm.py1-260:
  7c41c7002da0a8f1ee7cc936154c3105c0ec2b62
- tests/test_bio_stockholm.py1-103:
  e63beab3b24d03d75a5c2ab8b2c193f4ed81ceae
- tests/test_cli_msa.py1-35:
  9798d49fb795906dada5e90fa7a24a3ab8f39902
PLUS full separate re-read of test_parse_wrapped_blocks_and_markup29-35
and test_stockholm_semantic_roundtrip38-40 in the same gate. Earlier reads
not substituted. Rev-parse and blob ids confirmed. Author start18:29:16,
test author end18:29:20, this contract afterward. Test-first preparation.

Only literal '# STOCKHOLM 1.0\ns AC\n#=GS zz DE orphan\n//\n':
1. Parse stores gs DE/zz/orphan, with seqs s/AC and no zz sequence.
2. Parse-write-parse retains that structure including orphan GS.
Source54-60 stores GS independently,79-84 validates seqs/gc/gr only;
_validate_widths88-104 checks unknown names in GR, not GS. Writer118-120
emits GS values. Expectations source-derived, not run.

No valid-GS control authored: existing test_parse_wrapped_blocks_and_markup
29-35 and test_stockholm_semantic_roundtrip38-40 cover the known-sequence
fixture and roundtrip; duplicating them was dropped. Existing unknown-GR
rejection in test_stockholm_rejections52-53 is adjacent, not duplicated.
CLI tests use the same known-sequence fixture, no orphan annotation case.

Tip imported from local H32 bundle, SHA256
dda97488cc3894d5c2b98c2d3fa6d6d306b622a66c09d9adb597f5a875491100,
sole prerequisitefb9e276a74860098bdcc78001d63bde8bddd2757; verified locally.
RUN git/text/date/hash/diff/bundle only. NOT RUN pytest/tests, import,
product, AST/compile/syntax, pip or network. No PASS, execution result or
mutation evidence claimed. Peer owns independent execution and integration.
