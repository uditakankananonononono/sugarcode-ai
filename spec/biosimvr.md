> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep
> learning, foundation, GNN, or RL model, whatever the text below says. See
> STATUS.md for what is actually verified.

# BioSimVR

BioSimVR: A conceptual virtual reality interface for running experiments in a simulated 3D laboratory environment. It describes key observations and conclusions for complex tasks like molecular docking or CRISPR design. BioSimVR provides an immersive way to visualize biological data and test hypotheses, offering a cost-effective platform for exploration.

## Whole-claim corrections (2026-10-12)

These corrections apply to the original wording above. They describe the
implementation at commit 99cb2d329690cf946ae491cb3ca027ee66b7f656 and do not
claim that the aspirational capability has been implemented.

- S5-104.03.C02, original claim: "visualize biological data".
  Corrected scope (OVERSTATED): Coordinate arrays are not a delivered visualization; rendering is absent/unrunnable.
- S5-104.01.C01, original claim: "virtual reality interface".
  Corrected scope (UNSUPPORTED): No virtual reality interface exists. The shipped
  module is a headless coordinate scene model plus deterministic simulations;
  nothing renders and no headset or 3D client is involved.

- S5-104.01.C02, original claim: "running experiments".
  Corrected scope (SCOPED): The module runs scripted, seeded simulations of
  protocol steps, not laboratory experiments. Outputs are computed numbers and
  pre-written strings.

- S5-104.01.C03, original claim: "simulated 3D laboratory environment".
  Corrected scope (SCOPED): A coordinate scene graph of named lab objects
  (benches, instruments, positions) with scripted move/interact commands; not a
  physical simulation of a laboratory.

- S5-104.02.C01, original claim: "molecular docking".
  Corrected scope (SCOPED): One rigid-pose Lennard-Jones optimizer over
  caller-supplied coordinates and one fixed docking_studio.dock call on a fixed
  pocket/ligand pair; not a force-field docking engine and no affinity claim.

- S5-104.02.C02, original claim: "CRISPR design".
  Corrected scope (SCOPED): Enumeration of NGG-adjacent guides scored on GC
  fraction, homopolymer length and sequence uniqueness heuristics; no off-target
  search and no editing-efficiency prediction.

- S5-104.03.C01, original claim: "immersive".
  Corrected scope (OVERSTATED): There is no interface at all; interaction is by
  Python function calls returning dictionaries.

- S5-104.03.C03, original claim: "test hypotheses".
  Corrected scope (SCOPED): Hypothesis probing is limited to running the
  deterministic simulations and reading their summary fields; nothing about
  biological hypotheses is established.

- S5-104.03.C04, original claim: "cost-effective".
  Corrected scope (UNSUPPORTED): No cost model or cost comparison exists. The
  protocol simulator counts a fixed 0.25 currency-unit consumable charge per
  pipette step; no comparison against laboratory work is made.
