"""SMILES parser (OpenSMILES subset) to a hydrogen-suppressed molecular graph.

Supported: organic-subset atoms (B C N O P S F Cl Br I, aromatic b c n o p s),
bracket atoms [isotope symbol chirality Hcount charge :class] for any element in
the vendored periodic table (aromatic b c n o p s se as te), bonds - = # $ : / \\,
branches, ring closures (single digit and %nn, with bond order on either end),
dot-disconnected components.

Parsed but ignored (reported in ``Molecule.ignored``): tetrahedral / extended
chirality (@, @@, @TH1...), cis/trans bond direction (/ and \\), atom classes.

Not supported (raise ``SmilesError``): the '*' wildcard, reaction SMILES ('>'),
SMARTS syntax. Kekule rings ARE re-aromatised after hydrogen assignment by a
Hueckel 4n+2 rule over each minimum-cycle-basis ring and over pairs of fused
rings (see ``_perceive_aromaticity``); lowercase aromatic input is trusted as
written and invalid aromatic systems are not detected. Larger fused systems
that are only aromatic as a 3+ ring whole, and B/Se/Te/As donors in Kekule
form, are not perceived. Implicit hydrogens
on aromatic organic-subset atoms use the OpenSMILES rule (lowest normal valence
minus bond count minus one, floor 0), so pyrrole-type nitrogens must be written
[nH] as the standard requires. Bracket [H] atoms bonded to exactly one heavy atom
(no isotope, charge or class) are folded into that atom's hydrogen count;
isotopic hydrogens ([2H], [3H]) stay explicit atoms.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path

_TABLE = json.loads((Path(__file__).parent / "data" / "periodic_table.json").read_text())
ELEMENTS: dict = _TABLE["elements"]

ORGANIC = {"B", "C", "N", "O", "P", "S", "F", "Cl", "Br", "I"}
AROMATIC_ORGANIC = {"b", "c", "n", "o", "p", "s"}
AROMATIC_BRACKET = {"b", "c", "n", "o", "p", "s", "se", "as", "te"}
# lowest-first normal valences for organic-subset implicit H (OpenSMILES 3.1.5)
ORGANIC_VALENCES = {"B": [3], "C": [4], "N": [3, 5], "O": [2], "P": [3, 5],
                    "S": [2, 4, 6], "F": [1], "Cl": [1], "Br": [1], "I": [1]}
BOND_ORDER = {"-": 1.0, "=": 2.0, "#": 3.0, "$": 4.0, ":": 1.5, "/": 1.0, "\\": 1.0}

_BRACKET = re.compile(
    r"^(?P<iso>\d+)?(?P<sym>[A-Z][a-z]?|se|as|te|[bcnops])"
    r"(?P<chir>@@|@(?:TH[12]|AL[12]|SP[123]|TB\d{1,2}|OH\d{1,2})?)?"
    r"(?P<h>H\d*)?(?P<chg>\+\+|--|[+-]\d*)?(?P<cls>:\d+)?$")


class SmilesError(ValueError):
    pass


@dataclass
class Atom:
    symbol: str                 # element symbol, capitalised (e.g. "C", "Cl", "Se")
    aromatic: bool = False
    isotope: int | None = None
    charge: int = 0
    bracket: bool = False
    explicit_h: int = 0         # bracket H count
    implicit_h: int = 0
    chirality: str | None = None

    @property
    def total_h(self) -> int:
        return self.explicit_h + self.implicit_h

    @property
    def Z(self) -> int:
        return ELEMENTS[self.symbol]["Z"]


@dataclass
class Bond:
    a: int
    b: int
    order: float                # 1, 2, 3, 4 or 1.5 (aromatic)
    aromatic: bool = False
    ring: bool = False
    direction: str | None = None

    def other(self, i: int) -> int:
        return self.b if i == self.a else self.a


@dataclass
class Molecule:
    smiles: str
    atoms: list = field(default_factory=list)
    bonds: list = field(default_factory=list)
    ignored: list = field(default_factory=list)

    def neighbors(self, i: int):
        return [(bd.other(i), bd) for bd in self.bonds if bd.a == i or bd.b == i]

    def degree(self, i: int) -> int:
        return sum(1 for bd in self.bonds if bd.a == i or bd.b == i)

    def bond_between(self, i: int, j: int):
        for bd in self.bonds:
            if {bd.a, bd.b} == {i, j}:
                return bd
        return None


def _parse_bracket(body: str) -> Atom:
    m = _BRACKET.match(body)
    if not m:
        raise SmilesError(f"unsupported bracket atom [{body}]")
    sym = m.group("sym")
    aromatic = sym.islower()
    if aromatic and sym not in AROMATIC_BRACKET:
        raise SmilesError(f"unsupported aromatic symbol {sym!r}")
    element = sym.capitalize()
    if element not in ELEMENTS:
        raise SmilesError(f"unknown element {element!r}")
    h = m.group("h")
    hcount = 0 if h is None else (1 if h == "H" else int(h[1:]))
    chg = m.group("chg")
    if chg is None:
        charge = 0
    elif chg in ("++", "--"):
        charge = 2 if chg == "++" else -2
    else:
        charge = (1 if chg[0] == "+" else -1) * (int(chg[1:]) if len(chg) > 1 else 1)
    iso = int(m.group("iso")) if m.group("iso") else None
    return Atom(element, aromatic, iso, charge, True, hcount, 0, m.group("chir"))


def parse_smiles(smiles: str) -> Molecule:
    s = smiles.strip()
    if not s:
        raise SmilesError("empty SMILES")
    if ">" in s:
        raise SmilesError("reaction SMILES are not supported")
    mol = Molecule(s)
    prev: int | None = None
    pending_bond: str | None = None
    branch_stack: list[int | None] = []
    ring_open: dict[int, tuple[int, str | None]] = {}
    i = 0

    def add_atom(atom: Atom):
        nonlocal prev, pending_bond
        mol.atoms.append(atom)
        idx = len(mol.atoms) - 1
        if prev is not None:
            _add_bond(mol, prev, idx, pending_bond)
        elif pending_bond is not None:
            raise SmilesError("bond symbol with no preceding atom")
        prev, pending_bond = idx, None

    while i < len(s):
        ch = s[i]
        if ch == "[":
            j = s.find("]", i)
            if j < 0:
                raise SmilesError("unclosed bracket atom")
            add_atom(_parse_bracket(s[i + 1:j]))
            i = j + 1
        elif s.startswith("Cl", i) or s.startswith("Br", i):
            add_atom(Atom(s[i:i + 2]))
            i += 2
        elif ch in "BCNOPSFI":
            add_atom(Atom(ch))
            i += 1
        elif ch in AROMATIC_ORGANIC:
            add_atom(Atom(ch.upper(), aromatic=True))
            i += 1
        elif ch == "*":
            raise SmilesError("the '*' wildcard atom is not supported")
        elif ch in BOND_ORDER:
            if pending_bond is not None:
                raise SmilesError(f"two bond symbols in a row at position {i}")
            pending_bond = ch
            i += 1
        elif ch == "(":
            if prev is None:
                raise SmilesError("branch with no preceding atom")
            branch_stack.append(prev)
            i += 1
        elif ch == ")":
            if not branch_stack:
                raise SmilesError("unbalanced ')'")
            if pending_bond is not None:
                raise SmilesError("dangling bond before ')'")
            prev = branch_stack.pop()
            i += 1
        elif ch.isdigit() or ch == "%":
            if ch == "%":
                if not s[i + 1:i + 3].isdigit() or len(s[i + 1:i + 3]) != 2:
                    raise SmilesError("ring closure % must be followed by two digits")
                num, i = int(s[i + 1:i + 3]), i + 3
            else:
                num, i = int(ch), i + 1
            if prev is None:
                raise SmilesError("ring closure with no preceding atom")
            if num in ring_open:
                start, bsym = ring_open.pop(num)
                if bsym and pending_bond and BOND_ORDER[bsym] != BOND_ORDER[pending_bond]:
                    raise SmilesError(f"conflicting bond orders on ring closure {num}")
                if start == prev:
                    raise SmilesError("ring closure to the same atom")
                _add_bond(mol, start, prev, pending_bond or bsym, ring_closure=True)
            else:
                ring_open[num] = (prev, pending_bond)
            pending_bond = None
        elif ch == ".":
            if pending_bond is not None:
                raise SmilesError("bond symbol before '.'")
            prev = None
            i += 1
        else:
            raise SmilesError(f"unexpected character {ch!r} at position {i}")
    if ring_open:
        raise SmilesError(f"unclosed ring bond(s) {sorted(ring_open)}")
    if branch_stack:
        raise SmilesError("unbalanced '('")
    if pending_bond is not None:
        raise SmilesError("SMILES ends with a bond symbol")
    _fold_hydrogens(mol)
    _mark_ring_bonds(mol)
    _finalise_aromatic_bonds(mol)
    _implicit_hydrogens(mol)
    _perceive_aromaticity(mol)
    if any(a.chirality for a in mol.atoms):
        mol.ignored.append("chirality")
    if any(b.direction for b in mol.bonds):
        mol.ignored.append("cis/trans bond direction")
    return mol


def _add_bond(mol: Molecule, a: int, b: int, sym: str | None, ring_closure: bool = False):
    if mol.bond_between(a, b):
        raise SmilesError(f"duplicate bond between atoms {a} and {b}")
    if sym is None:
        both_arom = mol.atoms[a].aromatic and mol.atoms[b].aromatic
        bd = Bond(a, b, 1.5 if both_arom else 1.0, aromatic=both_arom)
        bd._implicit = True
    else:
        bd = Bond(a, b, BOND_ORDER[sym], aromatic=(sym == ":"),
                  direction=sym if sym in "/\\" else None)
        bd._implicit = False
    mol.bonds.append(bd)


def _fold_hydrogens(mol: Molecule):
    drop = []
    for i, at in enumerate(mol.atoms):
        if at.symbol == "H" and at.bracket and at.isotope is None and at.charge == 0 \
                and at.explicit_h == 0:
            nb = mol.neighbors(i)
            if len(nb) == 1 and mol.atoms[nb[0][0]].symbol != "H" and nb[0][1].order == 1.0:
                mol.atoms[nb[0][0]].explicit_h += 1
                drop.append(i)
    if not drop:
        return
    keep = [i for i in range(len(mol.atoms)) if i not in set(drop)]
    remap = {old: new for new, old in enumerate(keep)}
    mol.atoms = [mol.atoms[i] for i in keep]
    bonds = []
    for bd in mol.bonds:
        if bd.a in remap and bd.b in remap:
            bd.a, bd.b = remap[bd.a], remap[bd.b]
            bonds.append(bd)
    mol.bonds = bonds


def _mark_ring_bonds(mol: Molecule):
    """A bond is a ring bond iff removing it leaves its ends connected."""
    n = len(mol.atoms)
    adj = {i: set() for i in range(n)}
    for k, bd in enumerate(mol.bonds):
        adj[bd.a].add((bd.b, k))
        adj[bd.b].add((bd.a, k))
    for k, bd in enumerate(mol.bonds):
        seen, stack = {bd.a}, [bd.a]
        while stack:
            u = stack.pop()
            for v, kk in adj[u]:
                if kk != k and v not in seen:
                    seen.add(v)
                    stack.append(v)
        bd.ring = bd.b in seen


def _finalise_aromatic_bonds(mol: Molecule):
    # an implicit bond between two aromatic atoms outside any ring is single
    for bd in mol.bonds:
        if bd.aromatic and getattr(bd, "_implicit", False) and not bd.ring:
            bd.aromatic, bd.order = False, 1.0


def _implicit_hydrogens(mol: Molecule):
    for i, at in enumerate(mol.atoms):
        if at.bracket or at.symbol not in ORGANIC:
            continue
        bonds = [bd for _, bd in mol.neighbors(i)]
        vals = ORGANIC_VALENCES[at.symbol]
        if at.aromatic:
            used = sum(1 if bd.aromatic else bd.order for bd in bonds)
            at.implicit_h = max(0, int(vals[0] - used - 1))
        else:
            used = sum(1 if bd.aromatic else bd.order for bd in bonds)
            target = next((v for v in vals if v >= used), None)
            at.implicit_h = int(target - used) if target is not None else 0


_EN_EXO = {"O", "N", "S"}


def _pi_electrons(mol: Molecule, i: int):
    """Electrons atom i donates to a ring pi system (RDKit-style model), or None
    when the atom cannot be part of an aromatic ring."""
    at = mol.atoms[i]
    if at.symbol not in ("C", "N", "O", "S", "P") :
        return None
    nbrs = mol.neighbors(i)
    doubles = [(j, bd) for j, bd in nbrs if bd.order == 2.0]
    if any(bd.order >= 3.0 for _, bd in nbrs) or len(doubles) > 1:
        return None
    heavy_deg = len(nbrs)
    if doubles:
        j, bd = doubles[0]
        if bd.ring:
            return 1
        if at.symbol == "C" and mol.atoms[j].symbol in _EN_EXO:
            return 0            # exocyclic C=O / C=N / C=S (e.g. 2-pyridone)
        return None
    if at.symbol == "C":
        if at.charge == -1 and heavy_deg + at.total_h == 3:
            return 2
        if at.charge == 1 and heavy_deg + at.total_h == 3:
            return 0
        return None
    if at.symbol in ("N", "P") and at.charge == 0 and heavy_deg + at.total_h == 3:
        return 2
    if at.symbol in ("O", "S") and at.charge == 0 and heavy_deg == 2:
        return 2
    return None


def _perceive_aromaticity(mol: Molecule):
    """Mark Kekule-written aromatic rings aromatic (Hueckel 4n+2)."""
    if not any(bd.order == 2.0 and bd.ring for bd in mol.bonds):
        return
    from .descriptors import minimum_cycle_basis   # local import avoids a cycle
    rings = []
    for cyc in minimum_cycle_basis(mol):
        atoms = set()
        for k in cyc:
            atoms |= {mol.bonds[k].a, mol.bonds[k].b}
        rings.append((frozenset(cyc), frozenset(atoms)))
    if not rings:
        return
    elec = {i: _pi_electrons(mol, i) for i in range(len(mol.atoms))}

    def huckel(atoms):
        if any(mol.atoms[i].aromatic for i in atoms):
            return False
        if any(elec[i] is None for i in atoms):
            return False
        n = sum(elec[i] for i in atoms)
        return n >= 2 and (n - 2) % 4 == 0

    aromatic_bonds = set()
    single_ok = [huckel(atoms) for _, atoms in rings]
    for (cyc, _), ok in zip(rings, single_ok):
        if ok:
            aromatic_bonds |= cyc
    for x in range(len(rings)):
        for y in range(x + 1, len(rings)):
            if single_ok[x] and single_ok[y]:
                continue
            if not (rings[x][0] & rings[y][0]):
                continue
            if huckel(rings[x][1] | rings[y][1]):
                aromatic_bonds |= rings[x][0] | rings[y][0]
    for k in aromatic_bonds:
        bd = mol.bonds[k]
        bd.aromatic, bd.order = True, 1.5
        mol.atoms[bd.a].aromatic = True
        mol.atoms[bd.b].aromatic = True
