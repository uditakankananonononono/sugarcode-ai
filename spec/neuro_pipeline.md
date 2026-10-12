> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (a small NumPy MLP, SVD, leaky integrate-and-fire and Beta-count updates) -
> NOT a deep learning, foundation, GNN, or RL system, whatever the text below says. See
> STATUS.md for what is actually verified.

# Neuro-Pipeline

Neuro-Pipeline: Neuro-Pipeline can be reimagined as a closed-loop, neuro-symbolic MLOps system that not only trains biological deep learning models but actively interrogates and augments them using principles from cutting-edge computational neuroscience. At its core, the platform would orchestrate large-scale foundation models for biology—such as protein language models and structure predictors—while integrating brain-inspired architectures like spiking neural networks (SNNs), predictive coding frameworks, and hierarchical Bayesian models. Training pipelines would move beyond static supervised learning to incorporate continual learning and synaptic plasticity rules (e.g., STDP-inspired updates), enabling models to adapt dynamically to new biological datasets without catastrophic forgetting. The system could manage multi-modal inputs—genomic sequences, cryo-EM densities, single-cell RNA-seq, and electrophysiological traces—aligning them through shared latent representations learned via contrastive and self-supervised objectives.

> **Status at 99cb2d32 (rows S5-047.xx):** the trainable model is a one-hidden-layer NumPy MLP (`MLP`).
> No protein language model, structure predictor, hierarchical Bayesian model, cryo-EM, single-cell RNA-seq
> or electrophysiology code exists, and no contrastive or self-supervised objective. `spiking_dynamics` is a
> leaky integrate-and-fire loop separate from the MLP. `predictive_coding` relaxes a state toward the mean of
> the observations (no generative hierarchy). `continual_update` is a weight-anchor penalty without a Fisher
> term; on two opposite toy tasks, task-A accuracy fell from 0.993 to 0.017 (lambda 0), 0.013 (1), 0.040 (10),
> and to 0.520 with task B at 0.487 (100). `feedback_reward_update` is not wired to training, so the loop is
> not closed. S5-047.01.C01, S5-047.01.C03, S5-047.02.C03 downgraded to OVERSTATED; S5-047.04.C05 to UNSUPPORTED.

A defining feature would be its ability to map internal model representations to interpretable neurobiological analogues. Instead of generic attention maps, Neuro-Pipeline would generate circuit-level explainability by reconstructing “functional connectivity graphs” within the model—analogous to connectomics in the brain—highlighting which subnetworks correspond to structural motifs, binding pockets, or regulatory elements. Techniques like representational similarity analysis (RSA) and manifold alignment could be used to compare neural network embeddings with real neural data (e.g., fMRI or calcium imaging), enabling a bidirectional understanding: using neuroscience to interpret AI, and AI to hypothesize about brain function. This would push explainability from visualization into mechanistic insight.

> **Status at 99cb2d32 (rows S5-048.xx):** `functional_connectivity` thresholds |W1 x W2| weight products
> (19 nodes, 32 edges in the probe); it is a weight graph, not activation-based functional connectivity, and
> maps to no motif, binding pocket or regulatory element. `rsa` correlates input-space and hidden-space
> distance matrices (0.741 in the probe); it never reads fMRI or calcium-imaging data. `align_modalities` is
> per-modality PCA plus cosine of unpaired rows, not manifold alignment. S5-048.01, S5-048.03.C02 downgraded
> to OVERSTATED; S5-048.03.C03 to UNSUPPORTED.
On the training side, the platform would support hybrid simulation-learning loops where neural networks are co-trained with differentiable physics and biology engines. For example, a protein folding model could be jointly optimized with molecular dynamics simulations, using differentiable force fields to refine structural predictions in real time. Similarly, gene regulatory network models could be trained alongside SBML-based simulators, where discrepancies between predicted and simulated dynamics are backpropagated as learning signals. This creates a system where models are not just fitting data but are constrained by first-principles biological laws—bridging the gap between purely data-driven AI and mechanistic science.

> **Status at 99cb2d32 (rows S5-049.xx):** no differentiable physics, molecular dynamics, force field,
> protein folding model, gene regulatory network model or SBML simulator in this module. The one related
> function is `physics_cotraining`: it blends labels with caller-supplied "simulator" target arrays and
> backpropagates the squared error through the small MLP (probe: data_mse 0.260, physics_mse 0.123). Nothing
> calls it, and no simulator is attached. S5-049.01.C01 and S5-049.03.C03 are PARTIAL on that basis only.
Neuro-Pipeline would also introduce “cognitive debugging” interfaces inspired by systems neuroscience. Researchers could perform virtual lesion studies on models—ablating specific neurons, layers, or attention heads—to observe downstream effects on predictions, mirroring experimental neuroscience techniques. Time-resolved activation tracing would allow users to follow how information propagates through the network during inference, akin to tracking neural firing sequences. Coupled with causal inference methods (e.g., do-calculus-inspired interventions), this would enable users to move from correlation-based insights to causal understanding of model behavior—critical for high-stakes biological applications like drug discovery or gene editing.

> **Status at 99cb2d32 (rows S5-050.xx):** `lesion_study` zeroes one hidden unit's output weight at a time
> and reports accuracy drop; there is no layer-ablation or attention-head API (one hidden layer, no
> attention). `activation_trace` is a single forward pass with summary magnitudes, not a time series.
> `causal_intervention` clamps one input feature and compares mean outputs; it is not do-calculus over a
> causal graph. No drug-discovery or gene-editing application exists.
Finally, the system could evolve into a self-optimizing research agent by integrating reinforcement learning loops grounded in experimental feedback. Models deployed in silico (e.g., predicting CRISPR edits or ligand binding) would generate hypotheses that are tested either in simulation or real lab environments; the outcomes—successful edits, failed bindings, unexpected phenotypes—would be fed back into the training loop as reward signals. Over time, this creates a biologically grounded “learning system” that mirrors adaptive intelligence in the brain: continuously refining its internal representations, updating its priors, and improving its predictive accuracy. In this form, Neuro-Pipeline transcends traditional MLOps, becoming a computational neuroscience-driven engine for autonomous biological discovery.

> **Status at 99cb2d32 (rows S5-051.xx):** no reinforcement-learning loop, CRISPR or ligand-binding
> model, or lab connector exists. `feedback_reward_update` is a Beta-Bernoulli count update that is not
> connected to any trainer; `pipeline_report` calls it with hard-coded outcomes `[1,0,1]`. The built-in
> sequence task scores 0.975 train vs 0.562 holdout accuracy (probe, seed 42), and nothing improves it from
> feedback. Not "biologically grounded", "autonomous" or "self-optimizing". S5-051.03.C05 downgraded to OVERSTATED.
