# CONTRACT_H13 (final replacement; supersedes 0e0650e2 and 1ad4d197, which are history only and must not be applied): virtual_cell pFBA stage 2 uses the unrounded stage-1 optimum (AUTHORED, NOT RUN)
Base 465d7684db06c866646feb0f3036912f26b8c5e4 (core.py blob 4db6d027b8feb4b41d139b5928f51a24034124bb). Authority: peer rulings relayed by Main, not independently authenticated by me.
Chronology (IST, 10 Oct 2026): fixtures copied and tests written 15:52:41-15:52:54; source edited 15:53:04; this contract after. Tests were edited BEFORE source. H13f revision: test public checks changed 15:55:17-15:55:21 (after the original artifact 0e0650e2, which is kept as history only and must not be applied together with this commit); source and fixtures unchanged from 0e0650e2.
## Change
- New private helper _fba_with_raw returns (public fba dict, raw optimum or None). fba() is now a thin wrapper returning element 0: its result dict, keys and rounding are byte-for-byte what they were.
- pfba stage 2 lower bound on the objective reaction: max(lb, raw_optimum * optimum_fraction - 1e-9), where raw_optimum is the unrounded stage-1 objective. Before it used the 6 dp rounded public objective (round-up of +4.93e-7 for the textbook WT, +5.03e-8 for zero O2, by my arithmetic from the oracle values), which could push the floor above the true optimum.
- No new slack policy, no public API or signature change, public return shape unchanged. The failure fallback ({**first, "method": "fba", "pfba_stage": "failed: ..."}) and the early return of an infeasible stage 1 are unchanged lines; first is still the rounded public dict.
## Oracle and fixtures (hash-pinned byte-identical copies, tests/fixtures/h13_virtual_cell/)
- model-input.json sha256 3fbb889a94dfcedcb9fe63cdd9386394d6c8fae8b713e0577c2ceaa4fb488a9e (copy approved by ruling)
- oracle.json sha256 8a0da147c38c2fc3e0a57cb426d0f1dd2f1ed2bd9aace809b58322aa251d7306 (hash-pinned copy approved by ruling)
- Frozen COBRApy 0.30.0 textbook model, 72 x 95; WT and EX_o2_e=[0,0] are the only scored conditions.
## Test design (deliberate internals testing)
- Pass-through spy on core.linprog (real solver runs). Exactly two calls: stage 1, stage 2. Call 1 raw -res.fun vs stage-1 oracle (0.8739215069684279 WT, 0.21166294973531258 zero O2) rel 1e-9. Call 2 actual bounds entry for the objective reaction equals raw optimum - 1e-9 (abs 1e-15), is <= the raw optimum, and differs from round(raw, 6) - 1e-9. Call 2 raw res.fun vs oracle total absolute flux (518.4220855176071 / 335.65061686292484) rel 1e-6.
- Public predicate, VERBATIM (peer ruling, relayed by Main): "objective, biomass AND total flux each must EQUAL round(CANDIDATE'S OWN RAW internal value, 6) EXACTLY. RAW internal primary still oracle stage1 REL 1e-9 WT 0.8739215069684279 / zero O2 0.21166294973531258; raw total REL 1e-6 to 518.4220855176071 / 335.65061686292484. Statuses EXACT. NO comparison PUBLIC to PRE-ROUNDED ORACLE constant." The raw values come from the spy: objective = -res.fun of call 1; biomass and total = the stage-2 res.x split v = x[:n] - x[n:], v[objective index] and sum|v|. No pre-rounded public literal is pinned anywhere in the test or this contract. Statuses/method exact: pFBA, optimal, no pfba_stage key. Degenerate flux vectors are not compared.
- Superseded-policy results (not product-failure proof): the earlier absolute-tolerance and pinned-literal public policies produced actual floored public totals of 518.422085 / 335.650612 against pre-rounded oracle constants; those results are kept as receipts of superseded policy only.

## Spy robustness (peer audit finding, H13f)
- The first artifact's spy did float(res.fun) unconditionally, so a stage-2 failure (res.fun None) crashed the spy with a TypeError. The earlier pre-repair failures observed by the peer were therefore INCIDENTAL spy crashes, not assertion discrimination; those crash receipts stay as they were and no mutation-proof claim is made. Now the spy records fun as None when res.fun is None (checked before coercion) and never raises; the test then fails on intentional assertions (call count, stage-1 success, floor <= raw optimum, floor == raw optimum - 1e-9, floor != rounded-based floor, stage-2 solver success, then raw totals). Spy robustness and final public predicate edits are in the test file; this final revision's test edit ran 15:57:18-15:57:22 IST, before this contract text. Not run: no claim that the pre-repair code now fails on these assertions.

## Not done / unverified
- No test forces the fallback path; accepted by ruling (path untouched). Preservation is by source diff only (carried finding).
- Behaviour change for optimum_fraction < 1: the floor now scales the raw optimum instead of the rounded one. Not tested by the oracle.
- Whether existing tests that use pfba (test_virtual_cell*.py, others) still pass is UNKNOWN (not run).
## RUN vs NOT RUN
NOT RUN: all tests, imports, solver. RUN: git, sha256sum, python json shape reads, text edits only.
