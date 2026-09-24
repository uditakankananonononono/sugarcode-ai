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


# AutoDock Vina X-Score radii (src/lib/atom_constants.h, xs_vdw_radii) used for
# the Vina surface distance; they differ from the Bondi radii used for SASA.
XS_RADII = {"C": 1.9, "N": 1.8, "O": 1.7, "S": 2.0, "P": 2.1, "F": 1.5,
            "CL": 1.8, "BR": 2.0, "I": 2.2, "SI": 2.2,
            "MG": 1.2, "ZN": 1.2, "FE": 1.2, "CA": 1.2, "MN": 1.2}
# Vina hydrophobic types (xs_is_hydrophobic): C_H, F, Cl, Br, I. Sulfur is S_P
# (not hydrophobic); carbon bonded to N/O (C_P) cannot be told apart at the
# element level and is still counted, as the docstring states.
VINA_HYDROPHOBIC = {"C", "F", "CL", "BR", "I"}
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
            s = float(d) - XS_RADII.get(a.element, 1.9) - XS_RADII.get(b.element, 1.9); contacts += 1
            terms["gauss1"] += np.exp(-(s / 0.5)**2)
            terms["gauss2"] += np.exp(-((s - 3.0) / 2.0)**2)
            terms["repulsion"] += max(0.0, -s)**2
            if a.element in VINA_HYDROPHOBIC and b.element in VINA_HYDROPHOBIC:
                terms["hydrophobic"] += 1.0 if s <= 0.5 else max(0.0, 1.5 - s)
            donor_acceptor = ((a.element in DONOR_ELEMENTS and b.element in ACCEPTOR_ELEMENTS) or
                              (b.element in DONOR_ELEMENTS and a.element in ACCEPTOR_ELEMENTS))
            if donor_acceptor:
                h = 1.0 if s <= -0.7 else max(0.0, -s / 0.7)
                terms["hydrogen_bond"] += h
                hbonds += int(h > 0)
            clashes += int(s < -0.5)
    terms["rotors"] = float(rotatable_bonds)
    weighted = {k: terms[k] * VINA_WEIGHTS[k] for k in terms if k != "rotors"}
    inter = sum(weighted.values())
    # Vina divides the intermolecular energy by 1 + w_rot * N_rot
    # (conf_independent.cpp, num_tors_div); it is not an additive penalty.
    rot_factor = 1.0 + VINA_WEIGHTS["rotors"] * rotatable_bonds
    weighted["rotors"] = inter / rot_factor - inter
    return {"score_kcal_mol": round(inter / rot_factor, 4),
            "intermolecular_kcal_mol": round(inter, 4), "rotor_divisor": round(rot_factor, 5),
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


def _rotation_matrix(axis: np.ndarray, angle: float) -> np.ndarray:
    axis = np.asarray(axis, dtype=float)
    norm = np.linalg.norm(axis)
    if norm == 0: return np.eye(3)
    x, y, z = axis / norm; c, s, q = cos(angle), sin(angle), 1.0-cos(angle)
    return np.array([[c+x*x*q, x*y*q-z*s, x*z*q+y*s],
                     [y*x*q+z*s, c+y*y*q, y*z*q-x*s],
                     [z*x*q-y*s, z*y*q+x*s, c+z*z*q]])


def transform_atoms(atoms: Sequence[Atom], rotation: np.ndarray | None = None,
                    translation: Sequence[float] = (0.0, 0.0, 0.0),
                    center: Sequence[float] | None = None) -> list[Atom]:
    """Return atoms transformed rigidly without mutating the input."""
    if not atoms: return []
    rot = np.eye(3) if rotation is None else np.asarray(rotation, dtype=float)
    if rot.shape != (3, 3): raise StructureInputError("rotation must be 3x3")
    trans = np.asarray(translation, dtype=float)
    if trans.shape != (3,): raise StructureInputError("translation must have three values")
    xyz = _coords(atoms); pivot = xyz.mean(axis=0) if center is None else np.asarray(center, dtype=float)
    moved = (xyz-pivot) @ rot.T + pivot + trans
    return [Atom(**{**a.__dict__, "xyz": tuple(float(v) for v in p)}) for a, p in zip(atoms, moved)]


def vina_atom_contributions(receptor: Sequence[Atom], ligand: Sequence[Atom], *,
                            rotatable_bonds: int = 0, cutoff_A: float = 8.0) -> dict:
    """Decompose the fixed-pose score over receptor and ligand atoms.

    Pair terms are divided equally between the two participating atoms. The
    global rotor penalty is returned separately because assigning it to atoms
    would imply unsupported causality.
    """
    if not receptor or not ligand: raise StructureInputError("receptor and ligand atoms are required")
    rc, lc = _coords(receptor), _coords(ligand)
    rvalues = np.zeros(len(receptor)); lvalues = np.zeros(len(ligand))
    pair_rows = []
    for i, a in enumerate(receptor):
        for j, b in enumerate(ligand):
            d = float(np.linalg.norm(rc[i]-lc[j]))
            if d > cutoff_A: continue
            s = d - XS_RADII.get(a.element, 1.9) - XS_RADII.get(b.element, 1.9)
            raw = {"gauss1": np.exp(-(s/.5)**2), "gauss2": np.exp(-((s-3)/2)**2),
                   "repulsion": max(0.,-s)**2, "hydrophobic": 0., "hydrogen_bond": 0.}
            if a.element in VINA_HYDROPHOBIC and b.element in VINA_HYDROPHOBIC:
                raw["hydrophobic"] = 1. if s <= .5 else max(0.,1.5-s)
            if ((a.element in DONOR_ELEMENTS and b.element in ACCEPTOR_ELEMENTS) or
                (b.element in DONOR_ELEMENTS and a.element in ACCEPTOR_ELEMENTS)):
                raw["hydrogen_bond"] = 1. if s <= -.7 else max(0.,-s/.7)
            value = float(sum(raw[k]*VINA_WEIGHTS[k] for k in raw))
            rvalues[i] += value/2; lvalues[j] += value/2
            pair_rows.append((abs(value), {"receptor_atom": i, "ligand_atom": j,
                                          "distance_A": round(d,3), "contribution_kcal_mol": round(value,5)}))
    def rows(atoms, values):
        out = [{"atom_index": i, "serial": a.serial, "name": a.name,
                "residue_id": a.residue_id, "contribution_kcal_mol": round(float(v),5)}
               for i,(a,v) in enumerate(zip(atoms,values))]
        return sorted(out,key=lambda x: abs(x["contribution_kcal_mol"]),reverse=True)
    pair_sum = float(rvalues.sum()+lvalues.sum())
    total = pair_sum/(1.0+VINA_WEIGHTS["rotors"]*rotatable_bonds)  # Vina num_tors_div
    rotor = total-pair_sum
    pair_rows.sort(key=lambda x:x[0],reverse=True)
    return {"pair_score_kcal_mol": round(pair_sum,5), "global_rotor_penalty_kcal_mol": round(rotor,5),
            "total_score_kcal_mol": round(total,5),
            "receptor_atoms": rows(receptor,rvalues), "ligand_atoms": rows(ligand,lvalues),
            "strongest_pairs": [row for _,row in pair_rows[:50]],
            "accounting": "each pair contribution split equally across its two atoms; rotor penalty remains global"}


def refine_pose(receptor: Sequence[Atom], ligand: Sequence[Atom], *, rotatable_bonds: int = 0,
                translation_step_A: float = 1.0, rotation_step_degrees: float = 12.0,
                rounds: int = 5, max_displacement_A: float = 4.0) -> dict:
    """Deterministic rigid-body coordinate descent under the Vina-form score.

    Six translations and six rotations are tested per iteration, with step
    halving when no improvement occurs. Search is bounded around the input pose.
    It refines a plausible pose; it is intentionally not represented as global
    docking or flexible-ligand sampling.
    """
    if not receptor or not ligand: raise StructureInputError("receptor and ligand atoms are required")
    if rounds < 1 or rounds > 50 or translation_step_A <= 0 or rotation_step_degrees <= 0:
        raise StructureInputError("positive steps and rounds 1..50 required")
    origin = _coords(ligand); current = list(ligand)
    initial = vina_score(receptor,current,rotatable_bonds=rotatable_bonds)
    best_score = initial["score_kcal_mol"]; history = [best_score]
    tstep, astep = translation_step_A, rotation_step_degrees*pi/180
    axes = np.eye(3)
    accepted = 0
    for _ in range(rounds):
        candidates = []
        for axis in axes:
            for sign in (-1.,1.):
                candidates.append(transform_atoms(current,translation=axis*sign*tstep))
                candidates.append(transform_atoms(current,rotation=_rotation_matrix(axis,sign*astep)))
        valid=[]
        for cand in candidates:
            displacement=float(np.max(np.linalg.norm(_coords(cand)-origin,axis=1)))
            if displacement <= max_displacement_A:
                valid.append((vina_score(receptor,cand,rotatable_bonds=rotatable_bonds)["score_kcal_mol"],cand))
        if valid:
            candidate_score,candidate=min(valid,key=lambda x:x[0])
        else: candidate_score,candidate=best_score,current
        if candidate_score < best_score-1e-8:
            current,best_score=candidate,candidate_score; accepted+=1
        else:
            tstep/=2; astep/=2
        history.append(best_score)
    final = vina_score(receptor,current,rotatable_bonds=rotatable_bonds)
    displacement=np.linalg.norm(_coords(current)-origin,axis=1)
    return {"initial_score_kcal_mol": initial["score_kcal_mol"],
            "refined_score_kcal_mol": final["score_kcal_mol"],
            "score_improvement_kcal_mol": round(initial["score_kcal_mol"]-final["score_kcal_mol"],4),
            "accepted_moves": accepted, "score_history_kcal_mol": history,
            "max_atom_displacement_A": round(float(displacement.max()),4),
            "rms_atom_displacement_A": round(float(np.sqrt(np.mean(displacement**2))),4),
            "refined_ligand_xyz": [[round(v,5) for v in a.xyz] for a in current],
            "final_atom_contributions": vina_atom_contributions(receptor,current,rotatable_bonds=rotatable_bonds),
            "method": "bounded deterministic rigid-body coordinate descent under Vina-form score",
            "limitations": ["ligand torsions, receptor flexibility, protonation, and waters are Missing",
                            "local refinement only; no claim of globally optimal docked pose"]}

# Atomic solvation parameters in kcal mol-1 A-2. These Eisenberg-style
# element-class approximations are exposed so callers can audit/calibrate them.
DEFAULT_SOLVATION_PARAMETERS = {"C": 0.012, "S": 0.012, "F": 0.010, "CL": 0.010,
                                "BR": 0.010, "I": 0.010, "N": -0.010,
                                "O": -0.012, "P": -0.006, "H": 0.0}


def interface_desolvation(receptor: Sequence[Atom], partner: Sequence[Atom], *,
                          solvation_parameters: Mapping[str, float] | None = None,
                          probe_radius: float = 1.4, sphere_points: int = 960) -> dict:
    """Estimate desolvation from atom-wise SASA burial on complex formation.

    Positive values are an unfavorable cost from burying polar surface; negative
    values favor burial under the supplied convention. The default coefficients
    are intentionally simple element classes and not fitted affinity prediction.
    """
    if not receptor or not partner: raise StructureInputError("both partners are required")
    params = dict(DEFAULT_SOLVATION_PARAMETERS if solvation_parameters is None else solvation_parameters)
    for k,v in params.items():
        if not isinstance(v,(int,float)) or not np.isfinite(v):
            raise StructureInputError(f"invalid solvation parameter for {k}")
    isolated = shrake_rupley(list(receptor)+list(partner), probe_radius=probe_radius,
                             sphere_points=sphere_points)
    # In the concatenated isolated calculation partners can occlude each other;
    # calculate each partner separately to preserve true unbound SASA.
    ru = shrake_rupley(receptor,probe_radius=probe_radius,sphere_points=sphere_points)
    pu = shrake_rupley(partner,probe_radius=probe_radius,sphere_points=sphere_points)
    bound = isolated["atom_A2"]
    unbound = ru["atom_A2"] + pu["atom_A2"]
    atoms = list(receptor)+list(partner)
    atom_rows=[]; total=0.; unknown=set()
    for i,(a,u,b) in enumerate(zip(atoms,unbound,bound)):
        buried=max(0.,u-b)
        if a.element not in params: unknown.add(a.element)
        contribution=buried*params.get(a.element,0.)
        total+=contribution
        atom_rows.append({"atom_index":i,"serial":a.serial,"residue_id":a.residue_id,"name":a.name,
                          "element":a.element,"buried_A2":round(buried,3),
                          "desolvation_kcal_mol":round(contribution,5)})
    atom_rows.sort(key=lambda x:abs(x["desolvation_kcal_mol"]),reverse=True)
    return {"desolvation_kcal_mol":round(total,5),"total_buried_atomic_sasa_A2":round(sum(x["buried_A2"] for x in atom_rows),3),
            "atom_contributions":atom_rows,"solvation_parameters_kcal_mol_A2":params,
            "unknown_elements_assigned_zero":sorted(unknown),
            "method":"atom-wise Shrake-Rupley SASA burial times configurable element solvation parameters",
            "limitations":["unbound conformational relaxation and ordered waters are Missing",
                           "default element coefficients are screening approximations, not affinity-calibrated"]}


def _rotate_subset(atoms: Sequence[Atom], bond_a: int, bond_b: int,
                   moving_indices: Sequence[int], angle: float) -> list[Atom]:
    if not (0 <= bond_a < len(atoms) and 0 <= bond_b < len(atoms)) or bond_a == bond_b:
        raise StructureInputError("torsion bond indices out of range or identical")
    moving=set(moving_indices)
    if bond_a in moving or bond_b not in moving:
        raise StructureInputError("moving_indices must contain bond_b and exclude bond_a")
    xyz=_coords(atoms); pivot=xyz[bond_a]; axis=xyz[bond_b]-pivot
    if np.linalg.norm(axis)<1e-8: raise StructureInputError("torsion bond has zero length")
    rot=_rotation_matrix(axis,angle); new=xyz.copy()
    ids=np.array(sorted(moving),dtype=int)
    if len(ids) and (ids.min()<0 or ids.max()>=len(atoms)): raise StructureInputError("moving atom index out of range")
    new[ids]=(xyz[ids]-pivot)@rot.T+pivot
    return [Atom(**{**a.__dict__,"xyz":tuple(float(v) for v in p)}) for a,p in zip(atoms,new)]


def sample_ligand_torsions(receptor: Sequence[Atom], ligand: Sequence[Atom],
                           torsions: Sequence[Mapping[str, object]], *,
                           angles_degrees: Sequence[float] = (-120,-60,0,60,120,180),
                           beam_width: int = 20, rotatable_bonds: int | None = None) -> dict:
    """Sample user-defined ligand torsions with deterministic beam search.

    Each torsion requires zero-based ``bond=(fixed,moving)`` and
    ``moving_indices`` defining the downstream connected component. Requiring
    this topology prevents guessing bonds from distances or PDB atom order.
    """
    if not receptor or not ligand: raise StructureInputError("receptor and ligand atoms are required")
    if not torsions: raise StructureInputError("at least one explicit torsion is required")
    if not (1 <= beam_width <= 500): raise StructureInputError("beam_width must be 1..500")
    if not angles_degrees or any(not np.isfinite(x) for x in angles_degrees):
        raise StructureInputError("finite torsion angles are required")
    nrot=len(torsions) if rotatable_bonds is None else rotatable_bonds
    initial=vina_score(receptor,ligand,rotatable_bonds=nrot)
    beam=[(initial["score_kcal_mol"],list(ligand),[])]
    evaluated=0
    for t_idx,t in enumerate(torsions):
        try: a,b=t["bond"]  # type: ignore[misc]
        except (KeyError,TypeError,ValueError): raise StructureInputError(f"torsion {t_idx} needs bond=(fixed,moving)")
        moving=t.get("moving_indices")
        if not isinstance(moving,(list,tuple,set)): raise StructureInputError(f"torsion {t_idx} needs moving_indices")
        candidates=[]
        for _,pose,chosen in beam:
            for deg in angles_degrees:
                candidate=_rotate_subset(pose,int(a),int(b),moving,float(deg)*pi/180)
                score=vina_score(receptor,candidate,rotatable_bonds=nrot)["score_kcal_mol"]
                candidates.append((score,candidate,chosen+[float(deg)])); evaluated+=1
        candidates.sort(key=lambda x:(x[0],x[2]))
        beam=candidates[:beam_width]
    best_score,best,angles=beam[0]
    return {"initial_score_kcal_mol":initial["score_kcal_mol"],"best_score_kcal_mol":best_score,
            "score_improvement_kcal_mol":round(initial["score_kcal_mol"]-best_score,4),
            "selected_angles_degrees":angles,"conformers_evaluated":evaluated,"beam_width":beam_width,
            "best_ligand_xyz":[[round(v,5) for v in a.xyz] for a in best],
            "best_atom_contributions":vina_atom_contributions(receptor,best,rotatable_bonds=nrot),
            "method":"explicit-topology deterministic torsion beam search under Vina-form score",
            "limitations":["bond topology and moving components must be supplied; they are not guessed from PDB coordinates",
                           "ring conformers, receptor flexibility, protonation, and quantum strain are Missing"]}
