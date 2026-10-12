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
