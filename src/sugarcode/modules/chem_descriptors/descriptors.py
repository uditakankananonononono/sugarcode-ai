"""Molecular descriptors and drug-likeness filters on the parsed graph.

Masses use the vendored periodic table (RDKit atomic_data.cpp, pinned; see
PROVENANCE.md). Descriptor definitions re-implement the RDKit 2024.09.6
definitions (pinned sources in PROVENANCE.md) so they can be oracle-tested:

  * mol_wt           average molecular weight (isotope mass for labelled atoms)
  * exact_mol_wt     monoisotopic mass (most common isotope), minus charge x electron mass
  * hbd / hba        RDKit Lipinski NumHDonors / NumHAcceptors SMARTS, as graph rules
  * nhoh / no_count  Lipinski's original donor (OH + NH hydrogens) / acceptor (N + O) counts
  * rotatable_bonds  RDKit "Strict" rotatable-bond SMARTS, as graph rules
  * tpsa             Ertl 2000 fragment TPSA (N and O; optional S and P), RDKit's rule table
  * ring_count       size of the minimum cycle basis (= SSSR count)
  * aromatic / aliphatic ring counts over that basis

Filters: Lipinski rule of five (Lipinski et al. 1997/2001: MW <= 500,
logP <= 5, OH+NH <= 5, N+O <= 10; "poor absorption is more likely" with two or
more violations) and Veber et al. 2002 (rotatable bonds <= 10 and PSA <= 140).
No logP model is included: pass ``logp`` yourself or the logP criterion is
reported as Missing and the rule-of-five verdict is marked incomplete.
"""
from __future__ import annotations

from collections import Counter

from .smiles import ELEMENTS, Molecule, _TABLE, parse_smiles

ELECTRON_MASS = _TABLE["electron_mass"]
ISOTOPES = _TABLE["isotopes"]


# ----------------------------------------------------------------- masses
def _atom_mass(at, exact: bool) -> float:
    if at.isotope is not None:
        m = ISOTOPES.get(at.symbol, {}).get(str(at.isotope))
        if m is None:
            raise ValueError(f"no mass for isotope {at.isotope}{at.symbol}")
        return m
    e = ELEMENTS[at.symbol]
    return e["common_isotope_mass"] if exact else e["average_mass"]


def mol_wt(mol: Molecule) -> float:
    h = ELEMENTS["H"]["average_mass"]
    return sum(_atom_mass(a, False) + a.total_h * h for a in mol.atoms)


def exact_mol_wt(mol: Molecule) -> float:
    h = ELEMENTS["H"]["common_isotope_mass"]
    m = sum(_atom_mass(a, True) + a.total_h * h for a in mol.atoms)
    return m - sum(a.charge for a in mol.atoms) * ELECTRON_MASS


def formula(mol: Molecule) -> str:
    """Hill-order formula (carbon, hydrogen, then alphabetical; with no carbon,
    everything alphabetical including H). Isotope labels fold into their element,
    as in RDKit's CalcMolFormula default; net charge appended."""
    c = Counter()
    for a in mol.atoms:
        key = a.symbol
        c[key] += 1
        c["H"] += a.total_h
    c = +c
    keys = sorted(c)
    if "C" in c:
        order = ["C"] + (["H"] if "H" in c else []) + [k for k in keys if k not in ("C", "H")]
    else:
        order = keys
    out = "".join(k + (str(c[k]) if c[k] > 1 else "") for k in order)
    q = sum(a.charge for a in mol.atoms)
    if q:
        out += ("+" if q > 0 else "-") + (str(abs(q)) if abs(q) > 1 else "")
    return out


# ----------------------------------------------------------------- helpers
def _valence(mol: Molecule, i: int) -> float:
    at = mol.atoms[i]
    return sum(bd.order for _, bd in mol.neighbors(i)) + at.total_h


def _is(mol, i, symbol, aromatic=False):
    a = mol.atoms[i]
    return a.symbol == symbol and a.aromatic == aromatic


def _in_triple(mol, i):
    return any(bd.order == 3.0 for _, bd in mol.neighbors(i))


# ----------------------------------------------------------------- H-bonding
def hbd(mol: Molecule) -> int:
    """RDKit NumHDonors: [N&!H0&v3, N&!H0&+1&v4, O&H1&+0, S&H1&+0, n&H1&+0]."""
    n = 0
    for i, a in enumerate(mol.atoms):
        v = _valence(mol, i)
        if a.symbol == "N" and not a.aromatic and a.total_h > 0 and (
                v == 3 or (a.charge == 1 and v == 4)):
            n += 1
        elif a.symbol in ("O", "S") and not a.aromatic and a.total_h == 1 and a.charge == 0:
            n += 1
        elif a.symbol == "N" and a.aromatic and a.total_h == 1 and a.charge == 0:
            n += 1
    return n


