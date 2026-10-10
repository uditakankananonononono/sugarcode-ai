# H42 protein-summary strict classification threshold

Exact parentcb0048162955dc4af5c83ac7380b73ce888ec797.
One test parameterized over3 synthetic indices+contract only. No source or
old-test edit, physical half-life, instability-formula or biological claim.

## Source gate and chronology (2026-10-10 IST)
Full proteinprops.py1-261 and direct tests read visibly21:17:54 on this parent;
CLI test fully read21:18:07. Tip reverified21:18:21 before authoring. Attempted
sed281-345 returned no lines (source has261); that empty read adds no evidence.
Full visible source read already at exact parent. Later summary242-261 read
is not substituted for preauthor gate. Source8058dfae4914e05fc4cd61a77295a1bbc784b8f5;
direct test4a39c6516849f521d1173f132009fe94675d203a;
CLI6b83f1f0b81804ccbf2ce94b5c81977ef53948d1.
Tests first, execution afterward, contract last, documentary self-report.

## Narrow pin and coverage
Monkeypatch only instability_index, real protein_summary('AA') calls it once
with AA. Literal synthetic39.99/40/40.01 report stable/stable/unstable,
returned index equals round(index,2). These inputs already have2 decimals;
this does NOT independently exercise report rounding precision. Strict >40
only, not the formula, trained performance or physical predictions.
Existing summary test merely checks label membership stable/unstable; exact
boundary not found there. Direct proteinprops module importorskip Bio skips
whole module; CLI imports it and also skips. New file independent of those.

## Author runs
New3 PASS0.15s; new+proteinprops+CLI3 PASS/2 module SKIP0.30s;
self_improve+same3files1843 PASS/2 SKIP/13 XFAIL41.17s, not global suite.
Four temporary mutants killed: >=40 boundary, stable-label stub, unstable-label
stub, index-zero stub. Original source restored byte-exact; new3 PASS rerun.
No independent oracle/facade validation claim. Audit/EXECUTE before landing.
