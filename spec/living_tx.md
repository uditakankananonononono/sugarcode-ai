> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep
> learning, foundation, GNN, or RL model, whatever the text below says. See
> STATUS.md for what is actually verified.

# Living Tx

Living Tx: A design tool for engineered probiotics used as living therapeutics for disease treatment. It suggests safe strains and genetic modifications while simulating their impact on the gut microbiome. Living Tx predicts clinical success probabilities and models therapeutic compound delivery, providing a platform for developing next-generation biological medicines.

moved from spec/neohunter.md L32-37 at commit 8a214135
Living Tx
Living Tx is a synthetic biology platform for engineering programmable microbial therapeutics that function as autonomous living drug delivery systems within host biological environments. At the genetic circuit level, the system designs modular regulatory networks composed of promoters, repressors, riboswitches, CRISPR-based regulators, and synthetic transcription factors. These circuits are modeled using stochastic chemical kinetics governed by the chemical master equation, capturing intrinsic gene expression noise, transcriptional bursting, and resource competition effects such as ribosome allocation and metabolic burden.
Metabolic modeling is performed using genome-scale metabolic reconstructions and flux balance analysis, enabling simulation of cellular growth, energy utilization, and metabolite production under host-specific environmental conditions. These models ensure engineered strains remain metabolically viable while performing therapeutic functions. Constraint-based optimization is used to balance growth rate with therapeutic payload production, ensuring long-term stability within competitive microbiome ecosystems.
Host–microbiome interactions are modeled as multi-species ecological networks governed by generalized Lotka–Volterra dynamics combined with metabolite exchange coupling. This enables simulation of microbial competition, colonization resistance, and ecosystem-level stability under perturbations introduced by engineered strains. The system also models immune system interactions with engineered microbes, including pattern recognition receptor activation and inflammatory response thresholds.
Therapeutic delivery is simulated using diffusion–reaction equations that capture secretion, degradation, absorption, and spatial transport of biologically produced molecules. These models enable prediction of pharmacokinetic-like behavior of microbial therapeutics, including concentration gradients across intestinal or tissue compartments, time-dependent exposure levels, and local efficacy zones.
Safety engineering is implemented through synthetic containment systems including auxotrophy dependencies, kill switches activated by environmental triggers, quorum sensing-based population control, and genetic firewalls preventing horizontal gene transfer. Evolutionary stability analysis uses probabilistic mutation and selection models to estimate long-term genetic drift and escape risk, ensuring containment integrity over extended therapeutic timescales.