def _has_double_to(mol, j, symbols, exocyclic=False, exclude=None):
    for k, bd in mol.neighbors(j):
        if k == exclude or bd.aromatic or bd.order != 2.0:
            continue
        if exocyclic and bd.ring:
            continue
        if _aliphatic_in(mol, k, symbols):
            return True
    return False


def _aliphatic_in(mol, k, symbols):
    a = mol.atoms[k]
    return a.symbol in symbols and not a.aromatic


def hba(mol: Molecule) -> int:
    """RDKit NumHAcceptors:
    [$([O,S;H1;v2]-[!$(*=[O,N,P,S])]), $([O,S;H0;v2]), $([O,S;-]),
     $([N;v3;!$(N-*=!@[O,N,P,S])]), $([nH0,o,s;+0])]"""
    n = 0
    heteros = {"O", "N", "P", "S"}
    for i, a in enumerate(mol.atoms):
        v = _valence(mol, i)
        hit = False
        if a.symbol in ("O", "S") and not a.aromatic:
            if a.total_h == 1 and v == 2:
                hit = any(bd.order == 1.0 and not bd.aromatic and not _has_double_to(mol, j, heteros)
                          for j, bd in mol.neighbors(i))
            if not hit and a.total_h == 0 and v == 2:
                hit = True
            if not hit and a.charge < 0 and a.charge == -1:
                hit = True
        elif a.symbol == "N" and not a.aromatic and v == 3:
            hit = not any(bd.order == 1.0 and not bd.aromatic
                          and _has_double_to(mol, j, heteros, exocyclic=True)
                          for j, bd in mol.neighbors(i))
        elif a.aromatic and a.charge == 0 and (
                (a.symbol == "N" and a.total_h == 0) or a.symbol in ("O", "S")):
            hit = True
        n += hit
    return n


def nhoh_count(mol: Molecule) -> int:
    """Lipinski donors: hydrogens on N and O (RDKit NHOHCount)."""
    return sum(a.total_h for a in mol.atoms if a.symbol in ("N", "O"))


def no_count(mol: Molecule) -> int:
    """Lipinski acceptors: number of N and O atoms (RDKit NOCount)."""
    return sum(1 for a in mol.atoms if a.symbol in ("N", "O"))


# ----------------------------------------------------------------- rotatable bonds
def _base_ok(mol, i) -> bool:
    """[!$(*#*)&!D1&!$(C(F)(F)F)&!$(C(Cl)(Cl)Cl)&!$(C(Br)(Br)Br)&!$(C([CH3])([CH3])[CH3])]"""
    if _in_triple(mol, i) or mol.degree(i) == 1:
        return False
    a = mol.atoms[i]
    if a.symbol == "C" and not a.aromatic:
        nbrs = [j for j, _ in mol.neighbors(i)]
        for hal in ("F", "Cl", "Br"):
            if sum(1 for j in nbrs if _aliphatic_in(mol, j, {hal})) >= 3:
                return False
        methyls = sum(1 for j in nbrs if _is(mol, j, "C") and mol.atoms[j].total_h == 3)
        if methyls >= 3:
            return False
    return True


def _cd3_double_nos(mol, c, charged_n=False) -> bool:
    a = mol.atoms[c]
    if not (a.symbol == "C" and not a.aromatic and mol.degree(c) == 3):
        return False
    for k, bd in mol.neighbors(c):
        if bd.order == 2.0 and not bd.aromatic:
            b = mol.atoms[k]
            if charged_n:
                if b.symbol == "N" and not b.aromatic and b.charge == 1:
                    return True
            elif b.symbol in ("N", "O", "S") and not b.aromatic:
                return True
    return False


def _hetero_d(mol, k) -> bool:
    """[#7,O,S!D1]: any nitrogen, aliphatic O, or aliphatic S with D != 1."""
    b = mol.atoms[k]
    if b.symbol == "N":
        return True
    if b.symbol == "O" and not b.aromatic:
        return True
    return b.symbol == "S" and not b.aromatic and mol.degree(k) != 1


