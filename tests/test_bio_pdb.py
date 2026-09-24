"""PDB/mmCIF toolkit: fixed-column parse, CIF loop parse, queries, contacts."""
import pytest

from sugarcode.bio.pdb import (parse_pdb, write_pdb, parse_mmcif, chains,
                               residues, select, coordinates, centroid,
                               distance, contacts, stats)


def _atom(serial, name, resname, chain, resseq, x, y, z, element,
          record="ATOM", occ=1.00, bf=10.00):
    return (f"{record:<6}{serial:5d} {name:^4} {resname:>3} {chain}"
            f"{resseq:4d}    {x:8.3f}{y:8.3f}{z:8.3f}{occ:6.2f}{bf:6.2f}"
            f"          {element:>2}  ")


PDB = "\n".join([
    "HEADER    TEST STRUCTURE                          01-JAN-00   9XYZ",
    "TITLE     TOY PEPTIDE",
    _atom(1, "N", "ALA", "A", 1, 0.0, 0.0, 0.0, "N"),
    _atom(2, "CA", "ALA", "A", 1, 1.5, 0.0, 0.0, "C"),
    _atom(3, "C", "ALA", "A", 1, 2.0, 1.4, 0.0, "C"),
    _atom(4, "N", "GLY", "A", 2, 3.3, 1.8, 0.0, "N"),
    _atom(5, "CA", "GLY", "A", 2, 3.8, 3.1, 0.0, "C"),
    _atom(6, "O1", "HOH", "B", 1, 3.9, 3.2, 0.3, "O", record="HETATM"),
    "TER", "END"]) + "\n"

MMCIF = """data_test
#
_entry.id test
#
loop_
_atom_site.group_PDB
_atom_site.id
_atom_site.type_symbol
_atom_site.label_atom_id
_atom_site.label_alt_id
_atom_site.label_comp_id
_atom_site.label_asym_id
_atom_site.label_seq_id
_atom_site.pdbx_PDB_ins_code
_atom_site.Cartn_x
_atom_site.Cartn_y
_atom_site.Cartn_z
_atom_site.occupancy
_atom_site.B_iso_or_equiv
_atom_site.auth_seq_id
_atom_site.auth_asym_id
_atom_site.pdbx_PDB_model_num
ATOM 1 N N . ALA A 1 ? 0.0 0.0 0.0 1.00 10.00 1 A 1
ATOM 2 C CA . ALA A 1 ? 1.5 0.0 0.0 1.00 10.00 1 A 1
HETATM 3 O O1 . HOH B . ? 3.9 3.2 0.3 1.00 10.00 1 B 1
#
"""


def test_pdb_fixed_columns_and_header():
    s = parse_pdb(PDB)
    assert s["header"]["id"] == "9XYZ"
    assert s["header"]["classification"] == "TEST STRUCTURE"
    assert s["header"]["title"] == "TOY PEPTIDE"
    assert len(s["atoms"]) == 6
    a = s["atoms"][1]
    assert a == {"serial": 2, "name": "CA", "altloc": None, "resname": "ALA",
                 "chain": "A", "resseq": 1, "icode": None, "x": 1.5, "y": 0.0,
                 "z": 0.0, "occupancy": 1.0, "bfactor": 10.0, "element": "C",
                 "record": "ATOM", "model": 1}
    assert s["atoms"][5]["record"] == "HETATM"
    with pytest.raises(ValueError, match="no ATOM"):
        parse_pdb("HEADER    X\nEND\n")


def test_pdb_multimodel():
    text = ("MODEL        1\n" + _atom(1, "CA", "ALA", "A", 1, 0, 0, 0, "C")
            + "\nENDMDL\nMODEL        2\n"
            + _atom(2, "CA", "ALA", "A", 1, 9, 9, 9, "C") + "\nENDMDL\nEND\n")
    s = parse_pdb(text)
    assert [a["model"] for a in s["atoms"]] == [1, 2]
    assert [a["serial"] for a in select(s)] == [1]          # default model 1
    assert [a["serial"] for a in select(s, model=None)] == [1, 2]
    assert stats(s)["models"] == 2


def test_pdb_roundtrip():
    s = parse_pdb(PDB)
    assert parse_pdb(write_pdb(s))["atoms"] == s["atoms"]


def test_mmcif_atom_site_loop():
    s = parse_mmcif(MMCIF)
    assert len(s["atoms"]) == 3
    w = s["atoms"][2]
    assert w["record"] == "HETATM" and w["resname"] == "HOH"
    assert w["resseq"] == 1 and w["chain"] == "B"           # auth fallback
    assert s["atoms"][0]["altloc"] is None                  # '.' -> None
    assert s["atoms"][0]["icode"] is None                   # '?' -> None
    with pytest.raises(ValueError, match="_atom_site"):
        parse_mmcif("data_x\n_entry.id x\n")


def test_mmcif_quoted_and_semicolon_values():
    s = parse_mmcif("data_x\n_entry.id 'q v'\n"
                    "_entry.desc\n;multi\nline;\n;\n"
                    + MMCIF[MMCIF.index("loop_"):])
    assert len(s["atoms"]) == 3


def test_queries():
    s = parse_pdb(PDB)
    assert chains(s) == ["A", "B"]
    assert residues(s, "A") == [
        {"chain": "A", "resseq": 1, "icode": None, "resname": "ALA",
         "model": 1},
        {"chain": "A", "resseq": 2, "icode": None, "resname": "GLY",
         "model": 1}]
    assert [a["serial"] for a in select(s, names=["CA"])] == [2, 5]
    assert [a["serial"] for a in select(s, record="HETATM")] == [6]
    assert coordinates(select(s, chain="B")) == [(3.9, 3.2, 0.3)]
    assert centroid(select(s, chain="B")) == (3.9, 3.2, 0.3)
    assert stats(s) == {"format": "pdb", "models": 1, "chains": ["A", "B"],
                        "residues": 3, "atoms": 6, "hetatms": 1,
                        "elements": ["C", "N", "O"]}


def test_distance_and_contacts():
    s = parse_pdb(PDB)
    ca = select(s, names=["CA"])
    assert abs(distance(ca[0], ca[1])
               - ((1.5 - 3.8) ** 2 + 3.1 ** 2) ** 0.5) < 1e-9
    c = contacts(s, 2.0, chain_a="A", chain_b="B")
    assert len(c) == 2
    assert c[0]["distance"] == 1.5524 and c[1]["distance"] == 0.3317
    same_res = contacts(s, 2.0)
    assert all(not (p["a"]["chain"] == p["b"]["chain"]
                    and p["a"]["resseq"] == p["b"]["resseq"])
               for p in same_res)
    with pytest.raises(ValueError, match="positive"):
        contacts(s, 0)
