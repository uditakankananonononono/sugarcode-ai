from __future__ import annotations
import numpy as np


def _kirchhoff(coords: np.ndarray, cutoff: float = 10.0,
               stiffness_map: dict[int, float] | None = None) -> np.ndarray:
    """Kirchhoff/contact matrix for a C-alpha elastic network."""
    n = len(coords)
    K = np.zeros((n, n))
    for i in range(n):
        for j in range(i + 1, n):
            d = np.linalg.norm(coords[i] - coords[j])
            if d < cutoff:
                w = 1.0
                if stiffness_map:
                    w = stiffness_map.get(i, 1.0) * stiffness_map.get(j, 1.0)
                K[i, j] = K[j, i] = -w
                K[i, i] += w
                K[j, j] += w
    return K


def anm_modes(coords: list[list[float]], n_modes: int = 6, cutoff: float = 10.0) -> dict:
    """Anisotropic network model: low-frequency normal modes of a structure.

    Builds the 3N x 3N Hessian from the contact graph, eigen-solves, returns
    mode frequencies and per-residue fluctuation profiles (B-factor analog).
    """
    C = np.asarray(coords, dtype=float)
    n = len(C)
    K = _kirchhoff(C, cutoff)
    H = np.zeros((3 * n, 3 * n))
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            kij = K[i, j]
            if kij == 0:
                continue
            rij = C[j] - C[i]
            dist = np.linalg.norm(rij)
            if dist == 0:
                continue
            e = rij / dist
            block = kij * np.outer(e, e)  # kij < 0: correct ANM off-diagonal
            H[3 * i:3 * i + 3, 3 * j:3 * j + 3] = block
            H[3 * i:3 * i + 3, 3 * i:3 * i + 3] -= block
            H[3 * j:3 * j + 3, 3 * j:3 * j + 3] -= block
    vals, vecs = np.linalg.eigh(H)
    order = np.argsort(vals)
    vals, vecs = vals[order], vecs[:, order]
    nz = [i for i, v in enumerate(vals) if v > 1e-6][:n_modes]
    modes = []
    fluct = np.zeros(n)
    for idx in nz:
        mode = vecs[:, idx].reshape(n, 3)
        sq = (mode ** 2).sum(axis=1)
        fluct += sq / vals[idx]
        modes.append({"index": int(idx), "frequency": round(float(np.sqrt(vals[idx])), 4),
                      "mean_square": round(float(sq.mean()), 6)})
    return {
        "n_residues": n,
        "modes": modes,
        "fluctuation_profile": [round(float(f), 6) for f in fluct / max(len(nz), 1)],
        "hinge_residues": _hinges(fluct),
    }


def _hinges(fluct: np.ndarray) -> list[int]:
    if len(fluct) < 5 or fluct.max() == 0:
        return []
    norm = fluct / fluct.max()
    return [int(i) for i in range(2, len(norm) - 2)
            if norm[i] < 0.2 and norm[i - 1] >= norm[i] and norm[i + 1] >= norm[i]][:5]


def transition_trace(coords: list[list[float]], mode_index: int = 0,
                     steps: int = 20, amplitude: float = 3.0) -> dict:
    """Temporal morph between open and closed states along a slow mode.

    Returns per-frame coordinates and RMSD-from-start trace (the 4th dimension).
    """
    C = np.asarray(coords, dtype=float)
    res = anm_modes(coords, n_modes=max(1, mode_index + 1))
    C0 = C
    K = _kirchhoff(C)
    # rebuild the chosen mode direction
    n = len(C)
    H = np.zeros((3 * n, 3 * n))
    for i in range(n):
        for j in range(n):
            kij = K[i, j]
            if i == j or kij == 0:
                continue
            rij = C[j] - C[i]
            dist = np.linalg.norm(rij)
            if dist == 0:
                continue
            e = rij / dist
            block = kij * np.outer(e, e)  # kij < 0: correct ANM off-diagonal
            H[3 * i:3 * i + 3, 3 * j:3 * j + 3] = block
            H[3 * i:3 * i + 3, 3 * i:3 * i + 3] -= block
            H[3 * j:3 * j + 3, 3 * j:3 * j + 3] -= block
    vals, vecs = np.linalg.eigh(H)
    nz = [i for i, v in enumerate(vals) if v > 1e-6]
    if not nz:
        raise ValueError("structure has no non-rigid modes")
    mode = vecs[:, nz[min(mode_index, len(nz) - 1)]].reshape(n, 3)
    frames, rmsd = [], []
    for s in range(steps):
        phase = amplitude * np.sin(np.pi * s / (steps - 1))
        frame = C0 + phase * mode
        frames.append([[round(float(x), 3) for x in row] for row in frame])
        rmsd.append(round(float(np.sqrt(((frame - C0) ** 2).sum(axis=1).mean())), 4))
    return {
        "mode": mode_index, "frames": frames, "rmsd_trace": rmsd,
        "max_rmsd": max(rmsd),
        "event_timeline": [{"frame": i, "event": "opening" if i < steps // 2 else "closing"}
                           for i in (0, steps // 2, steps - 1)],
    }


def perturbation_effect(coords: list[list[float]], site: int, kind: str = "phosphorylation") -> dict:
    """Model a PTM/ligand as a local stiffness change; report fluctuation shift."""
    base = anm_modes(coords)
    stiff = {site: 2.5}
    C = np.asarray(coords, dtype=float)
    n = len(C)
    K = _kirchhoff(C, stiffness_map=stiff)
    # recompute fluctuation quickly with modified network
    from numpy.linalg import pinv
    G = pinv(K, rcond=1e-6)
    fluct_ptm = np.diag(G)[:n]
    base_f = np.array(base["fluctuation_profile"])
    f2 = fluct_ptm / fluct_ptm.max() if fluct_ptm.max() > 0 else fluct_ptm
    b = base_f / base_f.max() if base_f.max() > 0 else base_f
    delta = f2 - b
    return {
        "site": site, "perturbation": kind,
        "local_rigidification": round(float(-delta[site]), 4) if site < len(delta) else None,
        "most_affected_residues": sorted(range(len(delta)), key=lambda i: -abs(delta[i]))[:5],
        "interpretation": (f"{kind} at residue {site} stiffens the local network and "
                           "redistributes flexibility - shifting the open/closed equilibrium."),
    }
