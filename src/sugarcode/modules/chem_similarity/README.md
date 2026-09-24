# chem_similarity - Morgan fingerprints and similarity search

Pure Python, built on the chem_descriptors SMILES parser. No RDKit at runtime;
RDKit 2024.09.6 was the offline oracle.

```python
from sugarcode.modules.chem_similarity import morgan_counts, morgan_bits, tanimoto, nearest_neighbors
morgan_counts("CC")                      # {2246728737: 2, 3545175291: 1}  (same codes as RDKit)
tanimoto(morgan_bits("CCO"), morgan_bits("CCN"))
nearest_neighbors("CC(=O)Oc1ccccc1C(=O)O", library_smiles, k=5)
```

## What it computes
- `morgan_counts(smiles, radius)`: unfolded count fingerprint, 32-bit codes,
  identical to RDKit `GetMorganFingerprint(m, radius)` (ECFP invariants,
  bond types on, chirality off, redundant environments dropped).
- `morgan_bits(smiles, radius, n_bits)`: folded on-bits (code % n_bits),
  identical to `GetMorganFingerprintAsBitVect`. ECFP4 = radius 2.
- `morgan_bit_info`: bit -> [(atom, radius)].
- `tanimoto` (= `jaccard`) and `dice` on bit sets or count dicts (RDKit
  definitions; two empty fingerprints give 0.0).
- `nearest_neighbors`: top-k over a SMILES list with threshold, deterministic
  tie-break by library order, unparsable SMILES reported, not dropped silently.
- `similarity_matrix`.

## Verification
- PubChem CIDs 1-400: counts at radius 1, 2, 3 and 2048-bit ECFP4 bits equal
  RDKit exactly for all 400; the same molecules also check chem_descriptors.
- Bulk Tanimoto (bits and counts) and Dice for 10 queries x 400 equal RDKit's
  BulkTanimotoSimilarity/BulkDiceSimilarity to 1e-12; NN ranking matches.
- Hand-hashed methane/ethane codes with an independent hash_combine in the tests.

## Limits
- No FCFP (feature invariants), no chirality option, no path-based (RDKit
  topological) or MACCS fingerprints.
- Identical codes to RDKit depend on identical aromaticity; see
  chem_descriptors README for the aromaticity cases not perceived.
- Search is a linear scan (fine for thousands, not millions).
