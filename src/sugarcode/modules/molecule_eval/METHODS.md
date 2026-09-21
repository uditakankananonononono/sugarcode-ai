# Molecule library evaluation methods

This module evaluates generated libraries without claiming that molecules can be synthesised, are novel in law, bind a target, or are safe.

- Circular fingerprints follow Morgan (1965), DOI `10.1021/c160017a018`, and ECFP, Rogers & Hahn (2010), DOI `10.1021/ci100050t`.
- Internal diversity is mean pairwise `1 - Tanimoto`, with deterministic bounded pair sampling and a bootstrap 95% interval.
- Reference novelty is mean `1 - maximum reference Tanimoto`, also bootstrapped.
- Property distribution shift uses Jensen-Shannon divergence in bits with shared 20-bin histograms and 0.5 pseudocount smoothing. The exact setup is returned because the value depends on binning and samples.
- Multiobjective selection returns the exact nondominated Pareto front without scalarising unlike objectives.

## Missing

Canonical isomeric SMILES, tautomer/salt normalization, SA score, PAINS/structural-alert screening, docking, target activity, ADME/Tox, patent search/freedom-to-operate, synthesis and experimental validation are **Missing**. Graph digests in this module are deduplication aids, not canonical chemistry identifiers.
