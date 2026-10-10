# H37 notebook structural-check characterization

Exact parent853890644ad46c56e81a33ac6c3ae9ff704d4985.
Three tests+contract only. No source/old-test edit. No notebook execution,
nbformat schema certification, biological or valid-execution claim.

## Source gate and sequence (2026-10-10 IST)
Full notebook.py and direct notebook tests read20:55:12; report_studio spec
read20:55:23; CLI report tests fully read before authoring20:55:32. Tests
written before execution, contract afterward. Documentary self-report only.
Source blob590969f221edb378a12f90f441b085385e92544c;
direct-test blob5284a3d61eadfe1ccbcf04c479f1899f0326a7a6.

## Bounded findings
Exact ordered problem list for nbformat3/missing minor/nonobject cell/invalid
cell type and numeric source/code cell missing outputs and execution_count.
Raw cell source first-newline-second-newline becomes two newline-preserving
segments, metadata empty and no code-only fields. A markdown source list with
one numeric member yields the exact source-type diagnostic.
All expected literals derived from the current code, not external schema.
Existing malformed test checks any matching substring, not full order;
raw construction and invalid list-member shape not pinned there. No exhaustive
ownership/coverage claim. User-visible "valid" remains the existing structural
checker meaning; this unit does not upgrade it to executable/schema-valid.

## Author execution, not independent verdict
New3 PASS0.15s; new+notebook+CLI report+report_studio spec23 PASS0.70s.
tests/self_improve plus those four1863 PASS/13 XFAIL36.71s, not configured
global suite. Five temporary source mutants killed: reversed problems,
raw type removed, newline retention removed, bad source list accepted,
empty-problems stub. Source restored byte-exact, new tests rerun.
No source mutation committed; independent audit and EXECUTE before landing.
