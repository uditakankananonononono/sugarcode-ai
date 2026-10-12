> **Current claim-local scope at 7ff2dc87:** the correction section below supersedes the original aspirational wording for its named row IDs only. The original text is retained for traceability, not as a shipped-capability claim. Existing corrections for other rows remain in force.

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


## Claim-local wording corrections at 7ff2dc87

Pinned implementation: `src/sugarcode/modules/neuro_pipeline/core.py` at `7ff2dc8748965fcfc55f6ffd3a2efcab4e592368`. These are wording corrections only. They do not implement missing capabilities, establish biological validation, or change runtime behavior.

### Pin-scoped S5-047.01.C01

Original claim (historical): "closed-loop"

Current wording: MLP training, lesions, modality projections and continual_update are callable helpers. pipeline_report invokes a fixed sequence once; no recurring feedback-to-training orchestration exists.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:41 (train); src/sugarcode/modules/neuro_pipeline/core.py:246 (train_on_sequences); src/sugarcode/modules/neuro_pipeline/core.py:378 (pipeline_report); src/sugarcode/modules/neuro_pipeline/core.py:350 (continual_update)`.

### Pin-scoped S5-047.01.C02

Original claim (historical): "neuro-symbolic MLOps system"

Current wording: NumPy two-layer MLP, sequence encoders, numeric analysis and spiking simulation exist. No symbolic rule engine, production MLOps registry/deployment or neuro-symbolic integration is provided.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:5 (MLP); src/sugarcode/modules/neuro_pipeline/core.py:246 (train_on_sequences); src/sugarcode/modules/neuro_pipeline/core.py:378 (pipeline_report)`.

### Pin-scoped S5-047.01.C03

Original claim (historical): "biological deep learning models"

Current wording: Model is a two-layer tanh/sigmoid MLP trained on synthetic toy or caller-supplied DNA labels. Biological authenticity/generalization is not established by its architecture.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:5 (MLP); src/sugarcode/modules/neuro_pipeline/core.py:203 (synthetic_promoter_dataset); src/sugarcode/modules/neuro_pipeline/core.py:246 (train_on_sequences)`.

### Pin-scoped S5-047.01.C04

Original claim (historical): "cutting-edge computational neuroscience"

Current wording: Implementation includes simple MLP/lesion/RSA/SVD/LIF-style helpers, without an independent current neuroscience benchmark or validated biological comparison.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:5 (MLP); src/sugarcode/modules/neuro_pipeline/core.py:68 (lesion_study); src/sugarcode/modules/neuro_pipeline/core.py:112 (rsa); src/sugarcode/modules/neuro_pipeline/core.py:326 (align_modalities); src/sugarcode/modules/neuro_pipeline/core.py:337 (spiking_dynamics)`.

### Pin-scoped S5-047.02.C03

Original claim (historical): "predictive coding frameworks"

Current wording: predictive_coding iteratively moves a zero state toward the mean of supplied observations. It has no hierarchy, generative dynamics or future predictive task.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:343 (predictive_coding)`.

### Pin-scoped S5-047.03.C05

Original claim (historical): "without catastrophic forgetting"

Current wording: continual_update pulls W1/W2 toward previous weights without Fisher information; biases are not anchored and no old-task retention guarantee is checked.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:350 (continual_update)`.

### Pin-scoped S5-048.01

Original claim (historical): "A defining feature would be its ability to map internal model representations to interpretable neurobiological analogues."

Current wording: rsa compares input/hidden Euclidean dissimilarities, align_modalities projects each modality separately, and connectivity uses model weights. No brain correspondence dataset or neurobiological interpretation is validated.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:112 (rsa); src/sugarcode/modules/neuro_pipeline/core.py:326 (align_modalities); src/sugarcode/modules/neuro_pipeline/core.py:360 (functional_connectivity)`.

### Pin-scoped S5-048.02.C03

Original claim (historical): "connectomics in the brain"

Current wording: functional_connectivity thresholds products of W1 and W2 magnitudes into input-to-hidden edges. It does not ingest brain connectivity measurements.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:360 (functional_connectivity)`.

