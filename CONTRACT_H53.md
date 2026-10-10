# H53 one invalid-residue diagnostic before pH check

Parentbc00975e3a33d7a0db7f3a1177e7c638ac256c8c.
One test+contract additions only. No source/old-test edit, chemistry/pH
accuracy, input-range generalization or other validator behavior claim.

## Visible gate (2026-10-10 IST)
Full proteinprops1-261 and bio_proteinprops1-107 read22:13:42; full actual
cli_protein1-22 and H42 test/contract read22:13:52, CLI777-789 inspected.
Repository charge/diagnostic coverage search inspected. Initial nonexistent
CLI-protein-props path gave no evidence, actual file subsequently read.
Source8058dfae4914e05fc4cd61a77295a1bbc784b8f5;
direct4a39c6516849f521d1173f132009fe94675d203a;
CLI6b83f1f0b81804ccbf2ce94b5c81977ef53948d1.
Ratified22:13:56; public fetch verified exact parent, relevant160-170 and
217-232 visibly re-read before test22:14:01. Test first, execution next,
contract afterward. Documentary self-report, not comprehension proof.

## Exact scope and overlap
charge_at_ph(' zx ',15) raises exactly ValueError and exactly
non-standard residues ['X', 'Z'] - only the 20 standard amino acids are supported
Sorted multi-residue diagnostic and precedence over invalid pH only.
Existing invalid-sequence regex tests call molecular_weight, existing invalid
pH test uses valid AA. No conflicting-invalid sequence+pH diagnostic found.
Whitespace/case handling is incidental to this literal, not a separate
validator behavior acceptance claim. No successful chemical value asserted.

## Author execution and environment
New1 PASS0.15s; new+bio_proteinprops+cli_protein+H42:4 PASS/2 module SKIP0.47s;
self_improve+same4files1844 PASS/2 module SKIP/13 XFAIL45.05s, not global suite.
Module-level Bio importorskip skips entire adjacent bio and dependent CLI
modules in my env; their pre-oracle tests did NOT execute. New/H42 independent.
Four temporary mutants each1F: pH checked first; descending residue order;
diagnostic changed; uppercase removed. Source restored byte-exact, src diff
clean, restored new1 PASS0.11s. No skipped-module validation claim.
Independent audit and exact EXECUTE before landing.
