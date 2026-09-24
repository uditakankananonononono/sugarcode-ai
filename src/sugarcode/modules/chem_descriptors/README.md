# chem_descriptors - cheminformatics-lite

Pure-Python SMILES parser and molecular descriptors. No RDKit or other
dependency at runtime; RDKit 2024.09.6 was used only offline as the oracle.

```python
from sugarcode.modules.chem_descriptors import druglikeness
r = druglikeness("CC(=O)Oc1ccccc1C(=O)O", logp=1.31)   # aspirin
r["descriptors"]["mol_wt"]   # 180.159
r["descriptors"]["tpsa"]     # 63.6
r["lipinski"]["passes"], r["veber"]["passes"]   # True, True
```

## What it computes
| descriptor | definition (matches) |
|---|---|
| mol_wt / exact_mol_wt | average and monoisotopic mass from the vendored RDKit periodic table (`data/periodic_table.json`); exact mass subtracts electron mass for ions (RDKit `MolWt`/`ExactMolWt`) |
| formula | Hill order; isotope labels fold into the element |
| hbd / hba | RDKit Lipinski `NumHDonors` / `NumHAcceptors` SMARTS definitions |
| nhoh_count / no_count | Lipinski 1997 donor (N-H + O-H hydrogens) / acceptor (N + O) counts |
| rotatable_bonds | RDKit Strict pattern (excludes amide C-N, triple-bond neighbours, CF3/t-Bu-like ends) |
| ring_count, aromatic/aliphatic | minimum cycle basis (Horton), size = cycle rank |
| tpsa | Ertl 2000 fragment table as coded in RDKit MolSurf.cpp; `include_s_and_p=True` adds S/P terms |
| fraction_csp3, heavy/hetero atom count, formal charge | as RDKit |
| lipinski_rule_of_five | MW<=500, donors<=5, acceptors<=10, logP<=5, pass with <=1 violation; no logP model is bundled, so without a supplied logP the check is `Missing` and a 1-violation result is `Undetermined` |
| veber_filter | rotatable bonds <=10 and TPSA <=140 |

## Verification
- 66-molecule ladder (aspirin, caffeine, ibuprofen, statins, antibiotics,
  cyclosporine, heterocycles, cage compounds): every descriptor equals RDKit
  from both RDKit's aromatic SMILES and PubChem's Kekule SMILES; formula equals
  PubChem; MW within PubChem's rounding; neutral exact mass within 1e-4 of PubChem.
- 60-SMILES stress set (charges, isotopes, %nn ring closures, salts, N-oxides,
  azides, stereo marks, Kekule rings): matches RDKit except the 3 documented cases below.
- Hand fixtures: aspirin/caffeine/ibuprofen TPSA summed by hand from the Ertl table.

## Documented differences and unsupported input
- Ring count is the cycle rank; RDKit `RingCount` uses the symmetrized SSSR and
  reports one extra ring for adamantane (4 vs 3) and cubane (6 vs 5).
- Carbon-free formulas are fully alphabetical (Hill); RDKit writes H first (`H4ClN`).
- Isotopic hydrogens ([2H], [3H]) stay explicit atoms, so donor-H counts on
  their neighbours differ from RDKit.
- PubChem TPSA (Cactvs) uses a different fragment set and disagrees with
  Ertl/RDKit on several drugs (e.g. caffeine 58.4 vs 61.82); we follow Ertl/RDKit.
- Stereochemistry (@, @@, /, \) is parsed and ignored (listed in `ignored_features`).
- Aromaticity: lowercase input is trusted; Kekule rings are perceived by 4n+2
  over single rings and fused pairs only (a pair aromatic only as a whole gets
  an aromatic envelope and a non-aromatic fusion bond, as RDKit does for
  azulene). Exocyclic C=O/C=N/C=S give 0 electrons, exocyclic C=C gives 1,
  pyrrolide [N-] gives 2. Aromatic systems needing 3+ fused
  rings as a whole, and B/Se/Te/As donors in Kekule form, are not perceived.
- Not supported (raises `SmilesError`): `*` wildcard, reaction SMILES, SMARTS.
- No logP model. Crippen logP was not vendored.
