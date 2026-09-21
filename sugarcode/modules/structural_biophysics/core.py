"""Coordinate-based structural biophysics utilities.

The algorithms are deterministic and dependency-light. They are suitable for
screening and prioritisation, not a substitute for explicit-solvent free-energy
calculations or experimental affinity measurements.
"""
from __future__ import annotations

from dataclasses import dataclass
from math import cos, pi, sin, sqrt
from typing import Iterable, Mapping, Sequence
import numpy as np


class StructureInputError(ValueError):
    """Raised when a coordinate input cannot support the requested analysis."""


@dataclass(frozen=True)
class Atom:
    serial: int
    name: str
    residue: str
    chain: str
    residue_number: int
    insertion_code: str
    element: str
    xyz: tuple[float, float, float]
    record: str = "ATOM"
    altloc: str = ""
    occupancy: float = 1.0

    @property
    def residue_id(self) -> str:
        return f"{self.chain or '_'}:{self.residue}{self.residue_number}{self.insertion_code}"


# Bondi/commonly used united radii (A); unknown elements remain explicit.
VDW_RADII = {"H": 1.20, "C": 1.70, "N": 1.55, "O": 1.52, "F": 1.47,
             "P": 1.80, "S": 1.80, "CL": 1.75, "BR": 1.85, "I": 1.98,
             "MG": 1.73, "ZN": 1.39, "FE": 1.56, "CA": 1.94}
HYDROPHOBIC_ELEMENTS = {"C", "S", "F", "CL", "BR", "I"}
DONOR_ELEMENTS = {"N", "O", "S"}
ACCEPTOR_ELEMENTS = {"N", "O", "S", "F", "CL", "BR", "I"}
POSITIVE_RESIDUES = {"ARG", "LYS", "HIS"}
NEGATIVE_RESIDUES = {"ASP", "GLU"}


def _element(name: str, field: str) -> str:
    e = field.strip().upper()
    if e:
        return e
    letters = "".join(c for c in name if c.isalpha()).upper()
    if not letters:
        return ""
    # PDB atom names such as CA are alpha carbon, not calcium, in ATOM records.
    return letters[0]


def parse_pdb(data: str | bytes, *, include_hetero: bool = True,
              include_hydrogen: bool = False, model: int = 1) -> list[Atom]:
    """Parse one PDB model, resolving alternate locations by occupancy.

    The parser preserves chain, insertion code and author residue numbering.
    Water is excluded. Malformed coordinate records are counted and reported if
    no usable atoms remain rather than being silently fabricated.
    """
    if isinstance(data, bytes):
        data = data.decode("utf-8", errors="replace")
    selected: dict[tuple[str, int, str, str, str], Atom] = {}
    current_model, explicit_models, malformed = 1, False, 0
    for line in data.splitlines():
        rec = line[0:6].strip().upper()
        if rec == "MODEL":
            explicit_models = True
            try: current_model = int(line[10:14].strip())
            except ValueError: current_model += 1
            continue
        if rec == "ENDMDL" and explicit_models and current_model == model:
            break
        if explicit_models and current_model != model:
            continue
        if rec not in {"ATOM", "HETATM"} or (rec == "HETATM" and not include_hetero):
            continue
        if len(line) < 54:
            malformed += 1; continue
        residue = line[17:20].strip().upper()
        if residue in {"HOH", "WAT", "DOD"}:
            continue
        try:
            atom = Atom(
                serial=int(line[6:11].strip() or 0), name=line[12:16].strip(),
                altloc=line[16:17].strip(), residue=residue,
                chain=line[21:22].strip(), residue_number=int(line[22:26]),
                insertion_code=line[26:27].strip(),
                xyz=(float(line[30:38]), float(line[38:46]), float(line[46:54])),
                occupancy=float(line[54:60].strip() or 1.0),
                element=_element(line[12:16], line[76:78] if len(line) >= 78 else ""),
                record=rec)
        except ValueError:
            malformed += 1; continue
        if not include_hydrogen and atom.element in {"H", "D"}:
            continue
        key = (atom.chain, atom.residue_number, atom.insertion_code, atom.residue, atom.name)
        old = selected.get(key)
        # blank/A conformers are preferred only when occupancy does not decide.
        if old is None or atom.occupancy > old.occupancy or (
                atom.occupancy == old.occupancy and atom.altloc in {"", "A"} and old.altloc not in {"", "A"}):
            selected[key] = atom
    atoms = list(selected.values())
    if not atoms:
        suffix = f" ({malformed} malformed coordinate records)" if malformed else ""
        raise StructureInputError(f"no usable atoms in PDB model {model}{suffix}")
    return atoms


