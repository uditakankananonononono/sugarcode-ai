> **Spec vs implementation:** this file is the original aspirational product-spec
> text. The shipped module is deterministic/statistical/mechanistic computation
> (PWMs, ODEs, published vendored models, heuristics) - NOT a trained deep
> learning, foundation, GNN, or RL model, whatever the text below says. See
> STATUS.md for what is actually verified.

# NeoHunter

NeoHunter: An identification engine for personalized neoantigens derived from tumor mutational data. It ranks peptide candidates by immunogenicity and predicts binding to specific patient HLA alleles. NeoHunter enables the design of personalized cancer vaccines that target the unique mutations of an individual's tumor, providing a high-precision approach.





NeoHunter
NeoHunter is a computational immunogenomics platform for the identification, ranking, and optimization of tumor-specific neoantigens for personalized cancer immunotherapy. The system begins with tumor sequencing data processing, identifying somatic mutations including single nucleotide variants, insertions, deletions, and gene fusion events. These mutations are translated into candidate peptide sequences using transcript reconstruction algorithms and proteasomal cleavage prediction models that simulate antigen processing pathways.
Peptide–MHC binding prediction is performed using a hybrid approach combining structural docking simulations and deep learning models trained on immunopeptidomics datasets. Binding affinities are computed across patient-specific HLA alleles, enabling personalized antigen presentation mapping. This generates a high-dimensional binding affinity matrix representing potential immune visibility of each mutated peptide.
Immunogenicity scoring integrates multiple biological determinants including proteasomal processing probability, TAP transport efficiency, MHC stability, peptide surface accessibility, and predicted T-cell receptor recognition likelihood. These features are combined into a probabilistic scoring framework that ranks neoantigens based on their likelihood of eliciting strong immune responses.
Tumor evolution under immune pressure is modeled using stochastic branching processes and clonal selection dynamics. This allows simulation of antigen loss variants, immune escape mutations, and heterogeneous tumor subclonal architecture over time. The system predicts how tumors evolve in response to immune targeting, enabling proactive vaccine design that anticipates escape pathways.
Finally, a multi-objective optimization engine selects neoantigen panels that maximize tumor coverage, minimize immune evasion probability, and maximize breadth of T-cell activation. The output is a ranked vaccine design optimized for durability, specificity, and population of reactive T-cell clones, enabling fully personalized cancer vaccine generation from raw tumor genomic data.
