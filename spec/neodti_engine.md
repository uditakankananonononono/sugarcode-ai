> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep
> learning, foundation, GNN, or RL model, whatever the text below says. See
> STATUS.md for what is actually verified.

# NeoDti Engine

NeoDti Engine: A drug-repurposing tool that uses graph neural networks to discover new interactions between existing drugs and disease targets. It builds multiplex graphs from global datasets and validates predictions with molecular docking. NeoDti calculates a "Therapeutic Resilience Index" to rank candidates, enabling the rapid identification of medications.

moved from spec/liquid_biopsy.md L39-44 at commit 8a214135
NeoDti Engine
NeoDti Engine is a large-scale graph-based biomedical reasoning system for discovering novel drug–target and drug–disease interactions through integrative network analysis and molecular validation. It constructs multiplex biomedical graphs where nodes represent drugs, proteins, genes, diseases, and phenotypes, while edges encode biochemical interactions, regulatory relationships, clinical correlations, and literature-derived associations. These graphs integrate heterogeneous data sources including omics databases, clinical trial repositories, and scientific publications.
Graph neural networks embed this heterogeneous biomedical graph into continuous latent spaces that preserve both local molecular interactions and global disease topology. Link prediction tasks are used to infer previously unknown associations by identifying nonlinear interaction patterns within the learned embedding space. Temporal graph updates allow continuous incorporation of new biomedical knowledge, enabling dynamic adaptation of predictions as scientific literature evolves.
Molecular docking simulations serve as a mechanistic validation layer for predicted interactions. Drug molecules are computationally docked against protein targets using energy minimization algorithms that evaluate binding free energy landscapes, conformational flexibility, and solvent interaction effects. This ensures that graph-predicted associations are structurally and biophysically plausible.
A composite scoring system, termed the Therapeutic Resilience Index, evaluates drug candidates based on binding affinity, pathway modulation strength, pharmacokinetic feasibility, toxicity risk, and robustness against resistance mechanisms. This index captures not only efficacy but also long-term therapeutic durability across heterogeneous biological environments.
Finally, NeoDti Engine outputs ranked repurposing candidates with mechanistic explanations and pathway-level intervention maps. It identifies drugs capable of modulating multiple disease-relevant pathways simultaneously, making it particularly powerful for complex diseases, rare conditions, and polygenic disorders.
