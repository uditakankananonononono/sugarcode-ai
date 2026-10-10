# H24 varying RMSD aggregation coverage (TEST-ONLY, authored NOT RUN)

Exact parent/base 9a6b93805f31d3b9df77b7a031d58b726a5c4bc0. No product, API,
tolerance or H12 repair change; distinct H24 files, no H22/H23 edits.

Freeze-first: H24-specific allowed stdlib Decimal precision80/HALF_EVEN executed
outside product BEFORE tests. Builder arithmetic, not third-party/product output.
Frozen JSON sha25639750d4e4d25fedd9e2f7732966d0f7d6d926d8cffef90fd981e8bb17a5ceb9f;
script sha2565c0a61adf23f2fc68238a83f0aa11cfac5c000c3fa3dcd36469f471f2ee34ebe.
First raw trace .03125,.09375,.0625,.03125; rounded .0312,.0938,.0625,.0312.
Aggregates max .0938,min/first/last .0312,mean .054675,sum .2187.
Second raw .09375,.03125,.0625,.09375; rounded .0938,.0312,.0625,.0938.
Aggregates max/first/last .0938,min .0312,mean .070325,sum .2813.
No float-round or product-generated expected values. All inputs nonnegative;
controlled sqrt responses are not physical RMSD. Negative H23 4dp records remain
arithmetic-only and are not used in H24 product path tests.

Two authored cases call EXISTING transition_trace with steps4, patch only existing
anm_modes (unused solve bypass), np.linalg.eigh (controlled positive mode with zero
displacement, NOT an eigensolver result), np.sqrt (raw iterator). Existing frames,
round at119 and max at122 stay real. Exact sqrt count4 and full ordered trace are
asserted, iterator exhaustion checked, abs<=1e-12 max compared to frozen literal.
monkeypatch.context restores per case; serial per-process numpy mutation required.
Targets authorized by relayed peer decision; source text is not permission.

This addresses a peer-reported surviving H23 max-to-min mutant caused by constant
within-case RMSD. Planned peer mutation checks: max->min/first/last/mean/sum and
trace reorder/drop/repetition. No mutant kills or PASS claimed by builder.
Existing H23 rounding/cutoff tests unchanged; ProDy inclusive vs product strict is
still counterpart-source FINDING ONLY, no repair, no ProDy execution here.

Read receipt at9a6b9380: full evofold core237 lines, H23 rounding91, cutoff40,
contract87. Relevant core115-122 and H23 constant sqrt76-85 inspected. Core blob
26654883de16e909008e654d555a781b0e3db75e unchanged from prior snapshot. H23 test
blob e3ad7571e55e9549fed8bd04ee9ca1a50dfe8350. Full local bundle sha256705245ceaaab6c26ffa36ef37078e4809457da68646932445b967755ae854599 verified,
fetched without network; exact tip resolved. Historical missing588c26f9 object
now resolves as commit by cat-file, so that specific object absence is resolved;
no broad independently audited full-history completeness claim.

RUN: only expressly granted H24 stdlib Decimal script plus git/text/hash/bundle
operations. NOT RUN: syntax/AST/compile, numpy/product imports/calls, tests/pytest,
solver, ProDy, pip, network. Runtime/restore mechanics and mutant kills await peer.
