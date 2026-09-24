"""Regenerates part of tests/fixtures/chem_descriptors_oracle.json. Needs RDKit
(pip install rdkit==2024.9.6) and, for the ladder, network access to PubChem.
Not used at runtime; the repo does not depend on RDKit."""
import json, sys
from rdkit import Chem
from rdkit.Chem import Descriptors as D, rdMolDescriptors as R, Lipinski
import pathlib; sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))
from sugarcode.modules.chem_descriptors import compute_descriptors
S = ["C[N+](C)(C)C","[NH4+].[Cl-]","CC(=O)[O-].[Na+]","c1cc[nH]c1","[13CH4]","[2H]O[2H]","OC(=O)C(N)Cc1ccc(O)cc1",
"C1CC2CCC1CC2","C%10CCCCC%10","O=[N+]([O-])c1ccccc1","CS(=O)(=O)N","OP(=O)(O)O","N#Cc1ccccc1","C=CC=C",
"c1ccc2ccccc2c1","c1ccc2c(c1)[nH]c1ccccc12","O=C1NC(=O)C(=O)N1","CC(C)(C)OC(=O)N","NC(=N)N","CN1CCN(C)CC1",
"C1=CC=CC=C1","OC1=CC=CC=C1","n1ccncc1","c1ncc[nH]1","s1cccc1","o1cccc1","FC(F)(F)c1ccccc1","ClC(Cl)Cl","BrCCBr",
"[O-][n+]1ccccc1","C[S+](C)[O-]","CC#N","C1CCOC1","O=C=O","[Fe+2]","[H][H]","C/C=C/C","F/C=C\\F","N[C@@H](C)C(=O)O",
"CC(=O)Nc1ccc(O)cc1","c1ccccc1-c1ccccc1","C(C(=O)O)c1ccccc1","CCOC(=O)CC","NC(=O)c1ccccc1","CC1=CC(=O)C=CC1=O",
"C1CC1C1CC1","C12CCC(CC1)CC2","O=S(=O)(O)O","[Se]","CN=C=O","N=[N+]=[N-]","CCN(CC)CC","OCC(O)CO","C1CCC2(CC1)CCCC2",
"Oc1ccc2ccccc2c1","c1ccc(cc1)C(c1ccccc1)(c1ccccc1)O","CC(C)Cc1ccc(cc1)C(C)C(=O)O","[nH]1cccc1","C1=CNC=C1","O=c1cc[nH]cc1"]
keys = [("mol_wt","mol_wt",D.MolWt),("exact_mol_wt","exact_mol_wt",D.ExactMolWt),("hbd","hbd",Lipinski.NumHDonors),
("hba","hba",Lipinski.NumHAcceptors),("nhoh","nhoh_count",Lipinski.NHOHCount),("no","no_count",Lipinski.NOCount),
("rot","rotatable_bonds",lambda m:R.CalcNumRotatableBonds(m,R.NumRotatableBondsOptions.Strict)),("tpsa","tpsa",D.TPSA),
("ring","ring_count",lambda m: len(Chem.GetSSSR(m))),("arom","aromatic_ring_count",D.NumAromaticRings),
("formula","formula",R.CalcMolFormula),("heavy","heavy_atom_count",D.HeavyAtomCount),("charge","formal_charge",Chem.GetFormalCharge),
("hetero","heteroatom_count",D.NumHeteroatoms),("fsp3","fraction_csp3",D.FractionCSP3)]
bad=0; rows=[]
for s in S:
    m = Chem.MolFromSmiles(s)
    if m is None: print("rdkit fail", s); continue
    try: mine = compute_descriptors(s)
    except Exception as e: print("ERR", s, e); bad+=1; continue
    rec={"smiles":s}
    for n,mk,f in keys:
        a=f(m); b=mine[mk]; rec[mk]=a
        ok = abs(a-b)<1e-3 if isinstance(a,float) else a==b
        if not ok: print("DIFF",s,n,"rdkit",a,"mine",b); bad+=1
    rows.append(rec)
json.dump(rows, open("stress.json","w"), indent=1)
print("bad",bad,"of",len(S))