def _full_ok(mol, i) -> bool:
    if not _base_ok(mol, i):
        return False
    single_nonring = [(k, bd) for k, bd in mol.neighbors(i)
                      if bd.order == 1.0 and not bd.aromatic and not bd.ring]
    # !$([CD3](=[N,O,S])-!@[#7,O,S!D1])
    if _cd3_double_nos(mol, i) and any(_hetero_d(mol, k) for k, _ in single_nonring):
        return False
    # !$([#7,O,S!D1]-!@[CD3]=[N,O,S])
    if _hetero_d(mol, i) and any(_cd3_double_nos(mol, k) for k, _ in single_nonring):
        return False
    # !$([CD3](=[N+])-!@[#7!D1])
    if _cd3_double_nos(mol, i, charged_n=True) and any(
            mol.atoms[k].symbol == "N" and mol.degree(k) != 1 for k, _ in single_nonring):
        return False
    # !$([#7!D1]-!@[CD3]=[N+])
    if mol.atoms[i].symbol == "N" and mol.degree(i) != 1 and any(
            _cd3_double_nos(mol, k, charged_n=True) for k, _ in single_nonring):
        return False
    return True


def rotatable_bonds(mol: Molecule) -> int:
    """RDKit Strict NumRotatableBonds: full-pattern atom -,:;!@ base-pattern atom."""
    n = 0
    for bd in mol.bonds:
        if bd.ring or not (bd.order == 1.0 or bd.aromatic):
            continue
        a, b = bd.a, bd.b
        if (_full_ok(mol, a) and _base_ok(mol, b)) or (_full_ok(mol, b) and _base_ok(mol, a)):
            n += 1
    return n


# ----------------------------------------------------------------- rings
def minimum_cycle_basis(mol: Molecule) -> list[frozenset]:
    """Horton's algorithm: candidate cycles from shortest paths, then greedy
    GF(2)-independent selection by size. Returns rings as frozensets of bond indices."""
    n = len(mol.atoms)
    adj = {i: [] for i in range(n)}
    for k, bd in enumerate(mol.bonds):
        adj[bd.a].append((bd.b, k))
        adj[bd.b].append((bd.a, k))
    comps, seen = 0, set()
    for s in range(n):
        if s in seen:
            continue
        comps += 1
        stack = [s]
        seen.add(s)
        while stack:
            u = stack.pop()
            for v, _ in adj[u]:
                if v not in seen:
                    seen.add(v)
                    stack.append(v)
    rank_needed = len(mol.bonds) - n + comps
    if rank_needed == 0:
        return []

    def bfs_tree(root):
        parent = {root: (None, None)}
        order = [root]
        for u in order:
            for v, k in adj[u]:
                if v not in parent:
                    parent[v] = (u, k)
                    order.append(v)
        return parent

    def path_edges(parent, v):
        edges, verts = [], [v]
        while parent[v][0] is not None:
            u, k = parent[v]
            edges.append(k)
            v = u
            verts.append(v)
        return edges, verts

    candidates = set()
    for r in range(n):
        parent = bfs_tree(r)
        for k, bd in enumerate(mol.bonds):
            if bd.a not in parent or bd.b not in parent:
                continue
            e1, v1 = path_edges(parent, bd.a)
            e2, v2 = path_edges(parent, bd.b)
            if set(v1) & set(v2) != {r}:
                continue
            if k in e1 or k in e2:
                continue
            candidates.add(frozenset(e1 + e2 + [k]))
    basis_rows, chosen = [], []
    for cyc in sorted(candidates, key=lambda c: (len(c), sorted(c))):
        vec = 0
        for k in cyc:
            vec |= 1 << k
        for row in basis_rows:
            vec = min(vec, vec ^ row)
        if vec:
            basis_rows.append(vec)
            basis_rows.sort(reverse=True)
            chosen.append(cyc)
            if len(chosen) == rank_needed:
                break
    return chosen


def ring_counts(mol: Molecule) -> dict:
    rings = minimum_cycle_basis(mol)
    arom = sum(1 for r in rings if all(mol.bonds[k].aromatic for k in r))
    return {"ring_count": len(rings), "aromatic_ring_count": arom,
            "aliphatic_ring_count": len(rings) - arom,
            "ring_sizes": sorted(len(r) for r in rings)}


