"""Thermodynamic RNA folding via ViennaRNA (Turner 2004 nearest-neighbour
parameters), next to the Nussinov base-pair maximiser.

Why: on Rfam seed sequences with their projected consensus structure
(mega27-01 sweep, 25 per family, seed 7), Nussinov reaches base-pair F1
0.33 (tRNA RF00005), 0.19 (5S RF00001), 0.19 (RNase P RF00010); ViennaRNA
MFE reaches 0.71 / 0.53 / 0.55 and the centroid 0.72 / 0.49 / 0.59.
Nussinov stays as the exact combinatorial reference; this module is what
to use for biologically meaningful structures.

ViennaRNA is an optional dependency (pip install ViennaRNA). Without it
every call raises EnergyModelMissing - no silent fallback to Nussinov."""
from __future__ import annotations

from .core import dot_bracket_to_pairs, normalize_sequence

METHODS = ("mfe", "centroid", "mea")


class EnergyModelMissing(RuntimeError):
    pass


def _rna():
    try:
        import RNA  # type: ignore
    except ImportError as e:  # pragma: no cover - exercised only without ViennaRNA
        raise EnergyModelMissing("ViennaRNA not installed: pip install ViennaRNA") from e
    return RNA


def fold_energy(sequence: str, *, method: str = "mfe", gamma: float = 1.0,
                temperature: float = 37.0) -> dict:
    """Energy-model structure for an RNA/DNA sequence (T read as U).

    method: "mfe" (minimum free energy, Zuker), "centroid" (structure
    closest to the Boltzmann ensemble) or "mea" (maximum expected accuracy,
    weight ``gamma``). Returns dot-bracket, 0-based pairs, MFE (kcal/mol),
    ensemble free energy and the MFE structure's ensemble frequency."""
    if method not in METHODS:
        raise ValueError(f"method must be one of {METHODS}")
    seq = normalize_sequence(sequence)
    RNA = _rna()
    md = RNA.md()
    md.temperature = float(temperature)
    fc = RNA.fold_compound(seq, md)
    mfe_db, mfe = fc.mfe()
    fc.exp_params_rescale(mfe)
    _, ens = fc.pf()
    if method == "mfe":
        db = mfe_db
    elif method == "centroid":
        db = fc.centroid()[0]
    else:
        db = fc.MEA(float(gamma))[0]
    return {
        "sequence": seq, "method": method, "dot_bracket": db,
        "pairs": [list(p) for p in dot_bracket_to_pairs(db)],
        "mfe_kcal_mol": round(mfe, 2), "ensemble_free_energy_kcal_mol": round(ens, 2),
        "mfe_ensemble_frequency": round(fc.pr_structure(mfe_db), 6),
        "temperature_c": float(temperature),
        "model": "ViennaRNA %s, Turner 2004" % RNA.__version__,
    }
