# Catalog stack disposition

Base: 692143ee3999b08e816e0b90ef3cd39f3c030763. This audit addresses 140 supplied
rows. None had a pre-audit VERIFIED label, so none were excluded.

Counts: COMPLETE 0; PARTIAL 140; UNSUPPORTED 0. Independent reproduction fields
are blank. BUILD: 3; CORRECT: 137. PARTIAL is a row disposition, not proof of the
original source claim. The source spec banner is unchanged.

Build commit a211e9b adds an architecture part-budget refusal, sliding GC windows
with explicit coordinates and strict DNA alphabet, and SBML L3V2 core serial
stoichiometry. It adds compartments, required species attributes, serial reaction
references and a separate namespaced flux annotation. No kinetic-engine or lab
compatibility claim is made. python-libsbml is added to the dev dependency set
for parser/consistency tests.

Tests: 42 PASS across four focused module suites. Four new tests fail with only
the core file replaced by the parent version, and pass when restored. Logs are
reverted-red.txt, restored-green.txt and regression-green.txt. The separate parser
check uses libSBML and rejects severe consistency errors in the exported fixture.
There is no full-suite, wet-lab, live-data or scientific-performance claim.

The CSV names the changed function line, build commit and exact red test node for
each BUILD row. Both SBML test nodes are attached to the SBML row; each failed
separately. CORRECT rows state the smaller callable behavior or an unresolved
source capability, with cites limited to the module, spec and existing focused
tests read for this work. Absence statements refer to the inspected module, not
the repository as a whole. Historical result labels are not independent evidence.

Source claims involving laboratory execution, source integration, autonomous
learning, model training, experimental prediction and phenotype performance are
not replaced with new claims of those capabilities. Original text remains for
traceability; the appended row-local correction section supersedes it for each
listed ID. No original quotation is needed in the new CSV, avoiding accidental
republication of superseded affirmative labels.
