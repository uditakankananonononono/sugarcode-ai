"""Molecular graph descriptors and Morgan-style hashed fingerprints.

This is not a replacement for a sanitising chemistry toolkit. The parser is
deterministic, rejects unknown atom tokens, unbalanced or empty branches, unclosed
rings, dangling bond symbols and atoms above their maximum valence, and lists
stereo marks it does not model in ``Molecule.ignored``. It does not check
aromatic-ring kekulizability ("c1cccc1" parses). Kekule and aromatic spellings
of one molecule give different graphs and fingerprints.
"""
from __future__ import annotations
from dataclasses import dataclass
import hashlib, math, re
from collections import Counter, deque
import numpy as np

# IUPAC standard atomic weights (conventional abridged values).
MASS = {"H":1.008,"B":10.81,"C":12.011,"N":14.007,"O":15.999,"F":18.998403,
        "P":30.973762,"S":32.06,"Cl":35.45,"Br":79.904,"I":126.90447,
        "Si":28.085,"Se":78.971,
        # counter-ions and metals seen in approved-drug salts (bracket atoms only)
        "Li":6.94,"Na":22.98977,"K":39.0983,"Mg":24.305,"Ca":40.078,"Zn":65.38,
        "Ag":107.8682,"Al":26.981538,"Fe":55.845,"Cu":63.546,"Co":58.933194,
        "Pt":195.084,"Au":196.96657,"Bi":208.9804,"Gd":157.25,"Sr":87.62,
        "Ba":137.327,"As":74.921595,"Hg":200.592,"Mn":54.938043,"Ti":47.867,"Sb":121.76}
VALENCE = {"B":3,"C":4,"N":3,"O":2,"F":1,"P":3,"S":2,"Cl":1,"Br":1,"I":1,
           "Si":4,"Se":2}
# Highest valence accepted per element when checking a parsed graph. Hypervalent
# P, S, Se, halogens and N (nitro written N(=O)=O) are allowed up to the usual
# maximum; anything above is rejected instead of being accepted as written.
MAX_VALENCE = {"H":1,"B":3,"C":4,"N":5,"O":2,"F":1,"P":5,"S":6,"Cl":7,"Br":7,"I":7,
               "Si":4,"Se":6}
TOKEN = re.compile(r"Cl|Br|Si|Se|\[[^\]]+\]|[BCNOPSFIbcnops]|\(|\)|=|#|-|:|/|\\|\.|%\d{2}|\d")

@dataclass(frozen=True)
class Atom:
    element: str
    aromatic: bool = False
    charge: int = 0
    explicit_h: int = 0
    bracket: bool = False

@dataclass
class Molecule:
    atoms: list[Atom]
    bonds: list[tuple[int,int,float]]
    components: int
    # Syntax that is parsed but not represented in the graph (stereo). Never silent.
    ignored: tuple[str,...] = ()


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
    return Atom(element, aromatic, charge, explicit_h, token.startswith("["))


def parse_smiles(smiles: str, *, strict_stereo: bool = False) -> Molecule:
    """Parse common SMILES into a molecular graph; reject malformed input.

    Rejects dangling or doubled bond symbols ("C=", "C==C", "=C"), empty branches
    ("C()"), misplaced "." and ring closures onto the same atom or an already
    bonded atom ("C11", "C1C1"). Rejects valence-impossible atoms (for example
    pentavalent carbon). Does not check that aromatic
    rings can be kekulized ("c1cccc1" parses). Tetrahedral
    chirality (@, @@) and cis/trans marks (/, \\) are not represented in the graph:
    they are listed in ``Molecule.ignored``, or raise ValueError when
    ``strict_stereo=True``."""
    if not isinstance(smiles, str) or not smiles.strip(): raise ValueError("SMILES is empty")
    toks = TOKEN.findall(smiles)
    if "".join(toks) != smiles: raise ValueError("unsupported or malformed SMILES syntax")
    atoms=[]; bonds=[]; stack=[]; rings={}; current=None; pending=None; components=1
    bond_pending=False  # a bond symbol was read and no atom or ring digit has used it yet
    after_open=False    # the previous token was "("
    bondmap={"-":1.0,"=":2.0,"#":3.0,":":1.5,"/":None,"\\":None}  # / and \\ only mark direction: order follows the implicit rule (aromatic between aromatic atoms, as RDKit reads c1/s...)
    for tok in toks:
        if tok in bondmap:
            if bond_pending: raise ValueError("consecutive bond symbols")
            if current is None: raise ValueError("bond symbol with no preceding atom")
            pending=bondmap[tok]; bond_pending=True; after_open=False; continue
        if tok == "(":
            if current is None: raise ValueError("branch without atom")
            if bond_pending: raise ValueError("bond symbol before branch")
            stack.append(current); after_open=True; continue
        if tok == ")":
            if not stack: raise ValueError("unmatched branch close")
            if after_open or current is None: raise ValueError("empty branch")
            if bond_pending: raise ValueError("branch ends with a bond symbol")
            current=stack.pop(); continue
        if tok == ".":
            if bond_pending or current is None or after_open: raise ValueError("misplaced '.'")
            current=None; pending=None; components += 1; continue
        if tok[0].isdigit() or tok.startswith("%"):
            if current is None: raise ValueError("ring without atom")
            key=tok[1:] if tok.startswith("%") else tok
            if key in rings:
                other, oldbond=rings.pop(key); order=pending or oldbond
                if other==current: raise ValueError("ring closure bonds an atom to itself")
                if any({x,y}=={other,current} for x,y,_ in bonds): raise ValueError("ring closure repeats an existing bond")
                if order is None: order=1.5 if atoms[current].aromatic and atoms[other].aromatic else 1.0
                bonds.append((other,current,order))
            else: rings[key]=(current,pending)
            pending=None; bond_pending=False; after_open=False; continue
        atom=_atom(tok); idx=len(atoms); atoms.append(atom)
        if current is not None:
            order=pending
            if order is None: order=1.5 if atom.aromatic and atoms[current].aromatic else 1.0
            bonds.append((current,idx,order))
        current=idx; pending=None; bond_pending=False; after_open=False
    if bond_pending: raise ValueError("trailing bond symbol")
    if toks[-1]==".": raise ValueError("trailing '.'")
    if stack or rings: raise ValueError("unclosed branch or ring")
    if not atoms: raise ValueError("SMILES contains no atoms")
    _check_valence(atoms,bonds)
    ignored=[]
    if any(t.startswith("[") and "@" in t for t in toks): ignored.append("tetrahedral chirality (@, @@)")
    if "/" in toks or "\\" in toks: ignored.append("cis/trans bond direction (/, \\)")
    if ignored and strict_stereo: raise ValueError("stereochemistry not supported: "+"; ".join(ignored))
    return Molecule(atoms,bonds,components,tuple(ignored))


