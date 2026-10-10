# CONTRACT_H17: chemgpt_engine mass contract against frozen Batch Av3 evidence (AUTHORED, NOT RUN; test and contract only)
Base ea586991bad79824470f156578095992d2f69610. chemgpt_engine/core.py blob 275ce847865df163946882c29129925ce9cc7287 is UNCHANGED (no product edit: API, constants, rounding, scoring, Lipinski and extrapolation thresholds untouched). Authority: peer rulings relayed by Main, not independently authenticated by me.
Chronology (IST, 10 Oct 2026): fixtures copied and test written 16:37:44-16:37:54; this contract 16:37:57. No source edit exists to order against. Test before contract (self-reported).
## Evidence (peer-supplied, vendored byte-identical, not regenerated)
- tests/fixtures/h17_chemgpt_third_results.json sha256 635d7a5214bdb6d5a1c97bb1f95194f0d2a9f4822db6684a02a60e6e589a3dff; tests/fixtures/h17_chemgpt_third_input_freeze.json sha256 1225dda03a43152fed594321352969af4bfa852dd623f0fbbdd204cfbb67b984. Per the peer: RDKit 2025.9.1, run 2026-10-10, run-third.py, archive SHA 7b60ab42b56b7d1fe453d6127ceaaa0c771c84991541a4bf7041d528fedd1ea0 (archive not available to me; peer's claim). The frozen reference_mass values are the oracle of record; no live RDKit is used or required.
- Frozen protocol: 12 singleton fragments + 144 ordered pairs = 156 inputs; 8 explicit module refusals (first fragment fluorine, "fluorine cannot be the core of a larger molecule") reported separately, 148 returned; every returned SMILES sanitized; heavy atoms exact; mass abs <= 0.05 Da.
## Assertions (tests/test_h17_chemgpt_mass_contract.py)
- (i) public mw == round(own raw sum(FRAGMENT_MW) - 2.016*(n-1), 1) for all 148; (ii) the UNROUNDED raw sum is within 0.05 (abs, no epsilon) of the frozen RDKit reference_mass for all 148; (iii) public mw == frozen historical module_mass for all 148.
- 8 refusals asserted as ValueError refusals with no mass fields; 156 accounted in frozen order.
- Pre-authoring arithmetic (plain python on core.py constants and the frozen file, no module import, no RDKit): 148 rows, max unrounded error 0.005999999999971806 (sulfonamide,sulfonamide: 160.17000000000002 vs 160.176), none > 0.05, 0 rows where round(raw,1) != frozen module_mass. (Author's arithmetic, not an independent MolWt claim.)
## Tolerance and display
- Chemistry tolerance is on the UNROUNDED mass (<= 0.05 Da). The public mw is displayed to 1 decimal (round half per Python round), so the public value may sit up to 0.05 from the RDKit reference; no epsilon and no tie exceptions are used.
## Historical raw FAILs (retained, not erased, not reclassified in the original receipt)
- The Batch Av3 run recorded 3 FAIL rows with mass_abs_error 0.05000000000001137: [carboxyl,amide] C(=O)OC(=O)N module 89.0 vs ref 89.05000000000001; [ethyl_link,sulfonamide] CCS(=O)(=O)N 109.1 vs 109.15; [sulfonamide,ethyl_link] S(=O)(=O)NCC 109.1 vs 109.15. The fixture keeps verdict "FAIL" and the test asserts exactly these 3 and that value.
- Cause (peer ruling): ill-posed oracle, comparing the unrounded RDKit reference with the module's ROUNDED public mw and a strict <= 0.05 on floats at a .x5 tie. The unrounded raw sums (89.05, 109.147, 109.147) are within 1.4e-14, 0.003, 0.003 of the references.
## Policy correction
- The earlier proposed predicate "public mw == round(frozen reference, 1)" is WITHDRAWN: for the 3 tie rows it gives 89.1 / 109.2 / 109.2 against module 89.0 / 109.1 / 109.1. Replaced by (i)-(iii).
## RUN vs NOT RUN
NOT RUN: all tests, pytest, imports of sugarcode, RDKit. RUN: git, sha256sum, plain arithmetic on constants and frozen data, py_compile syntax check of the test file, file copies.
