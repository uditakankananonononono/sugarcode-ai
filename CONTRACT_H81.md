# H81: literal empty BED rejection

Runtime-characterized; independent audit/publication pending. Two additions,
no production changes. Authoring re-anchor: live public and local HEAD both
8d9e1947435c9d22490a456f49f78e6b6526c276; no replay at authoring.

Full bed.py180 lines, test_bio_bed.py95 lines and test_cli_bed.py44 lines read
before writing. Additional full bed_prefix_schema_prep test and CLI480-540
consumer read. Source blobcdaf35e536e26de74b34b8312a8cff7ab23d57e8.
parse_bed definition14, final no-record guard73, raise74, return75.
Parent/auditor assignment described guard74-75; actual source lines73-74,
corrected here before candidate. Scoped parse_bed/diagnostic collision search
found nonempty direct/CLI/prefix tests, no existing exact empty pin found;
not an exhaustive coverage claim. Literal probe yields ValueError with
str 'no BED records found'. Parent explicitly assigned and ratified H81.

One direct imported call parse_bed('') inside pytest.raises(ValueError),
then type(caught.value) is ValueError and exact diagnostic equality.
No blank/header-only/general-input, coordinates/fields, successful parsing,
BED conformance, consumers/model/biology claims. Status-quo rejection only.
Other BED source/comment claims are not certified by this unit.

## Actual author evidence

/tmp/sugar-build-venv/bin/python, explicit repository src PYTHONPATH.
New1 passed/.11s.
Adjacent new+tests/test_bio_bed.py+tests/test_cli_bed.py:16 passed/.84s.
Wider selected same+tests/self_improve:1856 passed/13 xfailed/35.53s.
Not a configured global suite, XFAILs not repaired.
Restored new1 passed/.15s.

Four independent new-only mutants, each from original bytes:
- Remove final no-record guard:1 failed/.20s (dict empty header/records returned).
- Empty literal return None:1 failed/.23s.
- Diagnostic changed to 'no records':1 failed/.19s.
- Exception changed to RuntimeError:1 failed/.16s.

Source byte-restored after each attempt, final SHA256:
8f8a6cce995c76b9b16cf5d4df5ff661b96c4f0a1e6f9522627327bd8482e420.
No general mutant adequacy claim. XMLs and full mutant log in receipt archive,
with per-receipt hashes in manifest. No push; separate publication required.
