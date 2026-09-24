"""chem_descriptors: SMILES parser + descriptors, oracle-tested without RDKit at test time.

The fixture tests/fixtures/chem_descriptors_oracle.json holds values computed by
RDKit 2024.09.6 and fetched from PubChem PUG-REST (scripts/chem_descriptors_oracle_*.py
regenerate it). Every ladder drug is checked twice: from RDKit's aromatic canonical
SMILES and from PubChem's Kekule SMILES (exercising aromaticity perception).
"""
import json
from pathlib import Path

import pytest

from sugarcode.modules.chem_descriptors import (SmilesError, compute_descriptors, druglikeness,
                                                lipinski_rule_of_five, parse_smiles, tpsa,
                                                veber_filter)

FX = json.loads((Path(__file__).parent / "fixtures" / "chem_descriptors_oracle.json").read_text())
LADDER = FX["ladder"]
KEYS = {"mol_wt": "mol_wt", "exact_mol_wt": "exact_mol_wt", "hbd": "hbd", "hba": "hba",
        "nhoh_count": "nhoh_count", "no_count": "no_count",
        "rotatable_bonds_strict": "rotatable_bonds", "tpsa": "tpsa",
        "aromatic_ring_count": "aromatic_ring_count", "heavy_atom_count": "heavy_atom_count",
        "fraction_csp3": "fraction_csp3", "formal_charge": "formal_charge",
        "heteroatom_count": "heteroatom_count"}
# RDKit RingCount uses the symmetrized SSSR; ours is the cycle rank (true SSSR size).
SYMM_SSSR_EXTRA = {"adamantane": 1, "cubane": 1}


def _eq(a, b):
    return abs(a - b) < 1e-6 if isinstance(a, float) else a == b


@pytest.mark.parametrize("which", ["smiles", "pubchem_smiles"])
def test_ladder_matches_rdkit(which):
    assert len(LADDER) == 66
    bad = []
    for m in LADDER:
        d = compute_descriptors(m[which])
        for rk, mk in KEYS.items():
            if not _eq(m["rdkit"][rk], d[mk]):
                bad.append((m["name"], mk, m["rdkit"][rk], d[mk]))
        assert d["ring_count"] + SYMM_SSSR_EXTRA.get(m["name"], 0) == m["rdkit"]["ring_count"], m["name"]
        assert d["formula"] == m["rdkit"]["formula"] == m["pubchem"]["formula"], m["name"]
        assert abs(tpsa(parse_smiles(m[which]), include_s_and_p=True) - m["rdkit"]["tpsa_sp"]) < 1e-6
    assert bad == []


def test_ladder_matches_pubchem_mass():
    for m in LADDER:
        d = compute_descriptors(m["pubchem_smiles"])
        assert abs(d["mol_wt"] - m["pubchem"]["mol_wt"]) <= 0.06, m["name"]   # PubChem rounds; Cl 35.45 vs 35.453
        if d["formal_charge"] == 0:
            assert abs(d["exact_mol_wt"] - m["pubchem"]["exact_mass"]) < 1e-4, m["name"]
    # PubChem does not subtract electron mass for ions; RDKit and we do.
    ach = next(m for m in LADDER if m["name"] == "acetylcholine")
    d = compute_descriptors(ach["pubchem_smiles"])
    assert abs(d["exact_mol_wt"] + 0.00054857991 - ach["pubchem"]["exact_mass"]) < 1e-6


def test_stress_set_matches_rdkit_with_documented_divergences():
    known = {("[NH4+].[Cl-]", "formula"),            # strict Hill (no C: alphabetical incl. H)
             ("[2H]O[2H]", "hba"), ("[2H]O[2H]", "nhoh_count")}  # D kept as explicit atoms
    bad = []
    for row in FX["stress"]:
        d = compute_descriptors(row["smiles"])
        for k, v in row.items():
            if k != "smiles" and not _eq(v, d[k]) and (row["smiles"], k) not in known:
                bad.append((row["smiles"], k, v, d[k]))
    assert len(FX["stress"]) == 60 and bad == []