### Pin-scoped S5-048.03.C02

Original claim (historical): "manifold alignment"

Current wording: rsa correlates upper triangles of input and hidden Euclidean-distance matrices. It does not learn an alignment transformation or pair manifolds.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:112 (rsa)`.

### Pin-scoped S5-048.04

Original claim (historical): "This would push explainability from visualization into mechanistic insight."

Current wording: RSA geometry correlation, feature clamping and lesion accuracy drops describe numerical model sensitivity. They do not establish a biological mechanism or validated mechanistic explanation.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:112 (rsa); src/sugarcode/modules/neuro_pipeline/core.py:68 (lesion_study); src/sugarcode/modules/neuro_pipeline/core.py:367 (causal_intervention)`.

### Pin-scoped S5-050.03.C01

Original claim (historical): "Time-resolved"

Current wording: activation_trace records magnitudes from one feedforward pass; lesion_study reports accuracy deltas and causal_intervention reports output changes. These functions have no temporal trajectory.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:99 (activation_trace); src/sugarcode/modules/neuro_pipeline/core.py:68 (lesion_study); src/sugarcode/modules/neuro_pipeline/core.py:367 (causal_intervention)`.

### Pin-scoped S5-050.03.C04

Original claim (historical): "neural firing sequences"

Current wording: The cited activation trace contains layer magnitudes, not neural spike sequences. Separate spiking_dynamics simulates threshold/decay voltage and spikes but is not wired to MLP inference.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:99 (activation_trace); src/sugarcode/modules/neuro_pipeline/core.py:337 (spiking_dynamics)`.

### Pin-scoped S5-050.04.C02

Original claim (historical): "do-calculus-inspired interventions"

Current wording: causal_intervention replaces one input column with a constant and forwards the MLP. It has no structural causal model, confounding graph or do-calculus identification.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:367 (causal_intervention)`.

### Pin-scoped S5-050.04.C03

Original claim (historical): "causal understanding of model behavior"

Current wording: The reported average_causal_effect is mean prediction change after feature clamping. It is a model sensitivity result, not causally identified biological or observational effect.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:367 (causal_intervention)`.

### Pin-scoped S5-051.01.C01

Original claim (historical): "self-optimizing research agent"

Current wording: feedback_reward_update returns Beta count statistics for supplied outcomes; it never updates model weights, chooses experiments or controls an autonomous loop.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:375 (feedback_reward_update); src/sugarcode/modules/neuro_pipeline/core.py:378 (pipeline_report)`.

### Pin-scoped S5-051.03.C01

Original claim (historical): "biologically grounded"

Current wording: Reward update is generic count arithmetic with no biological variables, external evidence or learned biological mechanism.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:375 (feedback_reward_update)`.

### Pin-scoped S5-051.03.C02

Original claim (historical): "adaptive intelligence in the brain"

Current wording: Beta update does not model brain circuits, plasticity mechanisms or adaptive cognition. No trained adaptive biological intelligence is produced.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:375 (feedback_reward_update)`.

### Pin-scoped S5-051.03.C05

Original claim (historical): "predictive accuracy"

Current wording: Reward helper returns reward mean/standard deviation; pipeline_report does not apply these values to its trained MLP or evaluate an accuracy improvement.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:375 (feedback_reward_update); src/sugarcode/modules/neuro_pipeline/core.py:378 (pipeline_report)`.

### Pin-scoped S5-051.04.C01

Original claim (historical): "computational neuroscience-driven"

Current wording: Cited reward function is a generic Beta update; neuroscience-inspired helpers elsewhere do not turn this update into a neuroscience-driven autonomous research system.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:375 (feedback_reward_update); src/sugarcode/modules/neuro_pipeline/core.py:378 (pipeline_report)`.

### Pin-scoped S5-051.04.C02

Original claim (historical): "autonomous biological discovery"

Current wording: No autonomous experiment selection, lab execution, biological discovery validation or publication-feedback runtime is implemented.

Source: `src/sugarcode/modules/neuro_pipeline/core.py:378 (pipeline_report); src/sugarcode/modules/neuro_pipeline/core.py:375 (feedback_reward_update)`.