def _in_ring_of_size(mol: Molecule, i: int, size: int) -> bool:
    """True if atom i lies on a simple cycle of exactly ``size`` atoms (DFS)."""
    def dfs(u, depth, visited):
        for v, _ in mol.neighbors(u):
            if v == i and depth == size and size >= 3:
                return True
            if v not in visited and depth < size and v != i:
                if dfs(v, depth + 1, visited | {v}):
                    return True
        return False
    return dfs(i, 1, {i})


# ----------------------------------------------------------------- TPSA
def tpsa(mol: Molecule, include_s_and_p: bool = False) -> float:
    """Ertl et al. 2000 fragment TPSA, following RDKit getTPSAAtomContribs."""
    total = 0.0
    for i, a in enumerate(mol.atoms):
        z = a.Z
        if z not in (7, 8) and not (include_s_and_p and z in (15, 16)):
            continue
        nS = nD = nT = nA = 0
        nH = a.total_h
        nNbrs = 0
        for j, bd in mol.neighbors(i):
            if mol.atoms[j].symbol == "H":
                nH += 1
                continue
            nNbrs += 1
            if bd.aromatic:
                nA += 1
            elif bd.order == 1.0:
                nS += 1
            elif bd.order == 2.0:
                nD += 1
            elif bd.order == 3.0:
                nT += 1
        chg = a.charge
        r3 = _in_ring_of_size(mol, i, 3)
        tmp = -1.0
        if z == 7:
            if nNbrs == 1:
                if nH == 0 and chg == 0 and nT == 1: tmp = 23.79
                elif nH == 1 and chg == 0 and nD == 1: tmp = 23.85
                elif nH == 2 and chg == 0 and nS == 1: tmp = 26.02
                elif nH == 2 and chg == 1 and nD == 1: tmp = 25.59
                elif nH == 3 and chg == 1 and nS == 1: tmp = 27.64
            elif nNbrs == 2:
                if nH == 0 and chg == 0 and nS == 1 and nD == 1: tmp = 12.36
                elif nH == 0 and chg == 0 and nT == 1 and nD == 1: tmp = 13.60
                elif nH == 1 and chg == 0 and nS == 2 and r3: tmp = 21.94
                elif nH == 1 and chg == 0 and nS == 2 and not r3: tmp = 12.03
                elif nH == 0 and chg == 1 and nT == 1 and nS == 1: tmp = 4.36
                elif nH == 1 and chg == 1 and nD == 1 and nS == 1: tmp = 13.97
                elif nH == 2 and chg == 1 and nS == 2: tmp = 16.61
                elif nH == 0 and chg == 0 and nA == 2: tmp = 12.89
                elif nH == 1 and chg == 0 and nA == 2: tmp = 15.79
                elif nH == 1 and chg == 1 and nA == 2: tmp = 14.14
            elif nNbrs == 3:
                if nH == 0 and chg == 0 and nS == 3 and r3: tmp = 3.01
                elif nH == 0 and chg == 0 and nS == 3 and not r3: tmp = 3.24
                elif nH == 0 and chg == 0 and nS == 1 and nD == 2: tmp = 11.68
                elif nH == 0 and chg == 1 and nS == 2 and nD == 1: tmp = 3.01
                elif nH == 1 and chg == 1 and nS == 3: tmp = 4.44
                elif nH == 0 and chg == 0 and nA == 3: tmp = 4.41
                elif nH == 0 and chg == 0 and nS == 1 and nA == 2: tmp = 4.93
                elif nH == 0 and chg == 0 and nD == 1 and nA == 2: tmp = 8.39
                elif nH == 0 and chg == 1 and nA == 3: tmp = 4.10
                elif nH == 0 and chg == 1 and nS == 1 and nA == 2: tmp = 3.88
            elif nNbrs == 4:
                if nH == 0 and nS == 4 and chg == 1: tmp = 0.0
            if tmp < 0:
                tmp = max(0.0, 30.5 - nNbrs * 8.2 + nH * 1.5)
        elif z == 8:
            if nNbrs == 1:
                if nH == 0 and chg == 0 and nD == 1: tmp = 17.07
                elif nH == 1 and chg == 0 and nS == 1: tmp = 20.23
                elif nH == 0 and chg == -1 and nS == 1: tmp = 23.06
            elif nNbrs == 2:
                if nH == 0 and chg == 0 and nS == 2 and r3: tmp = 12.53
                elif nH == 0 and chg == 0 and nS == 2 and not r3: tmp = 9.23
                elif nH == 0 and chg == 0 and nA == 2: tmp = 13.14
            if tmp < 0:
                tmp = max(0.0, 28.5 - nNbrs * 8.6 + nH * 1.5)
        elif z == 15:
            tmp = 0.0
            if nNbrs == 2 and nH == 0 and chg == 0 and nS == 1 and nD == 1: tmp = 34.14
            elif nNbrs == 3 and nH == 0 and chg == 0 and nS == 3: tmp = 13.59
            elif nNbrs == 3 and nH == 1 and chg == 0 and nS == 2 and nD == 1: tmp = 23.47
            elif nNbrs == 4 and nH == 0 and chg == 0 and nS == 3 and nD == 1: tmp = 9.81
        elif z == 16:
            tmp = 0.0
            if nNbrs == 1 and nH == 0 and chg == 0 and nD == 1: tmp = 32.09
            elif nNbrs == 1 and nH == 1 and chg == 0 and nS == 1: tmp = 38.80
            elif nNbrs == 2 and nH == 0 and chg == 0 and nS == 2: tmp = 25.30
            elif nNbrs == 2 and nH == 0 and chg == 0 and nA == 2: tmp = 28.24
            elif nNbrs == 3 and nH == 0 and chg == 0 and nA == 2 and nD == 1: tmp = 21.70
            elif nNbrs == 3 and nH == 0 and chg == 0 and nS == 2 and nD == 1: tmp = 19.21
            elif nNbrs == 4 and nH == 0 and chg == 0 and nS == 2 and nD == 2: tmp = 8.38
        total += tmp
    return total


