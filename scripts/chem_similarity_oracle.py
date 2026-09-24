"""Regenerates tests/fixtures/chem_similarity_oracle.json. Needs RDKit
(pip install rdkit==2024.9.6) and network access to PubChem. Not used at
runtime; the repo does not depend on RDKit."""
import json, sys, urllib.request, urllib.parse
from rdkit import Chem, DataStructs, RDLogger, rdBase
from rdkit.Chem import AllChem, Descriptors as D, rdMolDescriptors as R, Lipinski
RDLogger.DisableLog("rdApp.*")
CIDS = list(range(1, 401))
req = urllib.request.Request("https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/property/SMILES/JSON",
                             data=urllib.parse.urlencode({"cid": ",".join(map(str, CIDS))}).encode())
props = json.load(urllib.request.urlopen(req, timeout=60))["PropertyTable"]["Properties"]
mols = []
for p in props:
    m = Chem.MolFromSmiles(p["SMILES"])
    rec = {"cid": p["CID"], "smiles": p["SMILES"],
           "morgan_counts": {str(r): {str(k): v for k, v in AllChem.GetMorganFingerprint(m, r).GetNonzeroElements().items()} for r in (1, 2, 3)},
           "morgan2_bits_2048": sorted(AllChem.GetMorganFingerprintAsBitVect(m, 2, 2048).GetOnBits()),
           "descriptors": {"mol_wt": D.MolWt(m), "exact_mol_wt": D.ExactMolWt(m), "hbd": Lipinski.NumHDonors(m),
                           "hba": Lipinski.NumHAcceptors(m), "tpsa": D.TPSA(m),
                           "rotatable_bonds": R.CalcNumRotatableBonds(m, R.NumRotatableBondsOptions.Strict),
                           "aromatic_ring_count": D.NumAromaticRings(m), "ring_count": len(Chem.GetSSSR(m)),
                           "fraction_csp3": D.FractionCSP3(m), "formula": R.CalcMolFormula(m)}}
    mols.append(rec)
bits = [AllChem.GetMorganFingerprintAsBitVect(Chem.MolFromSmiles(r["smiles"]), 2, 2048) for r in mols]
cnts = [AllChem.GetMorganFingerprint(Chem.MolFromSmiles(r["smiles"]), 2) for r in mols]
queries = []
for qi in [0, 9, 49, 99, 149, 199, 249, 299, 349, 399]:
    tb = DataStructs.BulkTanimotoSimilarity(bits[qi], bits)
    tc = DataStructs.BulkTanimotoSimilarity(cnts[qi], cnts)
    db = DataStructs.BulkDiceSimilarity(bits[qi], bits)
    queries.append({"query_index": qi, "tanimoto_bits": tb, "tanimoto_counts": tc, "dice_bits": db})
json.dump({"description": "RDKit " + rdBase.rdkitVersion + " Morgan fingerprints (legacy GetMorganFingerprint / AsBitVect, "
           "useChirality=False, useBondTypes=True, includeRedundantEnvironments=False), BulkTanimoto/BulkDice, and descriptors "
           "for PubChem CIDs 1-400 (SMILES from PUG-REST, fetched 2026-09-24).",
           "rdkit_version": rdBase.rdkitVersion, "molecules": mols, "queries": queries}, sys.stdout, separators=(",", ":"))
