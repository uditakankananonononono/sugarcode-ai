"""Transparent molecular graph descriptors and Morgan-style fingerprints.

This is not a replacement for a sanitising chemistry toolkit. It provides a
strict, deterministic graph representation for common drug-like SMILES and
fails closed on unsupported syntax rather than silently inventing chemistry.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, math, re
from collections import Counter, deque
import numpy as np

# IUPAC standard atomic weights (conventional abridged values).
MASS = {"H":1.008,"B":10.81,"C":12.011,"N":14.007,"O":15.999,"F":18.998403,
        "P":30.973762,"S":32.06,"Cl":35.45,"Br":79.904,"I":126.90447,
        "Si":28.085,"Se":78.971}
VALENCE = {"B":3,"C":4,"N":3,"O":2,"F":1,"P":3,"S":2,"Cl":1,"Br":1,"I":1,
           "Si":4,"Se":2}
TOKEN = re.compile(r"Cl|Br|Si|Se|\[[^\]]+\]|[BCNOPSFIbcnops]|\(|\)|=|#|-|:|\.|%\d{2}|\d")

@dataclass(frozen=True)
class Atom:
    element: str
    aromatic: bool = False
    charge: int = 0
    explicit_h: int = 0

@dataclass
class Molecule:
    atoms: list[Atom]
    bonds: list[tuple[int,int,float]]
    components: int


def _atom(token: str) -> Atom:
    raw = token[1:-1] if token.startswith("[") else token
    m = re.match(r"(?:\d+)?(Cl|Br|Si|Se|[A-Z][a-z]?|[bcnops])", raw)
    if not m or m.group(1).capitalize() not in MASS:
        raise ValueError(f"unsupported atom token: {token}")
    sym = m.group(1); aromatic = sym.islower(); element = sym.capitalize()
    hm = re.search(r"H(\d*)", raw[m.end():])
    explicit_h = (int(hm.group(1)) if hm and hm.group(1) else 1) if hm else 0
    charge = 0
    for sign, n in re.findall(r"([+-])(\d*)", raw[m.end():]):
        charge += (1 if sign == "+" else -1) * (int(n) if n else 1)
    return Atom(element, aromatic, charge, explicit_h)


def parse_smiles(smiles: str) -> Molecule:
    """Parse common SMILES into a molecular graph; reject malformed input."""
    if not isinstance(smiles, str) or not smiles.strip(): raise ValueError("SMILES is empty")
    toks = TOKEN.findall(smiles)
    if "".join(toks) != smiles: raise ValueError("unsupported or malformed SMILES syntax")
    atoms=[]; bonds=[]; stack=[]; rings={}; current=None; pending=None; components=1
    bondmap={"-":1.0,"=":2.0,"#":3.0,":":1.5}
    for tok in toks:
        if tok in bondmap: pending=bondmap[tok]; continue
        if tok == "(":
            if current is None: raise ValueError("branch without atom")
            stack.append(current); continue
        if tok == ")":
            if not stack: raise ValueError("unmatched branch close")
            current=stack.pop(); continue
        if tok == ".": current=None; pending=None; components += 1; continue
        if tok[0].isdigit() or tok.startswith("%"):
            if current is None: raise ValueError("ring without atom")
            key=tok[1:] if tok.startswith("%") else tok
            if key in rings:
                other, oldbond=rings.pop(key); order=pending or oldbond
                if order is None: order=1.5 if atoms[current].aromatic and atoms[other].aromatic else 1.0
                bonds.append((other,current,order))
            else: rings[key]=(current,pending)
            pending=None; continue
        atom=_atom(tok); idx=len(atoms); atoms.append(atom)
        if current is not None:
            order=pending
            if order is None: order=1.5 if atom.aromatic and atoms[current].aromatic else 1.0
            bonds.append((current,idx,order))
        current=idx; pending=None
    if stack or rings: raise ValueError("unclosed branch or ring")
    if not atoms: raise ValueError("SMILES contains no atoms")
    return Molecule(atoms,bonds,components)


def _adj(m: Molecule):
    a=[[] for _ in m.atoms]
    for i,j,o in m.bonds: a[i].append((j,o)); a[j].append((i,o))
    return a


def _implicit_h(atom: Atom, neighbors) -> int:
    if atom.aromatic:
        target = 3 if atom.element == "C" else (3 if atom.element == "N" and atom.charge > 0 else 2)
        used = len(neighbors) + atom.explicit_h
    else:
        target = VALENCE.get(atom.element, 0) + (1 if atom.element == "N" and atom.charge > 0 else 0)
        used = int(round(sum(o for _,o in neighbors))) + atom.explicit_h
    return max(0, target-used)


def descriptors(smiles: str) -> dict[str,float]:
    """Calculate auditable 2D constitutional/graph descriptors.

    Values are computed from the parsed graph: formula mass, heavy atom and
    heteroatom counts, formal charge, H-bond donor/acceptor heuristic counts,
    rotatable acyclic single bonds, ring rank, aromatic fraction and graph
    diameter. HBD/HBA rules are deliberately labelled heuristic because full
    tautomer and resonance normalisation requires a chemistry toolkit.
    """
    m=parse_smiles(smiles); adj=_adj(m); counts=Counter(a.element for a in m.atoms)
    implicit=[_implicit_h(a,adj[i]) for i,a in enumerate(m.atoms)]
    total_h=sum(implicit)+sum(a.explicit_h for a in m.atoms)
    mw=sum(MASS[a.element] for a in m.atoms)+MASS["H"]*total_h
    hetero=sum(a.element not in {"C","H"} for a in m.atoms)
    hbd=sum(a.element in {"N","O","S"} and (a.explicit_h+implicit[i])>0 for i,a in enumerate(m.atoms))
    hba=sum(a.element in {"N","O","S","P","F","Cl","Br","I"} and a.charge<=0 and
            not (a.element=="N" and (a.explicit_h+implicit[i])>0 and len(adj[i])>=3)
            for i,a in enumerate(m.atoms))
    ring_rank=max(0,len(m.bonds)-len(m.atoms)+m.components)
    rot=sum(o==1 and len(adj[i])>1 and len(adj[j])>1 for i,j,o in m.bonds)-ring_rank
    # maximum finite shortest-path distance
    diameter=0
    for start in range(len(m.atoms)):
        d={start:0}; q=deque([start])
        while q:
            u=q.popleft()
            for v,_ in adj[u]:
                if v not in d: d[v]=d[u]+1; q.append(v)
        diameter=max(diameter,max(d.values()))
    return {"molecular_weight":round(mw,6),"heavy_atoms":float(len(m.atoms)),
      "hetero_atoms":float(hetero),"formal_charge":float(sum(a.charge for a in m.atoms)),
      "hbd_heuristic":float(hbd),"hba_heuristic":float(hba),
      "rotatable_bonds_heuristic":float(max(0,rot)),"ring_rank":float(ring_rank),
      "aromatic_fraction":sum(a.aromatic for a in m.atoms)/len(m.atoms),
      "graph_diameter":float(diameter),"fraction_csp3":sum(a.element=="C" and not a.aromatic for a in m.atoms)/max(1,counts["C"])}


def morgan_fingerprint(smiles: str, radius: int=2, n_bits: int=2048) -> np.ndarray:
    """Hashed circular fingerprint following Morgan/ECFP neighbourhood updates.

    Uses stable SHA-256 folding, avoiding Python's process-randomised hash.
    Collisions are expected and exposed through ``n_bits``.
    """
    if radius<0 or n_bits<8: raise ValueError("radius must be >=0 and n_bits >=8")
    m=parse_smiles(smiles); adj=_adj(m); fp=np.zeros(n_bits,dtype=np.float64)
    ids=[]
    for i,a in enumerate(m.atoms):
        s=f"{a.element}|{a.aromatic}|{a.charge}|{len(adj[i])}|{a.explicit_h}"
        ids.append(hashlib.sha256(s.encode()).hexdigest())
    for r in range(radius+1):
        for value in ids: fp[int(value[:16],16)%n_bits]=1.0
        if r<radius:
            ids=[hashlib.sha256((ids[i]+"|"+";".join(sorted(f"{o}:{ids[j]}" for j,o in adj[i]))).encode()).hexdigest() for i in range(len(ids))]
    return fp
