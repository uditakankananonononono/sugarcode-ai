# H77: literal empty FASTA rejection

Status: runtime-characterized, awaiting independent audit and publication decision.

## Source and boundary

Base: 6d370cf0153c1f5a57294cf7794cd2516b231572.
Fresh full read: src/sugarcode/bio/fasta.py, 55 lines, blob e53da56159d9de7147f0cc6ac2d378d8fdba7104.
parse_fasta lines5-24; no-record guard22, diagnostic23.
Read H29 33 lines, H34 26 lines and test_bio_utils.py60 lines in full,
plus CLI fasta-stats/alignment and kmer loader consumer context.
Collision search: H29 preheader rejection, H34 mixed-case records,
utils roundtrip and restriction fixture parse are different inputs, not this pin.
Probe: parse_fasta('') raises ValueError, str exactly 'no FASTA records found'.

The new test directly imports sugarcode.bio.fasta.parse_fasta and calls it
once with the single literal ''. It checks pytest.raises(ValueError) and exact
str(exc.value) equality. pytest.raises accepts subclasses; exact exception-type
identity is not claimed. No production changes.
No blank, whitespace, header, casing, normalization, successful parse, consumer,
standard-conformance, biology, general empty-like/falsy or guard-placement claim.
This is a status-quo rejection characterization, not a parsing specification.

## Runtime evidence

Interpreter: /tmp/sugar-build-venv/bin/python; explicit repository src PYTHONPATH.
New-only: 1 passed/.13s.
Adjacent: new + tests/test_h29_fasta_prefix_characterization.py +
tests/test_h34_fasta_case_characterization.py + tests/test_bio_utils.py:
19 passed/.33s.
Wider selected: adjacent + tests/self_improve:
1859 passed/13 xfailed/46.51s. This is not an entire configured-suite run.
Restored new-only: 1 passed/.18s.

Independent one-at-a-time mutants, new-only test:
- Remove no-record guard: 1 failed/.18s (returns []).
- Replace exception with RuntimeError: 1 failed/.12s.
- Change diagnostic to 'no records': 1 failed/.13s.
- Empty literal early return None: 1 failed/.16s.

Named survivors:
- Remove record uppercasing: 1 passed/.21s. No records processed for this input;
  no casing or successful-parse coverage.
- Add equivalent empty-literal rejection before records/loop: 1 passed/.11s.
  No guard-placement claim.

Source restored byte-exact after each mutant; final source SHA256:
cb898c1d85eb8ba9e04fab108a7a731c0d94e9bb8ef952b555d0a9ef24eee21a.
XML receipts and full mutant log accompany the read-only audit package.
Publication requires separate parent instruction after independent verdict.
