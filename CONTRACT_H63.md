# H63 literal short-input GC window fallback

Parent: 1624a6d68c499ee0f8aed5ce94ce2844b5bf2787.
Only this contract and one independent test added; no product-source or
old-test edits. One literal gc_windows('GC', window=4) == [(0, 1.0)] pin.
No general window-policy, consumer/design/report, model or biology claims.

## Documentary read and overlap gates

2026-10-10 IST: publicdf2cdce597707413209eb30dc22bd9b87ae63f6e verified,
full sequence174/bio_utils60 read22:44:20. Source blob
b660260768248d22ee1dfbf4b1cb13e98dd89c89; direct-test blob
4708c7d6a61495dc35f4a362cee458de4b3a5c56. Full codon_opt/core286
read22:44:32, blob752d27baf272f415d958f1290a6332096a1d425b.
Direct consumer tests codon_opt21/spec17 read22:44:26, published73 read
22:44:32. Actual consumers42/273 use gc_windows(...,60). No no-caller claim.
Tracked gc_windows/GC_window searches found no direct short-input fallback
pin. Consumer tests overlap overallGC/design outputs, not this literal call.
Static scoped search is not exhaustive dynamic semantic proof.

Parent ratified22:44:48. Publicdf2cdce5 reverified and sequence88-105 visibly
re-anchored22:44:54 immediately before authoring the test. H62 landing
interrupt arrived after those runs, before mutants/contract/commit. H63 test
left untouched during H62 staged==candidate==committed landing. New public
1624a6d6 reverified and same source88-105 re-anchored22:46:43, test rerun on
new tip. H62 adds only unrelated rnaseq test/contract. Read chronology is
documentary self-report, not independently certified.

## Exact source-derived scope

With this literal2-base input and4 window, max(1,len(s)-window+1) is1.
Default step is2, yielding start0 only; slice isGC, gc_content yields1.0.
This pins this returned single-element list, start and fraction only.
It does not test longer sequences, nonzero starts, multiple windows,
custom steps, other fractions, cleaning or general window policies.

## Author receipts; independent audit required

Existing Python3.10.12/pytest9.1.1, no dependency installation.
Pre-H62 new1PASS/.12s, five-file adjacent30PASS/1.30s, samefive plus
self_improve1870PASS/13XFAIL/37.46s. Post-H62 new1PASS/.12s,
adjacent30PASS/1.12s, wider1870PASS/13XFAIL/41.41s, no skips.
Five files: newH63, test_bio_utils.py, test_codon_opt.py,
test_codon_opt_spec.py, test_codon_published.py. Wider is not global suite;
thirteen strict-XFAIL canaries are not implemented repairs.

Four independent temporary mutants each1FAIL: remove max fallback,
change fallback lower bound1 to0, start range at1, force output fraction0.
Named out.append((0,gc_content(w))) survivor1PASS/.11s retained: this input
has only start0 and cannot distinguish hardcoded0 from general offsets.
Source byte-exact restored SHA256:
c7e83e0a5903c1375fbf493cab16208ea329718f1c56e7bb48226606b6c60b70.
Restored new1PASS/.12s. No source mutation committed.

Independent audit and explicit EXECUTE required before publication.