def test_hand_fixtures_aspirin_caffeine_ibuprofen():
    # PubChem CID 2244 / 2519 / 3672; TPSA per Ertl 2000 fragment table.
    a = compute_descriptors("CC(=O)OC1=CC=CC=C1C(=O)O")
    assert a["formula"] == "C9H8O4" and round(a["mol_wt"], 2) == 180.16
    assert a["exact_mol_wt"] == pytest.approx(180.04225873, abs=1e-7)
    # 2 carbonyl O (17.07 each) + ester O (9.23) + OH (20.23) = 63.60
    assert a["tpsa"] == pytest.approx(2 * 17.07 + 9.23 + 20.23)
    assert (a["hbd"], a["nhoh_count"], a["no_count"], a["aromatic_ring_count"]) == (1, 1, 4, 1)
    c = compute_descriptors("CN1C=NC2=C1C(=O)N(C(=O)N2C)C")
    assert c["formula"] == "C8H10N4O2" and round(c["mol_wt"], 2) == 194.19
    assert c["aromatic_ring_count"] == 2 and c["hbd"] == 0
    # 3 methylated aromatic n(-C)(:):  4.93 each, 1 pyridine-type :n: 12.89, 2 C=O 17.07 each
    assert c["tpsa"] == pytest.approx(3 * 4.93 + 12.89 + 2 * 17.07)
    i = compute_descriptors("CC(C)CC1=CC=C(C=C1)C(C)C(=O)O")
    assert i["formula"] == "C13H18O2" and round(i["mol_wt"], 2) == 206.28
    assert i["tpsa"] == pytest.approx(37.30) and i["rotatable_bonds"] == 4


def test_parser_features_and_errors():
    m = parse_smiles("C%10CCCCC%10.[Na+]")
    assert len(m.atoms) == 7 and sum(a.charge for a in m.atoms) == 1
    m = parse_smiles("N[C@@H](C)C(=O)O")
    assert m.ignored and compute_descriptors("N[C@@H](C)C(=O)O")["formula"] == "C3H7NO2"
    assert compute_descriptors("F/C=C\\F")["formula"] == "C2H2F2"
    assert compute_descriptors("[13CH4]")["mol_wt"] == pytest.approx(17.035, abs=1e-3)
    for bad in ["", "C1CC", "C(C", "C)C", "*C", "CC>>CC", "[Xx]", "C==C"]:
        with pytest.raises(SmilesError):
            parse_smiles(bad)


def test_kekule_aromaticity_perception():
    for s, n in [("C1=CC=CC=C1", 1), ("C1=CNC=C1", 1), ("O=C1C=CNC=C1", 1),
                 ("C1=CC2=CC=CC=CC2=C1", 2),          # azulene: aromatic only as a fused pair
                 ("C1=CC=CC=CC=C1", 0),               # cyclooctatetraene, 8 pi
                 ("CC1=CC(=O)C=CC1=O", 0),            # quinone
                 ("C1C=CC=C1", 0)]:                    # cyclopentadiene, sp3 CH2
        assert compute_descriptors(s)["aromatic_ring_count"] == n, s


def test_lipinski_and_veber():
    asp = druglikeness("CC(=O)Oc1ccccc1C(=O)O", logp=1.31)
    assert asp["lipinski"]["passes"] is True and asp["lipinski"]["complete"]
    assert asp["veber"]["passes"] is True
    cyc = next(m for m in LADDER if m["name"] == "cyclosporine")
    d = compute_descriptors(cyc["smiles"])
    lip = lipinski_rule_of_five(d, logp=cyc["rdkit"]["crippen_logp"])
    assert lip["passes"] is False and "mol_wt_le_500" in lip["violations"]
    v = veber_filter(d)
    assert v["passes"] is False and not v["checks"]["tpsa_le_140"]
    # one violation + unknown logP cannot be decided
    one = {"mol_wt": 600.0, "nhoh_count": 1, "no_count": 2}
    assert lipinski_rule_of_five(one)["passes"] == "Undetermined"
    assert lipinski_rule_of_five({"mol_wt": 300.0, "nhoh_count": 1, "no_count": 2})["passes"] is True
