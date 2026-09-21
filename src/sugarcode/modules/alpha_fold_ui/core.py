from __future__ import annotations
import math
import numpy as np

# Chou-Fasman propensities (P_alpha, P_beta, P_turn) - published parameters
CF = {
    "A": (142, 83, 66), "R": (98, 93, 95), "N": (67, 89, 156), "D": (101, 54, 146),
    "C": (70, 119, 119), "Q": (111, 110, 98), "E": (151, 37, 74), "G": (57, 75, 156),
    "H": (100, 87, 95), "I": (108, 160, 47), "L": (121, 130, 59), "K": (114, 74, 101),
    "M": (145, 105, 60), "F": (113, 138, 60), "P": (57, 55, 152), "S": (77, 75, 143),
    "T": (83, 119, 96), "W": (108, 137, 96), "Y": (69, 147, 114), "V": (106, 170, 50),
}


def chou_fasman(seq: str) -> list[str]:
    """Chou-Fasman secondary structure prediction (real 1978 algorithm)."""
    n = len(seq)
    ss = ["C"] * n
    # helix nucleation: 4 of 6 residues with Pa > 100
    for i in range(n - 5):
        win = seq[i:i + 6]
        if sum(1 for a in win if CF.get(a, (0, 0, 0))[0] >= 100) >= 4:
            for j in range(i, min(n, i + 6)):
                ss[j] = "H"
    # extend helices
    i = 0
    while i < n:
        if ss[i] == "H":
            j = i
            while j + 1 < n and CF.get(seq[j + 1], (0, 0, 0))[0] > 100:
                j += 1
                ss[j] = "H"
            i = j
        i += 1
    # strands where not helix
    for i in range(n - 4):
        win = seq[i:i + 5]
        if sum(1 for a in win if CF.get(a, (0, 0, 0))[1] >= 105) >= 3:
            for j in range(i, min(n, i + 5)):
                if ss[j] == "C":
                    ss[j] = "E"
    return ss


def _confidence(seq: str, ss: list[str]) -> list[float]:
    """pLDDT-analog per residue: propensity-window agreement, scaled 0-100."""
    conf = []
    for i, a in enumerate(seq):
        lo, hi = max(0, i - 3), min(len(seq), i + 4)
        win_ss = ss[lo:hi]
        pa, pb, pt = CF.get(a, (50, 50, 50))
        dominant = max(pa, pb, pt)
        agree = win_ss.count(ss[i]) / len(win_ss)
        conf.append(round(min(95.0, 40.0 + 0.4 * dominant * agree), 1))
    return conf


def _pae_matrix(ss: list[str]) -> list[list[float]]:
    """PAE-analog: expected positional error; low within same element, high across."""
    n = len(ss)
    element_id = [0] * n
    eid = 0
    for i in range(1, n):
        if ss[i] != ss[i - 1]:
            eid += 1
        element_id[i] = eid
    pae = []
    for i in range(n):
        row = []
        for j in range(n):
            if element_id[i] == element_id[j]:
                row.append(round(1.0 + abs(i - j) * 0.15, 2))
            else:
                row.append(round(8.0 + abs(element_id[i] - element_id[j]) * 4.0, 2))
        pae.append(row)
    return pae


def _backbone(seq: str, ss: list[str]) -> np.ndarray:
    """Idealized C-alpha trace: helix (100 deg, 1.5 A rise), strand (extended), coil."""
    coords = np.zeros((len(seq), 3))
    pos = np.array([0.0, 0.0, 0.0])
    direction = np.array([1.0, 0.0, 0.0])
    helix_angle = math.radians(100.0)
    for i, s in enumerate(ss):
        coords[i] = pos
        if s == "H":
            theta = helix_angle * i
            step = np.array([0.0, 3.8 * math.cos(theta) * 0.4, 3.8 * math.sin(theta) * 0.4])
            step[0] = 1.5
        elif s == "E":
            step = direction * 3.4
        else:
            step = direction * 3.0 + np.array([0, 0.6 * math.sin(i * 1.7), 0.4 * math.cos(i * 2.3)])
        pos = pos + step
    return coords


def write_pdb(seq: str, coords: np.ndarray, confidence: list[float]) -> str:
    """PDB-format C-alpha trace with confidence in the B-factor column."""
    lines = []
    for i, (aa, (x, y, z), c) in enumerate(zip(seq, coords, confidence)):
        lines.append(
            f"ATOM  {i + 1:>5}  CA  {_aa3(aa)} A{i + 1:>4}    "
            f"{x:8.3f}{y:8.3f}{z:8.3f}  1.00{c:6.2f}           C"
        )
    lines.append("END")
    return "\n".join(lines) + "\n"


def _aa3(a: str) -> str:
    m = {"A": "ALA", "R": "ARG", "N": "ASN", "D": "ASP", "C": "CYS", "Q": "GLN",
         "E": "GLU", "G": "GLY", "H": "HIS", "I": "ILE", "L": "LEU", "K": "LYS",
         "M": "MET", "F": "PHE", "P": "PRO", "S": "SER", "T": "THR", "W": "TRP",
         "Y": "TYR", "V": "VAL"}
    return m.get(a, "UNK")


def predict_structure(sequence: str) -> dict:
    """Full structure pipeline: secondary prediction, confidence, PAE, PDB.

    Honest scope: Chou-Fasman statistics + idealized backbone geometry with
    pLDDT/PAE-analog metrics - not learned AlphaFold weights (later drop).
    """
    seq = "".join(a for a in sequence.upper() if a in CF)
    if not seq:
        raise ValueError("no valid amino acids")
    ss = chou_fasman(seq)
    conf = _confidence(seq, ss)
    coords = _backbone(seq, ss)
    pae = _pae_matrix(ss)
    from collections import Counter
    comp = Counter(ss)
    pockets = _binding_pockets(seq, ss, conf)
    return {
        "length": len(seq),
        "secondary_structure": "".join(ss),
        "composition": {"helix": comp.get("H", 0), "strand": comp.get("E", 0),
                        "coil": comp.get("C", 0)},
        "plddt_per_residue": conf,
        "mean_plddt": round(sum(conf) / len(conf), 1),
        "pae": pae,
        "pdb": write_pdb(seq, coords, conf),
        "candidate_binding_sites": pockets,
        "method": "chou-fasman-idealized-backbone (learned weights pending)",
    }


def _binding_pockets(seq: str, ss: list[str], conf: list[float]) -> list[dict]:
    """Surface pocket candidates: coil regions flanked by ordered elements with
    catalytic-residue content (His/Cys/Asp/Glu/Ser clusters)."""
    catalytic = set("HCDES")
    pockets = []
    i = 0
    while i < len(seq):
        if ss[i] == "C":
            j = i
            while j < len(seq) and ss[j] == "C":
                j += 1
            seg = seq[i:j]
            hits = [k for k, a in enumerate(seg) if a in catalytic]
            if len(seg) >= 4 and len(hits) >= 2:
                pockets.append({"start": i, "end": j,
                                "catalytic_residues": [f"{seg[k]}{i + k + 1}" for k in hits],
                                "mean_confidence": round(sum(conf[i:j]) / (j - i), 1)})
            i = j
        else:
            i += 1
    return pockets
