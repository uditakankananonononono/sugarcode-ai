# S5-004.A02: executable educational analogies

Base source: 7ff2dc8748965fcfc55f6ffd3a2efcab4e592368.

Tests added before behavior changes reproduced five missing-helper NameErrors;
only the empty Promoter example ran. See before.txt. The initial CRISPR test
address was 21 characters and was subsequently corrected to an explicit
20-character address; its pre-fix failure was still the missing helper.

Every public CONCEPTS source block and translate_concept response now includes
its own stdlib/local string helpers and educational-only scope. No file access,
network request, biological prediction, or experimental outcome is performed.

- Transcription reads an in-memory DNA string and returns reverse complement RNA.
  This is distinct from execute_transcription, whose existing coding-strand
  T-to-U behavior remains unchanged.
- Translation includes the complete standard codon table and codon splitter.
- PCR is literal boundary-string duplication, not primer binding chemistry.
  It defaults to four rounds and refuses more than ten, bounding list expansion
  to 1,024 strings of at most 1,000 characters.
- CRISPR is exact forward-strand string addressing followed by insertion. It
  refuses absent/ambiguous addresses and accepts only the toy 20-character NGG
  address rule. It is not off-target analysis or a repair-outcome model.
- Mutation compares coding-frame string translations before and after one
  substitution. It is not transcript-aware consequence analysis.
- Promoter remains an educational object-state formula.

Bounded string/type/alphabet/position checks are included. Legacy callable
execute_* behavior and concept names are unchanged. No audit-ledger/spec claim
was broadened. README's existing narrowed analogy description is left intact.

Run:

```sh
PYTHONPATH=src pytest -q tests/test_dna_to_code_executable_analogies.py \
  tests/test_dna_to_code_spec.py tests/test_registry_disclosure_wave2.py \
  tests/test_registry_health_search.py tests/test_registry_truth_current.py
```

See after.txt for exact targeted results. No full-repository test run, external
provider test or biological accuracy claim. No push performed.