def _coords(atoms: Sequence[Atom]) -> np.ndarray:
    return np.asarray([a.xyz for a in atoms], dtype=float)


def _fibonacci_sphere(n: int) -> np.ndarray:
    i = np.arange(n, dtype=float)
    z = 1.0 - 2.0 * (i + 0.5) / n
    theta = pi * (3.0 - sqrt(5.0)) * i
    r = np.sqrt(np.maximum(0.0, 1.0 - z*z))
    return np.column_stack((r*np.cos(theta), r*np.sin(theta), z))


def shrake_rupley(atoms: Sequence[Atom], *, probe_radius: float = 1.4,
                   sphere_points: int = 960) -> dict:
    """Compute atomic and residue SASA with Shrake-Rupley point sampling."""
    if not atoms: raise StructureInputError("SASA requires at least one atom")
    if probe_radius <= 0 or not (60 <= sphere_points <= 10000):
        raise StructureInputError("probe_radius must be positive and sphere_points 60..10000")
    unknown = sorted({a.element for a in atoms if a.element not in VDW_RADII})
    radii = np.array([VDW_RADII.get(a.element, 1.70) + probe_radius for a in atoms])
    xyz, unit = _coords(atoms), _fibonacci_sphere(sphere_points)
    areas: list[float] = []
    for i, (center, radius) in enumerate(zip(xyz, radii)):
        points = center + unit * radius
        accessible = np.ones(sphere_points, dtype=bool)
        # Candidate pruning avoids allocating atom x point x atom cubes.
        center_dist = np.linalg.norm(xyz - center, axis=1)
        candidates = np.where((np.arange(len(atoms)) != i) & (center_dist < radius + radii))[0]
        for j in candidates:
            accessible &= np.sum((points - xyz[j])**2, axis=1) >= radii[j]**2
            if not accessible.any(): break
        areas.append(float(accessible.sum() / sphere_points * 4.0 * pi * radius**2))
    residue: dict[str, float] = {}
    for atom, area in zip(atoms, areas): residue[atom.residue_id] = residue.get(atom.residue_id, 0.0) + area
    return {"total_A2": round(sum(areas), 3), "atom_A2": [round(x, 3) for x in areas],
            "residue_A2": {k: round(v, 3) for k, v in residue.items()},
            "probe_radius_A": probe_radius, "sphere_points": sphere_points,
            "unknown_elements_defaulted_to_carbon_radius": unknown,
            "method": "Shrake-Rupley numerical surface sampling"}


VINA_WEIGHTS = {"gauss1": -0.035579, "gauss2": -0.005156,
                "repulsion": 0.840245, "hydrophobic": -0.035069,
                "hydrogen_bond": -0.587439, "rotors": 0.05846}


def _surface_distance(a: Atom, b: Atom, distance: float) -> float:
    return distance - VDW_RADII.get(a.element, 1.7) - VDW_RADII.get(b.element, 1.7)


