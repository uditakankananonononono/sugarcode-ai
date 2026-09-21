# DTI Bench methods and claim boundary

This module implements a target-conditioned proteochemometric baseline. It combines Morgan/ECFP-style ligand features with amino-acid composition, grouped dipeptides, simple physicochemical sequence composition, and explicit ligand-target interaction products. The estimator is ridge regression.

Related published foundations:
- Morgan (1965), DOI `10.1021/c160017a018`; Rogers & Hahn (2010), DOI `10.1021/ci100050t`.
- Lapinsh et al. (2001), proteochemometrics, *Biochim. Biophys. Acta* 1525, 180-190, DOI `10.1016/S0304-4165(00)00172-X`.
- Hoerl & Kennard (1970), ridge regression, DOI `10.1080/00401706.1970.10488634`.
- Pahikkala et al. (2015), careful DTI evaluation settings, *Brief. Bioinform.* 16, 325-337, DOI `10.1093/bib/bbt132`.

Cold-target, cold-drug, chronological and warm random splits are exposed separately. Exact indices and applicability support counts are returned. ChEMBL ingestion keeps only exact-relation pChEMBL data and median-aggregates replicate records per target and canonical SMILES.

## Missing

Sequence alignment/embeddings, 3D structures, protein-family clustering, stereochemical/tautomer standardisation, assay confidence filtering, calibrated uncertainty, nested tuning, external benchmark reproduction, independent external validation and prospective experimental validation are **Missing**. The 0.35 ligand and 0.30 positional-identity applicability thresholds are declared operating heuristics, not universal published cutoffs.
