"""Regenerates part of tests/fixtures/chem_descriptors_oracle.json. Needs RDKit
(pip install rdkit==2024.9.6) and, for the ladder, network access to PubChem.
Not used at runtime; the repo does not depend on RDKit."""
import json, time, urllib.request, urllib.parse, sys
from rdkit import Chem, rdBase
from rdkit.Chem import Descriptors as D, rdMolDescriptors as R, Lipinski
NAMES = ["aspirin","caffeine","ibuprofen","acetaminophen","naproxen","diclofenac","metformin",
 "atorvastatin","simvastatin","omeprazole","lisinopril","losartan","amlodipine","metoprolol",
 "propranolol","warfarin","clopidogrel","sildenafil","fluoxetine","sertraline","diazepam",
 "morphine","codeine","nicotine","benzylpenicillin","amoxicillin","ciprofloxacin","doxycycline",
 "azithromycin","erythromycin","cyclosporine","imatinib","gefitinib","tamoxifen","methotrexate",
 "levothyroxine","furosemide","hydrochlorothiazide","captopril","ranitidine","dapsone",
 "chloroquine","oseltamivir","sofosbuvir","acetylcholine","celecoxib","efavirenz","zidovudine",
 "glycine","benzene","ethanol","cyclopropane","adamantane","cubane","nitrobenzene","acetonitrile",
 "pyridine","pyrrole","thiophene","furan","indole","trifluoroacetic acid","tert-butanol",
 "dimethyl sulfoxide","triphenylphosphine","sodium acetate"]
props = "SMILES,MolecularWeight,ExactMass,TPSA,XLogP,MolecularFormula"
out = []
for name in NAMES:
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/%s/property/%s/JSON" % (urllib.parse.quote(name), props)
    import os
    os.makedirs("cache", exist_ok=True)
    cf = "cache/" + name.replace(" ","_") + ".json"
    if os.path.exists(cf):
        p = json.load(open(cf))
    else:
        for attempt in range(4):
            try:
                with urllib.request.urlopen(url, timeout=20) as r:
                    p = json.load(r)["PropertyTable"]["Properties"][0]
                break
            except Exception as e:
                print(name, "retry", e, file=sys.stderr); time.sleep(2)
        else:
            print("SKIP", name, file=sys.stderr); continue
        json.dump(p, open(cf,"w")); time.sleep(0.3)
    m = Chem.MolFromSmiles(p["SMILES"])
    can = Chem.MolToSmiles(m, isomericSmiles=True)
    m2 = Chem.MolFromSmiles(can)
    rec = {"name": name, "pubchem_cid": p["CID"], "pubchem_smiles": p["SMILES"], "smiles": can,
           "pubchem": {"formula": p.get("MolecularFormula"), "mol_wt": float(p["MolecularWeight"]),
                       "exact_mass": float(p["ExactMass"]), "tpsa": p.get("TPSA"), "xlogp": p.get("XLogP")},
           "rdkit": {"formula": R.CalcMolFormula(m2), "mol_wt": D.MolWt(m2), "exact_mol_wt": D.ExactMolWt(m2),
                     "heavy_atom_count": D.HeavyAtomCount(m2), "hbd": Lipinski.NumHDonors(m2),
                     "hba": Lipinski.NumHAcceptors(m2), "nhoh_count": Lipinski.NHOHCount(m2),
                     "no_count": Lipinski.NOCount(m2),
                     "rotatable_bonds": D.NumRotatableBonds(m2),
                     "rotatable_bonds_strict": R.CalcNumRotatableBonds(m2, R.NumRotatableBondsOptions.Strict),
                     "tpsa": D.TPSA(m2), "tpsa_sp": R.CalcTPSA(m2, includeSandP=True),
                     "ring_count": D.RingCount(m2), "aromatic_ring_count": D.NumAromaticRings(m2),
                     "aliphatic_ring_count": D.NumAliphaticRings(m2),
                     "fraction_csp3": D.FractionCSP3(m2), "formal_charge": Chem.GetFormalCharge(m2),
                     "heteroatom_count": D.NumHeteroatoms(m2), "crippen_logp": D.MolLogP(m2)}}
    out.append(rec)
json.dump({"generated": "2026-09-24", "rdkit_version": rdBase.rdkitVersion,
           "pubchem_endpoint": "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name/<name>/property/" + props + "/JSON",
           "molecules": out}, sys.stdout, indent=1)
