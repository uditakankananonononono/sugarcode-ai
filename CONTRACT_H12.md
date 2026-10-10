# CONTRACT_H12: evofold_4d transition_trace diagonal double-count (AUTHORED, NOT RUN)
Base 5c21515122c679408bd306886b2903ae428b4f2c (core.py blob d756828d95d8a1f3e70b0790b5dca55c625c79c3). Authority: peer rulings relayed by Main, not independently authenticated by me.
Chronology (IST, 10 Oct 2026): fixtures copied and tests written 15:45:59-15:46:16; source edited 15:46:21; this contract after. Tests were edited BEFORE source.
## Change
- transition_trace: the ordered-pair loop (j over range(n), with i == j skip) visited each contact twice and applied "-=" to both diagonal super-elements twice. Replaced by the in-place j > i loop used by anm_modes. Nothing else changed: no shared helper, no new eigenvector API, no signature change.
- NOT changed (out of scope, by ruling): the unused res = anm_modes(...) line, the steps=1 divide-by-zero, mode selection, rounding, return shape.
## Oracle and fixtures (hash-pinned byte-identical copies, tests/fixtures/h12_evofold/)
- oracle.json sha256 098a99bb6d1c3922c003ed3f49d871d56ab94f59223ea3e66b3581fbd8b0bf98
- coordinates.json sha256 13f3e820715b178b0446bf5d6e3db963c47e4135b0be3fa633595deb70d079f3
- Frozen peer oracle: ProDy 2.6.1, numpy 2.2.6, scipy 1.15.3, 1CRN chain A, 46 CA, cutoff 10, gamma 1, first positive ANM mode, nondegenerate (cluster dimension 1). Not a biological validation.
## Test design (deliberate internals testing)
- PRIMARY: pass-through spy on numpy.linalg.eigh (global numpy dependency: it patches the numpy.linalg module attribute while the call runs and is restored in finally). Call order in transition_trace: call 1 is the solve inside the unused anm_modes call; call 2, the LAST, is transition_trace's own solve. Only the LAST call is used. Raw checks: six zero eigenvalues then positive modes, first 12 eigenvalues vs oracle (abs 1e-8 OR rel 1e-6; see the tolerance label below), used mode vs canonical unit vector after ONE global sign L2 <= 1e-7, projector max abs <= 1e-7.
- SECONDARY: ROUNDED public frames vs the oracle's ROUNDED 3 dp frames, max abs <= 0.00050001 after ONE global sign for all frames (other sign built as round(2*C0 - unrounded reference, 3)); rounded 4 dp RMSD <= 0.00005001.
- No raw frame instrumentation and no claim about reconstructed raw frames.
- SUPPLEMENTARY only: Hessian rows sum to zero and symmetry.
## Eigenvalue tolerance label (explicit)
- The eigenvalue comparison (abs 1e-8 OR rel 1e-6) is the BUILDER's interpretation of the two frozen eigenvalue tolerances in oracle.json as alternatives. It is NOT the original frozen-tolerance assumption: eigenvalues were not previously ruled. The +918134098571 side has since RATIFIED this interpretation (peer-reported, relayed by Main, not independently authenticated by me). Rationale given: OR suits near-zero absolute values (the six zero modes) and relative elsewhere.
- Mode L2, one global sign and projector tolerances (1e-7) are unchanged.

## Risks (unverified, not run)
- core uses d < cutoff (strict) for contacts; the ProDy convention at exactly 10.0 A is not verified by me.
- Rounded-to-rounded 0.00050001 can in principle fail if a raw value sits within ~1e-12 of a rounding boundary; peer-frozen tolerance, used as ruled.
- The spy needs the call to go through np.linalg.eigh attribute lookup (it does today).
## RUN vs NOT RUN
NOT RUN: all tests, imports, SugarCode, solver. RUN: git, sha256sum, text edits only.
