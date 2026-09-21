# QSAR Bench methods and claim boundary

This module supplies a reproducible baseline, not a claim that a molecule is safe, effective, or clinically useful.

- Circular features follow the Morgan connectivity update and ECFP design: Morgan (1965), *J. Chem. Doc.* 5, 107-113, DOI `10.1021/c160017a018`; Rogers & Hahn (2010), *J. Chem. Inf. Model.* 50, 742-754, DOI `10.1021/ci100050t`.
- Ridge regression follows Hoerl & Kennard (1970), *Technometrics* 12, 55-67, DOI `10.1080/00401706.1970.10488634`.
- The applicability-domain report uses nearest-training Tanimoto similarity. The 0.35 cutoff is a declared operational heuristic, not a universal published threshold.
- ChEMBL data come from the public REST API. Exact-relation pChEMBL measurements are median-aggregated by canonical SMILES. Exclusion counts are returned.
- Random splits are available for diagnostics. Scaffold-like grouped and chronological splits are preferable for less optimistic estimates. The dependency-light scaffold signature is not a Bemis-Murcko implementation.

## Missing

Stereochemical and tautomer standardisation, salt stripping, assay-confidence policy, uncertainty calibration, Y-randomisation, nested hyperparameter tuning, a true Bemis-Murcko split, independent external validation, and prospective experimental validation are **Missing**. Performance belongs only to the dataset and split returned by the call.
