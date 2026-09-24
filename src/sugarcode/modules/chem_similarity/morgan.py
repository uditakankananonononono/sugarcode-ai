"""Morgan / ECFP-style circular fingerprints, bit-compatible with RDKit.

Re-implements RDKit's MorganGenerator (Release_2024_09_6,
Code/GraphMol/Fingerprints/MorganGenerator.cpp + FingerprintUtil.cpp
getConnectivityInvariants) with RDKit's 32-bit boost-style hash
(Code/RDGeneral/hash/hash.hpp). Algorithm: Rogers & Hahn 2010, J Chem Inf Model
50:742 (doi 10.1021/ci100050t).

Atom invariant (ECFP): hash of [atomic number, total degree incl. H, total H,
formal charge, int(mass - average atomic weight), 1 if in a ring]. Each round
hashes (round, own invariant, sorted (bond type, neighbour invariant) pairs);
environments whose bond set was already seen are dropped (RDKit's default
includeRedundantEnvironments=False). Chirality is not used (RDKit default).
"""
from __future__ import annotations

from collections import Counter

from sugarcode.modules.chem_descriptors.descriptors import ISOTOPES
from sugarcode.modules.chem_descriptors.smiles import ELEMENTS, Molecule, parse_smiles

M32 = 0xFFFFFFFF
# RDKit Bond::BondType enum values
_BOND_TYPE = {1.0: 1, 2.0: 2, 3.0: 3, 4.0: 4}
AROMATIC_BOND = 12


def _u32(v: int) -> int:
    return v & M32


def hash_combine(seed: int, value: int) -> int:
    """boost::hash_combine on 32-bit seeds; ``value`` is already the element hash."""
    return (seed ^ _u32(value + 0x9E3779B9 + (seed << 6) + (seed >> 2))) & M32


def hash_pair(a: int, b: int) -> int:
    return hash_combine(hash_combine(0, _u32(a)), _u32(b))


def hash_vector(values) -> int:
    seed = 0
    for v in values:
        seed = hash_combine(seed, _u32(v))
    return seed


def _bond_invariant(bd) -> int:
    return AROMATIC_BOND if bd.aromatic else _BOND_TYPE[bd.order]


def atom_invariants(mol: Molecule, include_ring_membership: bool = True) -> list[int]:
    ring_atoms = set()
    for bd in mol.bonds:
        if bd.ring:
            ring_atoms |= {bd.a, bd.b}
    inv = []
    for i, at in enumerate(mol.atoms):
        el = ELEMENTS[at.symbol]
        if at.isotope is not None:
            iso = ISOTOPES.get(at.symbol, {}).get(str(at.isotope))
            mass = iso if iso is not None else float(at.isotope)
        else:
            mass = el["average_mass"]
        delta = int(mass - el["average_mass"])        # C++ truncation toward zero
        # RDKit getTotalNumHs(includeNeighbors=True): explicit H atoms count too
        h_all = at.total_h + sum(1 for j, _ in mol.neighbors(i) if mol.atoms[j].symbol == "H")
        comps = [at.Z, mol.degree(i) + at.total_h, h_all, at.charge, delta]
        if include_ring_membership and i in ring_atoms:
            comps.append(1)
        inv.append(hash_vector(comps))
    return inv


def morgan_environments(mol: Molecule, radius: int = 2, use_bond_types: bool = True):
    """List of (code, atom_index, layer) exactly as RDKit's generator emits them."""
    n = len(mol.atoms)
    nbrs = [[] for _ in range(n)]
    for k, bd in enumerate(mol.bonds):
        nbrs[bd.a].append((bd.b, k))
        nbrs[bd.b].append((bd.a, k))
    bond_inv = [(_bond_invariant(bd) if use_bond_types else 1) for bd in mol.bonds]
    cur = atom_invariants(mol)
    out = [(cur[i], i, 0) for i in range(n)]
    atom_nb = [frozenset() for _ in range(n)]
    dead = [False] * n
    seen = set()
    for layer in range(radius):
        nxt = [0] * n
        round_nb = list(atom_nb)
        this_round = []
        for i in range(n):
            if dead[i]:
                continue
            if not nbrs[i]:
                dead[i] = True
                continue
            env = set(round_nb[i])
            pairs = []
            for j, k in nbrs[i]:
                env.add(k)
                env |= atom_nb[j]
                pairs.append((bond_inv[k], cur[j]))
            round_nb[i] = frozenset(env)
            pairs.sort()
            invar = layer
            invar = hash_combine(invar, cur[i])
            for bt, ci in pairs:
                invar = hash_combine(invar, hash_pair(bt, ci))
            nxt[i] = invar
            this_round.append((round_nb[i], invar, i))
        # RDKit sorts (bitset, code, atom); among equal bond sets the smallest
        # (code, atom) is kept, the rest are dead.
        this_round.sort(key=lambda t: (t[1], t[2]))
        for env, code, i in this_round:
            if env not in seen:
                out.append((code, i, layer + 1))
                seen.add(env)
            else:
                dead[i] = True
        cur = nxt
        atom_nb = round_nb
    return out


def _mol(x) -> Molecule:
    return parse_smiles(x) if isinstance(x, str) else x


def morgan_counts(smiles_or_mol, radius: int = 2, use_bond_types: bool = True) -> dict[int, int]:
    """Unfolded count fingerprint {32-bit code: count} (RDKit GetMorganFingerprint)."""
    envs = morgan_environments(_mol(smiles_or_mol), radius, use_bond_types)
    return dict(Counter(code for code, _, _ in envs))


def morgan_bits(smiles_or_mol, radius: int = 2, n_bits: int = 2048,
                use_bond_types: bool = True) -> frozenset[int]:
    """Folded bit fingerprint: set of on-bit indices, code % n_bits
    (RDKit GetMorganFingerprintAsBitVect / MorganGenerator fpSize)."""
    return frozenset(c % n_bits for c in morgan_counts(smiles_or_mol, radius, use_bond_types))


def morgan_bit_info(smiles_or_mol, radius: int = 2, n_bits: int = 2048) -> dict[int, list]:
    """bit -> [(atom index, radius), ...] like RDKit's bitInfo."""
    info: dict[int, list] = {}
    for code, i, layer in morgan_environments(_mol(smiles_or_mol), radius):
        info.setdefault(code % n_bits, []).append((i, layer))
    return info
