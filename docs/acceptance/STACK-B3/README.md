# STACK-B3: ChemGPT row closeout

Base source: 692143ee. Input contains 120 rows. Two rows with pre_verdict VERIFIED
are excluded; 118 rows are processed. Post-audit grades
do not supply independent proof. Original input fields are preserved as history.
Only new corrected_claim, decision and evidence fields describe this patch.

No final COMPLETE label is issued. CORRECT rows narrow current descriptions,
without adding the missing model/data/capability. BUILD is used only for the
bounded subset parser boundary. Independent reproduction fields are left empty.

Parser change: refuse unsupported tokens, empty branches, dangling/repeated
bonds, invalid ring closures and non-string/oversize input. The parser remains a
lexical subset, not a chemistry sanitizer or valence checker. Existing fragment
assembly, descriptor constants, property scores and route formulas are unchanged.
C((C)) and C(=1CC1) still accept; the listed guards do not establish general
SMILES grammar closure. No existing tests were altered or loosened. New regression tests were committed
before code; a clean tests-only worktree reproduces 17 failed and 3 passed when
the code patch is absent. After the patch, targeted parser, ChemGPT and H17 tests
report 46 passed and 1 skipped (optional RDKit test). No fresh RDKit/network
oracle or full repository run is claimed.

Run:

```sh
PYTHONPATH=src pytest -q tests/test_stack_b3_parser_boundary.py \
  tests/test_chemgpt_engine_spec.py tests/test_h17_chemgpt_mass_contract.py
```

`closeout.csv` contains the 118 active rows, with source citations and reasons.
Excluded IDs: S5-006.A03 and S5-020.A03. Their original evidence remains
outside this publication package. Source ranges prefixed
692143ee refer to the input pin before the parser insert shifted later lines.
The specification additions preserve the original banner and text. No push.

CSV exports use LF line endings. A subsequent installed-RDKit targeted run
reported 47 passed; the original local run remains recorded as 46 passed and
one optional-dependency skip. This changes no parser/chemistry scope.

Coordination-only source quotes omitted; original evidence retained privately.