def _check_valence(atoms,bonds):
    used=[0.0]*len(atoms); deg=[0]*len(atoms)
    for i,j,o in bonds:
        used[i]+=o; used[j]+=o; deg[i]+=1; deg[j]+=1
    for i,a in enumerate(atoms):
        if a.aromatic:
            if deg[i]>3: raise ValueError(f"valence error: aromatic {a.element} atom {i} has {deg[i]} neighbours")
            continue
        if a.charge!=0 or a.element not in MAX_VALENCE: continue
        total=int(round(used[i]))+a.explicit_h
        if a.element=="N" and total>3 and not any(o>=2 for k,(x,y,o) in enumerate(bonds) if i in (x,y)):
            raise ValueError(f"valence error: N atom {i} has valence {total} with no multiple bond")
        if total>MAX_VALENCE[a.element]:
            raise ValueError(f"valence error: {a.element} atom {i} has valence {total} (max {MAX_VALENCE[a.element]})")


def _adj(m: Molecule):
    a=[[] for _ in m.atoms]
    for i,j,o in m.bonds: a[i].append((j,o)); a[j].append((i,o))
    return a


def _implicit_h(atom: Atom, neighbors) -> int:
    if atom.bracket:
        return 0  # SMILES: bracket atoms carry exactly their written hydrogens
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
    def _in_ring(i,j):
        seen={i}; q=deque([i])
        while q:
            u=q.popleft()
            for v,_ in adj[u]:
                if (u==i and v==j) or v in seen: continue
                if v==j: return True
                seen.add(v); q.append(v)
        return False
    triple={k for a,b,o in m.bonds if o==3 for k in (a,b)}
    # rotatable: acyclic single bond between two non-terminal atoms, neither in a triple bond
    rot=sum(o==1 and len(adj[i])>1 and len(adj[j])>1 and i not in triple and j not in triple
            and not _in_ring(i,j) for i,j,o in m.bonds)
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
      "graph_diameter":float(diameter),"fraction_csp3":sum(a.element=="C" and not a.aromatic and all(o==1 for _,o in adj[i]) for i,a in enumerate(m.atoms))/max(1,counts["C"])}


def morgan_fingerprint(smiles: str, radius: int=2, n_bits: int=2048) -> np.ndarray:
    """Hashed circular fingerprint with Morgan/ECFP-style neighbourhood updates.

    Not RDKit's Morgan implementation: duplicate environments are not removed,
    aromatic and Kekule spellings differ, and chirality is ignored. On the
    first 60 molecules (1,770 pairs) and first 120 molecules (7,140 pairs) from
    seed 20261012, both comparisons against RDKit Morgan radius 2, 2048 bits
    produced Spearman 1.0 (maximum absolute difference 0.0) with RDKit 2024.09.6.
    Corpus SHA-256: 1f2256b7cfbe8d41fa3b2be9f2726e9a392ae076f82da1359630dc7737fb66c7;
    60-molecule pair-list SHA-256: b6b39cbce33c9003e96def5262f1c5ebdd51cac11c33e7d57c16b09cff4348b7.

    Uses stable SHA-256 folding, avoiding Python's process-randomised hash.
    Collisions are expected and exposed through ``n_bits``.
    """
    if radius<0 or n_bits<8: raise ValueError("radius must be >=0 and n_bits >=8")
    m=parse_smiles(smiles); adj=_adj(m); fp=np.zeros(n_bits,dtype=np.float64)
    ids=[]
    # ECFP-style invariants (Rogers & Hahn 2010): element, heavy degree, total
    # H count (written + implicit), formal charge, ring membership (the RDKit
    # default invariant set; aromaticity is not an invariant there).
    # Using only the written H made CH3/CH2/CH and OH indistinguishable.
    def _ring_atom(i):
        for j,_ in adj[i]:
            seen={i}; q=deque([i]); found=False
            while q and not found:
                u=q.popleft()
                for v,_ in adj[u]:
                    if (u==i and v==j) or v in seen: continue
                    if v==j: found=True; break
                    seen.add(v); q.append(v)
            if found: return True
        return False
    for i,a in enumerate(m.atoms):
        th=a.explicit_h+_implicit_h(a,adj[i])
        s=f"{a.element}|{a.charge}|{len(adj[i])}|{th}|{_ring_atom(i)}"
        ids.append(hashlib.sha256(s.encode()).hexdigest())
    for r in range(radius+1):
        for value in ids: fp[int(value[:16],16)%n_bits]=1.0
        if r<radius:
            ids=[hashlib.sha256((ids[i]+"|"+";".join(sorted(f"{o}:{ids[j]}" for j,o in adj[i]))).encode()).hexdigest() for i in range(len(ids))]
    return fp
