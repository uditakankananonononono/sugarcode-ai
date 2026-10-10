# H36 exact literal TSV output characterization

Parent exactly60c5ca854c2a98a109891916fa59f66fd039c58a.
Two new tests+contract only, no source/helper/old-test edits, no write_bundle
scope. Findings, not independent CSV/TSV standards or biological validation.

## Gate and sequence, 2026-10-10 IST
Full exporters1-104, exporter tests1-58, reservation tests1-50 read at20:51:26;
public report export route and H32 tests read by20:51:37. Both report_studio
consumer test files read fully before authoring20:51:46. Tests authored before
execution, contract afterward. Documentary self-report, not comprehension proof.
Source exporters blob541e2ddf3f196692f689b2fa4bbeb1895a8946f7;
exporter tests f8c3cb2746c955f00f5412a8d4576c666ddac92d;
reservation a3090230e6b07228394a5794ef58d3963135549a;
H32 test b12624d86595f1ac8ab85fda1ce51890cdbc161d.

## Exact bounded expectations
Explicit a,b columns with embedded tab, newline, quotes and None pins the full
literal string including delimiter, doubled quotes, field quoting and LF.
Sparse rows b=1 then a=2 pin full default sorted-union header and missing cells.
Expected strings were stdlib predictions before execution, then observed to
match actual runtime exactly. No discrepancy or corrective rewrite occurred.
Existing TSV controls assert headers only; existing CSV roundtrip uses CSV,
not TSV body. H32 excludes TSV. No exhaustive coverage/ownership claim.

## Author execution, independent audit still required
New2 PASS0.17s; six-file new+exporter+reservation+H32+report_studio spec+realdata
45 PASS0.75s. tests/self_improve plus those six:1885 PASS/13 XFAIL36.91s,
not configured global suite. Five temporary mutants killed: comma TSV,
reverse default columns, None-to-text, missing-cell marker, empty TSV stub.
Source restored byte-exact; new tests rerun. No product mutation committed.
No landing/push before independent audit and EXECUTE.