def vina_score(receptor: Sequence[Atom], ligand: Sequence[Atom], *,
               rotatable_bonds: int = 0, cutoff_A: float = 8.0) -> dict:
    """Evaluate the AutoDock Vina 1.1 empirical functional form on a fixed pose.

    Atom typing uses element-level donor/acceptor and hydrophobe approximations,
    because PDB coordinates do not encode bond order or protonation. The result
    must therefore be labelled an approximate Vina-form score, not a Vina run.
    """
    if not receptor or not ligand: raise StructureInputError("receptor and ligand atoms are required")
    if rotatable_bonds < 0: raise StructureInputError("rotatable_bonds cannot be negative")
    rc, lc = _coords(receptor), _coords(ligand)
    terms = {k: 0.0 for k in VINA_WEIGHTS}
    contacts = clashes = hbonds = 0
    for i, a in enumerate(receptor):
        ds = np.linalg.norm(lc - rc[i], axis=1)
        for b, d in zip(ligand, ds):
            if d > cutoff_A: continue
            s = _surface_distance(a, b, float(d)); contacts += 1
            terms["gauss1"] += np.exp(-(s / 0.5)**2)
            terms["gauss2"] += np.exp(-((s - 3.0) / 2.0)**2)
            terms["repulsion"] += max(0.0, -s)**2
            if a.element in HYDROPHOBIC_ELEMENTS and b.element in HYDROPHOBIC_ELEMENTS:
                terms["hydrophobic"] += 1.0 if s <= 0.5 else max(0.0, 1.5 - s)
            donor_acceptor = ((a.element in DONOR_ELEMENTS and b.element in ACCEPTOR_ELEMENTS) or
                              (b.element in DONOR_ELEMENTS and a.element in ACCEPTOR_ELEMENTS))
            if donor_acceptor:
                h = 1.0 if s <= -0.7 else max(0.0, -s / 0.7)
                terms["hydrogen_bond"] += h
                hbonds += int(h > 0)
            clashes += int(s < -0.5)
    terms["rotors"] = float(rotatable_bonds)
    weighted = {k: terms[k] * VINA_WEIGHTS[k] for k in terms}
    return {"score_kcal_mol": round(sum(weighted.values()), 4),
            "raw_terms": {k: round(v, 5) for k, v in terms.items()},
            "weighted_terms_kcal_mol": {k: round(v, 5) for k, v in weighted.items()},
            "pair_contacts_within_cutoff": contacts, "steric_clashes": clashes,
            "putative_hydrogen_bonds": hbonds, "cutoff_A": cutoff_A,
            "weights": dict(VINA_WEIGHTS),
            "method": "Trott-Olson 2010 / AutoDock Vina 1.1 functional form on a fixed pose",
            "limitations": ["element-level atom typing; bond order and protonation are Missing",
                            "no pose search, receptor flexibility, solvation, entropy, or calibration",
                            "score is a ranking feature, not a measured binding free energy"]}