# ----------------------------------------------------------------- summary + filters
def fraction_csp3(mol: Molecule) -> float:
    carbons = [i for i, a in enumerate(mol.atoms) if a.symbol == "C"]
    if not carbons:
        return 0.0
    sp3 = sum(1 for i in carbons if not mol.atoms[i].aromatic and all(
        bd.order == 1.0 and not bd.aromatic for _, bd in mol.neighbors(i)))
    return sp3 / len(carbons)


def compute_descriptors(smiles_or_mol) -> dict:
    mol = parse_smiles(smiles_or_mol) if isinstance(smiles_or_mol, str) else smiles_or_mol
    rc = ring_counts(mol)
    return {
        "smiles": mol.smiles,
        "formula": formula(mol),
        "mol_wt": mol_wt(mol),
        "exact_mol_wt": exact_mol_wt(mol),
        "heavy_atom_count": sum(1 for a in mol.atoms if a.symbol != "H"),
        "heteroatom_count": sum(1 for a in mol.atoms if a.symbol not in ("C", "H")),
        "formal_charge": sum(a.charge for a in mol.atoms),
        "hbd": hbd(mol), "hba": hba(mol),
        "nhoh_count": nhoh_count(mol), "no_count": no_count(mol),
        "rotatable_bonds": rotatable_bonds(mol),
        "tpsa": tpsa(mol),
        "fraction_csp3": fraction_csp3(mol),
        **rc,
        "ignored_features": list(mol.ignored),
    }


def lipinski_rule_of_five(desc: dict, logp: float | None = None) -> dict:
    """Lipinski 1997/2001. Donors = OH+NH hydrogens, acceptors = N+O atoms.
    Passes with at most one violation. Without ``logp`` the logP criterion is
    Missing and ``complete`` is False."""
    checks = {"mol_wt_le_500": desc["mol_wt"] <= 500,
              "hbd_le_5": desc["nhoh_count"] <= 5,
              "hba_le_10": desc["no_count"] <= 10,
              "logp_le_5": (logp <= 5) if logp is not None else "Missing"}
    violations = [k for k, v in checks.items() if v is False]
    return {"checks": checks, "violations": violations, "violation_count": len(violations),
            "passes": (len(violations) <= 1) if (logp is not None or len(violations) != 1)
                      else "Undetermined",
            "complete": logp is not None,
            "note": None if logp is not None else
            "logP not supplied (no logP model is bundled); verdict based on 3 of 4 criteria"}


def veber_filter(desc: dict) -> dict:
    """Veber et al. 2002: rotatable bonds <= 10 and polar surface area <= 140 A^2."""
    checks = {"rotatable_bonds_le_10": desc["rotatable_bonds"] <= 10,
              "tpsa_le_140": desc["tpsa"] <= 140}
    return {"checks": checks, "passes": all(checks.values())}


def druglikeness(smiles: str, logp: float | None = None) -> dict:
    d = compute_descriptors(smiles)
    return {"descriptors": d, "lipinski": lipinski_rule_of_five(d, logp), "veber": veber_filter(d)}
