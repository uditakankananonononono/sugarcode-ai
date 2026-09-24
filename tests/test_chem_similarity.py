"""chem_similarity: RDKit-compatible Morgan fingerprints, Tanimoto/Dice, nearest neighbours.

Oracle values (tests/fixtures/chem_similarity_oracle.json) come from RDKit
2024.09.6 on PubChem CIDs 1-400; RDKit is not imported here. Tiny molecules are
also hand-hashed with an independent 32-bit boost::hash_combine written below.
"""
import json
from pathlib import Path

import pytest

from sugarcode.modules.chem_descriptors import compute_descriptors
from sugarcode.modules.chem_similarity import (dice, morgan_bit_info, morgan_bits, morgan_counts,
                                               nearest_neighbors, similarity_matrix, tanimoto)

FX = json.loads((Path(__file__).parent / "fixtures" / "chem_similarity_oracle.json").read_text())
MOLS = FX["molecules"]


def _hc(seed, v):   # independent boost::hash_combine, 32-bit
    return (seed ^ ((v + 0x9E3779B9 + (seed << 6) + (seed >> 2)) & 0xFFFFFFFF)) & 0xFFFFFFFF


def _hv(vals):
    s = 0
    for v in vals:
        s = _hc(s, v & 0xFFFFFFFF)
    return s


def test_hand_hashed_methane_ethane():
    # atom invariant = hash([Z, total degree, total H, charge, delta mass])
    ch4 = _hv([6, 4, 4, 0, 0])
    assert ch4 == 2246733040 and morgan_counts("C") == {ch4: 1}      # RDKit value
    ch3 = _hv([6, 4, 3, 0, 0])
    # round 1: seed = layer 0, combine own invariant, then hash(pair(bond type 1, nbr inv))
    r1 = _hc(_hc(0, ch3), _hv([1, ch3]))
    assert (ch3, r1) == (2246728737, 3545175291)
    # both carbons share the same one-bond environment -> kept once
    assert morgan_counts("CC") == {ch3: 2, r1: 1}
    assert morgan_counts("O") == {864666390: 1}
    assert morgan_counts("C=O") == {864942730: 1, 1517181260: 1, 2246997334: 1}
    assert morgan_counts("c1ccccc1") == {98513984: 6, 2763854213: 6, 3218693969: 6}
    # ring flag: cyclohexane carbon invariant carries the trailing 1
    assert _hv([6, 4, 2, 0, 0, 1]) in morgan_counts("C1CCCCC1", 0)


def test_morgan_counts_match_rdkit_on_400_pubchem_compounds():
    assert len(MOLS) == 400
    bad = []
    for m in MOLS:
        for r in ("1", "2", "3"):
            ref = {int(k): v for k, v in m["morgan_counts"][r].items()}
            if morgan_counts(m["smiles"], int(r)) != ref:
                bad.append((m["cid"], r))
        if sorted(morgan_bits(m["smiles"], 2, 2048)) != m["morgan2_bits_2048"]:
            bad.append((m["cid"], "bits"))
    assert bad == []


def test_descriptors_match_rdkit_on_400_pubchem_compounds():
    bad = []
    for m in MOLS:
        d = compute_descriptors(m["smiles"])
        for k, v in m["descriptors"].items():
            if k == "formula" and "C" not in v.replace("Ca", "").replace("Cl", ""):
                continue     # carbon-free: we use strict Hill order, RDKit writes H first
            ok = abs(v - d[k]) < 1e-6 if isinstance(v, float) else v == d[k]
            if not ok:
                bad.append((m["cid"], k, v, d[k]))
    assert bad == []


def test_bulk_similarity_matches_rdkit():
    bits = [morgan_bits(m["smiles"]) for m in MOLS]
    cnts = [morgan_counts(m["smiles"]) for m in MOLS]
    for q in FX["queries"]:
        i = q["query_index"]
        for j in range(len(MOLS)):
            assert tanimoto(bits[i], bits[j]) == pytest.approx(q["tanimoto_bits"][j], abs=1e-12)
            assert tanimoto(cnts[i], cnts[j]) == pytest.approx(q["tanimoto_counts"][j], abs=1e-12)
            assert dice(bits[i], bits[j]) == pytest.approx(q["dice_bits"][j], abs=1e-12)


def test_nearest_neighbors_rank_matches_rdkit_order():
    lib = [m["smiles"] for m in MOLS]
    for q in FX["queries"][:4]:
        i = q["query_index"]
        res = nearest_neighbors(lib[i], lib, k=5)
        ref = sorted(range(len(lib)), key=lambda j: (-q["tanimoto_bits"][j], j))[:5]
        assert [h["index"] for h in res["hits"]] == ref
        assert res["hits"][0]["similarity"] == 1.0 and res["invalid"] == []


def test_tanimoto_hand_values_and_edge_cases():
    assert tanimoto({1, 2, 3}, {2, 3, 4}) == pytest.approx(2 / 4)
    assert dice({1, 2, 3}, {2, 3, 4}) == pytest.approx(4 / 6)
    assert tanimoto({1: 2, 2: 1}, {1: 1, 3: 1}) == pytest.approx(1 / (3 + 2 - 1))
    assert tanimoto(set(), set()) == 0.0
    ethane, ethanol = morgan_counts("CC"), morgan_counts("CCO")
    # shared: one CH3 radius-0 code (min(2,1)=1); totals 3 and 6
    assert tanimoto(ethane, ethanol) == pytest.approx(1 / (3 + 6 - 1))


def test_nn_threshold_invalid_and_matrix():
    res = nearest_neighbors("CCO", ["CCO", "CCCO", "C1CC", "c1ccccc1"], k=3, threshold=0.2)
    assert [h["smiles"] for h in res["hits"]][0] == "CCO"
    assert all(h["similarity"] >= 0.2 for h in res["hits"])
    assert res["invalid"][0]["smiles"] == "C1CC"
    with pytest.raises(ValueError):
        nearest_neighbors("CCO", ["C1CC"], skip_invalid=False)
    mx = similarity_matrix(["CCO", "CCN", "CCO"], kind="counts")
    assert mx[0][2] == 1.0 and mx[0][1] == mx[1][0] and 0 < mx[0][1] < 1


def test_bit_info_radius_and_fold():
    info = morgan_bit_info("CCO", 2, 64)
    assert all(0 <= b < 64 for b in info)
    # radius-2 environments of the end atoms equal the middle atom's radius-1 one -> dropped
    assert sorted(r for v in info.values() for _, r in v) == [0, 0, 0, 1, 1, 1]
    assert morgan_bits("CCO", 0) == frozenset(c % 2048 for c in morgan_counts("CCO", 0))
