"""Real AutoDock Vina docking (Eberhardt et al. 2021, vina>=1.2) with Open Babel
preparation. Optional dependency: `pip install vina openbabel-wheel`.

Unlike vina.py (a Vina-form scorer on a straight-chain ligand), this runs the
actual Vina search with an RDKit 3D conformer and returns real poses.
Validated in mega27-01 benchmarks/sweep_docking.json (LP-PDBBind test split)."""
from __future__ import annotations
import os, shutil, subprocess, tempfile


class VinaUnavailable(RuntimeError):
    pass


def _require():
    try:
        import vina  # noqa: F401
    except ImportError as e:
        raise VinaUnavailable("install `vina` and `openbabel-wheel` for real docking") from e
    if shutil.which("obabel") is None:
        raise VinaUnavailable("Open Babel `obabel` binary not found")


def prepare_receptor(pdb_path: str, out_pdbqt: str, ph: float = 7.4) -> str:
    _require()
    tmp = out_pdbqt + ".protein.pdb"
    with open(pdb_path) as f, open(tmp, "w") as g:
        g.write("".join(l for l in f if l.startswith("ATOM")) + "END\n")
    subprocess.run(["obabel", tmp, "-xr", "-h", "-p", str(ph), "-O", out_pdbqt],
                   check=True, capture_output=True, timeout=300)
    os.remove(tmp)
    return out_pdbqt


def prepare_ligand_from_smiles(smiles: str, out_pdbqt: str, seed: int = 7) -> str:
    _require()
    from rdkit import Chem
    from rdkit.Chem import AllChem
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise ValueError("invalid SMILES")
    mol = Chem.AddHs(mol)
    if AllChem.EmbedMolecule(mol, randomSeed=seed) != 0:
        raise ValueError("RDKit could not embed a 3D conformer")
    AllChem.MMFFOptimizeMolecule(mol)
    sdf = out_pdbqt + ".sdf"
    Chem.MolToMolFile(mol, sdf)
    subprocess.run(["obabel", sdf, "-O", out_pdbqt], check=True, capture_output=True, timeout=120)
    os.remove(sdf)
    return out_pdbqt


def dock(receptor_pdbqt: str, ligand_pdbqt: str, center, box_size=(22.0, 22.0, 22.0),
         exhaustiveness: int = 8, n_poses: int = 9, seed: int = 7) -> dict:
    """Run Vina; returns energies (kcal/mol) and the poses PDBQT text."""
    _require()
    from vina import Vina
    v = Vina(sf_name="vina", seed=seed, verbosity=0)
    v.set_receptor(receptor_pdbqt)
    v.set_ligand_from_file(ligand_pdbqt)
    v.compute_vina_maps(center=list(center), box_size=list(box_size))
    v.dock(exhaustiveness=exhaustiveness, n_poses=n_poses)
    with tempfile.NamedTemporaryFile("r", suffix=".pdbqt", delete=False) as t:
        path = t.name
    v.write_poses(path, n_poses=n_poses, overwrite=True)
    poses = open(path).read(); os.remove(path)
    e = v.energies(n_poses=n_poses)
    return {"engine": "AutoDock Vina", "best_affinity_kcal_mol": float(e[0][0]),
            "affinities": [float(x[0]) for x in e], "poses_pdbqt": poses,
            "center": list(center), "box_size": list(box_size)}


def score_pose(receptor_pdbqt: str, ligand_pdbqt: str, center, box_size=(24.0, 24.0, 24.0)) -> dict:
    """Vina score_only and local optimization of an existing (e.g. crystal) pose."""
    _require()
    from vina import Vina
    v = Vina(sf_name="vina", verbosity=0)
    v.set_receptor(receptor_pdbqt); v.set_ligand_from_file(ligand_pdbqt)
    v.compute_vina_maps(center=list(center), box_size=list(box_size))
    return {"score_only": float(v.score()[0]), "local_opt": float(v.optimize()[0])}