def analyze_interface(atoms: Sequence[Atom], chain_a: str, chain_b: str, *,
                      probe_radius: float = 1.4, sphere_points: int = 960,
                      contact_cutoff_A: float = 5.0) -> dict:
    """Analyze a two-chain protein interface from coordinates and buried SASA."""
    if chain_a == chain_b: raise StructureInputError("chain_a and chain_b must differ")
    a = [x for x in atoms if x.chain == chain_a and x.record == "ATOM"]
    b = [x for x in atoms if x.chain == chain_b and x.record == "ATOM"]
    if not a or not b: raise StructureInputError(f"missing protein atoms for chain {chain_a if not a else chain_b}")
    sa = shrake_rupley(a, probe_radius=probe_radius, sphere_points=sphere_points)
    sb = shrake_rupley(b, probe_radius=probe_radius, sphere_points=sphere_points)
    sc = shrake_rupley(a+b, probe_radius=probe_radius, sphere_points=sphere_points)
    buried = max(0.0, sa["total_A2"] + sb["total_A2"] - sc["total_A2"])
    complex_res = sc["residue_A2"]
    delta: dict[str, float] = {}
    for rid, area in {**sa["residue_A2"], **sb["residue_A2"]}.items():
        delta[rid] = max(0.0, area - complex_res.get(rid, 0.0))
    ac, bc = _coords(a), _coords(b)
    distances = np.linalg.norm(ac[:, None, :] - bc[None, :, :], axis=2)
    pairs = np.argwhere(distances <= contact_cutoff_A)
    residue_contacts = sorted({(a[i].residue_id, b[j].residue_id) for i, j in pairs})
    salt = sorted({(a[i].residue_id, b[j].residue_id) for i, j in np.argwhere(distances <= 4.0)
                   if ((a[i].residue in POSITIVE_RESIDUES and b[j].residue in NEGATIVE_RESIDUES) or
                       (a[i].residue in NEGATIVE_RESIDUES and b[j].residue in POSITIVE_RESIDUES))})
    interface_res = [{"residue_id": rid, "buried_A2": round(v, 3)} for rid, v in delta.items() if v >= 1.0]
    interface_res.sort(key=lambda x: x["buried_A2"], reverse=True)
    return {"chains": [chain_a, chain_b], "buried_surface_area_A2": round(buried, 3),
            "buried_area_per_partner_A2": round(buried / 2.0, 3),
            "interface_residues": interface_res,
            "residue_contact_pairs": [list(x) for x in residue_contacts],
            "atom_contacts": int(len(pairs)), "putative_salt_bridges": [list(x) for x in salt],
            "contact_cutoff_A": contact_cutoff_A, "sasa": {"chain_a_A2": sa["total_A2"],
            "chain_b_A2": sb["total_A2"], "complex_A2": sc["total_A2"],
            "probe_radius_A": probe_radius, "sphere_points": sphere_points},
            "method": "Shrake-Rupley ΔSASA plus heavy-atom distance contacts",
            "limitations": ["hydrogens, protonation, crystal contacts, and biological assembly validity are not inferred",
                            "salt bridges are residue/geometry candidates, not electrostatic energies"]}


def alanine_interface_scan(atoms: Sequence[Atom], chain_a: str, chain_b: str, *,
                            contact_cutoff_A: float = 5.0) -> dict:
    """Prioritise interface hotspots by loss of fixed-pose inter-chain contacts.

    Each residue is reduced in silico to backbone+CB, and the removed pairwise
    Vina-form weighted contribution is reported. Coordinates are not rebuilt.
    """
    a = [x for x in atoms if x.chain == chain_a and x.record == "ATOM"]
    b = [x for x in atoms if x.chain == chain_b and x.record == "ATOM"]
    if not a or not b: raise StructureInputError("both protein chains are required")
    results = []
    for own, other in ((a, b), (b, a)):
        by_res: dict[str, list[Atom]] = {}
        for atom in own: by_res.setdefault(atom.residue_id, []).append(atom)
        for rid, residue_atoms in by_res.items():
            removed = [x for x in residue_atoms if x.name not in {"N", "CA", "C", "O", "OXT", "CB"}]
            if not removed: continue
            score = vina_score(other, removed, cutoff_A=contact_cutoff_A)
            contact_count = score["pair_contacts_within_cutoff"]
            if contact_count:
                # More negative removed contribution suggests a stronger lost contact network.
                results.append({"residue_id": rid, "residue": residue_atoms[0].residue,
                                "removed_sidechain_atoms": len(removed), "cross_interface_contacts": contact_count,
                                "removed_contact_score_kcal_mol": score["score_kcal_mol"],
                                "hotspot_priority": round(max(0.0, -score["score_kcal_mol"]), 4)})
    results.sort(key=lambda x: (x["hotspot_priority"], x["cross_interface_contacts"]), reverse=True)
    return {"chains": [chain_a, chain_b], "candidates": results,
            "method": "fixed-coordinate computational alanine contact deletion scan",
            "limitations": ["side-chain and backbone relaxation are Missing", "desolvation and conformational entropy are Missing",
                            "priorities require experimental or higher-fidelity validation"]}
