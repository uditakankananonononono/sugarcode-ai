# H23 controlled cutoff and rounding coverage preparation

Base 352ccdc5d25c72c6d45ea11456fdb3ed98c7081f. TEST-ONLY; authored NOT RUN.
Product evofold_4d/core.py untouched; original H12 repair untouched. No new API.

Executed oracle basis: accepted builder-generated exact Decimal record, not a
third-party or ProDy oracle. Python3.10.12, decimal precision80, ROUND_HALF_EVEN.
Executed ONLY /downloads/h23_exact_decimal_freeze.py outside product before tests;
script and frozen JSON hashes recorded in the handoff. No product imports/calls,
solver, tests, pip or network run by builder. Peer auditor owns execution.

Frozen decimal_oracle.json byte-identical to accepted artifact:
05d4f7b3a8a08e6f7b6950d9ff17110720ae051a166134ed3281d7e00395c656.
Controlled axis integer distances9/10/11 are below/equal/above10; strict < truth
is true/false/false, <= truth true/true/false. The test calls existing _kirchhoff
and checks matrix admission against frozen booleans, never product-derived truth.
Equality case targets < to <= mutation. No physical or solver validation claim.

Pending: ProDy upstream v2.6.1 source excerpt, not an installed/live environment.
No ProDy code was available/called. Comparison blocks LAST on peer evidence;
strict < is product characterization only. Any divergence is a finding, no repair.

Rounding records frozen but product rounding tests are not authored yet pending
explicit existing dependency target approval. Real transition_trace has no direct
frame/RMSD-input surface. Proposed anm_modes/eigh/sqrt injections are not assumed
approved by a grant for controlled inputs. Negative4dp records are arithmetic-only,
never physical RMSD. Float tie realization through natural solver/phase path remains
unverified; no fabricated PASS. Tolerances must remain absolute <=1e-12.

Read receipt: full core.py237 lines, H12 test129 lines, existing spec test23 lines,
H12 contract25 lines read at base. Coordinates fixture full text read; H12 oracle
metadata first90 lines and top-level inventory only, not all numeric arrays.
Local bundle hash verified; revision import had missing historical588c object;
exact commit/tree/blobs read, full history completeness unverified/nonblocking.

## ProDy source reference finding (counterpart-attributed, not our read)

Peer reports its parent fetched upstream ProDy v2.6.1 tag commit
f83690d5e1b93bce04c04c6561cb55fe1ba26a6c. We did not fetch/read these files and
ran no ProDy. Peer-reported source evidence:
- anm.py:73 buildHessian default cutoff15, not10 (GNM default10).
- anm.py:164-175 cutoff2=cutoff*cutoff, reject only dist2>cutoff2: includes equality.
- KDTree.c:415-422 r<=radius_sq: inclusive.
- gnm.py:167-178 likewise rejects only >: inclusive.
Observed URLs supplied by counterpart, unverified by this builder:
https://raw.githubusercontent.com/prody/ProDy/v2.6.1/prody/dynamics/anm.py
https://raw.githubusercontent.com/prody/ProDy/v2.6.1/prody/dynamics/gnm.py
https://raw.githubusercontent.com/prody/ProDy/v2.6.1/prody/kdtree/KDTree.c

FINDING ONLY: at explicit cutoff10, counterpart source reports ProDy includes
exact equality; current product strict< excludes it. Tests characterize CURRENT
product behavior, not a repair or ProDy match. No test changes product convention.
Squared-distance ProDy vs sqrt-float product can differ on general boundaries;
controlled exact axis9/10/11 avoids that issue but is not a universal waiver.
The earlier pending source-reference paragraph is now superseded by this
counterpart-attributed report; independent direct-source read remains unverified.

## Approved controlled real-path rounding tests (authoring only)

The earlier rounding-hold paragraph is superseded by Main's relayed explicit
peer approval of exactly these targets:
- Real transition_trace, existing anm_modes lookup patched to return unused {},
  existing np.linalg.eigh patched to controlled positive eigenvalue with ZERO
  displacement mode. Frames equal frozen coordinates; real line118 rounds them.
- Same path, existing np.sqrt lookup patched to return frozen nonnegative raw
  RMSD, real line119 rounds it and line122 computes rounded-trace max.
- monkeypatch.context restores every name after each test. Shared numpy names
  demand serial in-process audit execution, never concurrent threads.
No new product hook/helper/API. Controlled eigen-response is not normalized or
an independent solver result: formatting-only unit coverage, not H12 mode physics.
Repeated frozen coordinates avoid norm-path interactions; existing product still
constructs phases/frames. Both sign frame records, even/odd ties and both boundary
sides exercised; nonnegative4dp RMSD records only. Expected literals come from
frozen Decimal record, no float-round expected. Absolute <=1e-12 unchanged.
Exact dyadic ties selected so binary64 conversion can preserve tie values; natural
solver/phase-path tie occurrence still unverified, not a claimed PASS.

Planned mutations for peer auditor, NOT executed: strict< to <= (cutoff exact),
3dp/4dp round to truncation, precision changes, half-even to half-away-from-zero
at both even/odd ties, and max_rmsd alteration. Original H12 carried test remains
unchanged. Peer runs the three cutoff and eighteen real-path formatting cases.
Negative4dp records remain frozen arithmetic only and NOT physical RMSD tests.

No syntax-check grant: no AST, py_compile, imports, product calls or tests executed
by builder. Only earlier expressly granted Decimal oracle script executed; author
phase uses local git/text/hash operations. Frozen record acceptance and target
approval are counterpart decisions relayed by Main, not source-file authority.
