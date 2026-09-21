"""Live structure connector: RCSB PDB + AlphaFold DB (EBI), with a real
PDB/mmCIF-lite coordinate parser. Cached, offline-capable."""
from __future__ import annotations
import json
import time
import urllib.error
import urllib.request
from pathlib import Path

RCSB = "https://data.rcsb.org/rest/v1/core/entry"
RCSB_FILE = "https://files.rcsb.org/download"
AFDB = "https://alphafold.ebi.ac.uk/api/prediction"
CACHE_DIR = Path.home() / ".sugarcode_cache" / "structures"
_last_call = 0.0


class StructureError(RuntimeError):
    pass


def _get(url: str, offline: bool = False, retries: int = 3) -> bytes:
    global _last_call
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{abs(hash(url))}.raw"
    if cache_file.exists():
        return cache_file.read_bytes()
    if offline:
        raise StructureError(f"offline mode: no cache for {url}")
    wait = 0.34 - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()
    delay = 0.5
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sugarcode-ai/0.4"})
            with urllib.request.urlopen(req, timeout=30) as r:
                data = r.read()
            cache_file.write_bytes(data)
            return data
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt == retries - 1:
                raise StructureError(f"structure fetch failed: {e}") from e
            time.sleep(delay)
            delay *= 2
    raise StructureError("unreachable")


def parse_pdb(text: str) -> dict:
    """Parse ATOM records into per-residue C-alpha trace + B-factors.

    Returns residues: [{resnum, resname, chain, ca:(x,y,z), bfactor}].
    B-factor holds pLDDT for AlphaFold models.
    """
    residues = []
    seen = set()
    for line in text.splitlines():
        if not line.startswith("ATOM"):
            continue
        atom = line[12:16].strip()
        if atom != "CA":
            continue
        resname = line[17:20].strip()
        chain = line[21].strip()
        resnum = int(line[22:26])
        key = (chain, resnum)
        if key in seen:
            continue
        seen.add(key)
        x = float(line[30:38]); y = float(line[38:46]); z = float(line[46:54])
        b = float(line[60:66]) if line[60:66].strip() else 0.0
        residues.append({"resnum": resnum, "resname": resname, "chain": chain,
                         "ca": (x, y, z), "bfactor": b})
    if not residues:
        raise StructureError("no C-alpha atoms parsed - not a usable PDB text")
    return {"residues": residues, "chains": sorted({r["chain"] for r in residues}),
            "n_residues": len(residues)}


def fetch_pdb(pdb_id: str, offline: bool = False) -> dict:
    """Experimental structure from RCSB: metadata + parsed coordinates."""
    pdb_id = pdb_id.lower()
    meta = json.loads(_get(f"{RCSB}/{pdb_id}", offline=offline))
    text = _get(f"{RCSB_FILE}/{pdb_id}.pdb", offline=offline).decode(errors="replace")
    parsed = parse_pdb(text)
    method = (meta.get("exptl") or [{}])[0].get("method", "unknown")
    reso = meta.get("rcsb_entry_info", {}).get("resolution_combined")
    return {"pdb_id": pdb_id, "source": "RCSB PDB (live)", "method": method,
            "resolution_A": reso[0] if isinstance(reso, list) and reso else None,
            "title": meta.get("struct", {}).get("title", ""), **parsed}


def fetch_alphafold(uniprot_acc: str, offline: bool = False) -> dict:
    """AlphaFold DB model for a UniProt accession: coordinates + per-residue pLDDT."""
    acc = uniprot_acc.upper()
    listing = json.loads(_get(f"{AFDB}/{acc}", offline=offline))
    if not listing:
        raise StructureError(f"no AlphaFold model for {acc}")
    entry = listing[0]
    text = _get(entry["pdbUrl"], offline=offline).decode(errors="replace")
    parsed = parse_pdb(text)
    plddts = [r["bfactor"] for r in parsed["residues"]]
    mean_plddt = round(sum(plddts) / len(plddts), 2)
    low_conf = sum(1 for p in plddts if p < 50) / len(plddts)
    return {"accession": acc, "source": "AlphaFold DB (live)",
            "model_version": entry.get("latestVersion"),
            "mean_plddt": mean_plddt,
            "fraction_low_confidence": round(low_conf, 3),
            "paE_url": entry.get("paeDocUrl"), **parsed}


# --- drop 14: Shrake-Rupley solvent accessibility + interface areas -------------
VDW_RADII = {"C": 1.70, "N": 1.55, "O": 1.52, "S": 1.80, "P": 1.80, "DEFAULT": 1.70}


def sasa_shrake_rupley(atoms: list[dict], probe: float = 1.4, n_points: int = 96) -> dict:
    """Shrake & Rupley (1973) solvent-accessible surface area per atom.

    atoms: [{element, xyz:(x,y,z)}]. Each atom gets n_points on a sphere of
    radius r_vdw + probe; a point is accessible if no other atom's sphere
    covers it. Returns per-atom A^2 and total."""
    import math
    pts = []
    inc = math.pi * (3 - math.sqrt(5))  # fibonacci sphere
    for i in range(n_points):
        y = 1 - (i / (n_points - 1)) * 2
        r = math.sqrt(max(0.0, 1 - y * y))
        th = inc * i
        pts.append((math.cos(th) * r, y, math.sin(th) * r))
    radii = [VDW_RADII.get(a.get("element", "C"), VDW_RADII["DEFAULT"]) + probe for a in atoms]
    coords = [a["xyz"] for a in atoms]
    rmax = max(radii)
    # spatial hash: only atoms within rmax + ri can bury a point of atom i
    cell = 2 * rmax
    grid = {}
    for j, (x, y, z) in enumerate(coords):
        grid.setdefault((int(x // cell), int(y // cell), int(z // cell)), []).append(j)
    def neighbors(x, y, z, reach):
        c0 = (int(x // cell), int(y // cell), int(z // cell))
        n = int(reach // cell) + 1
        out = []
        for dx in range(-n, n + 1):
            for dy in range(-n, n + 1):
                for dz in range(-n, n + 1):
                    out.extend(grid.get((c0[0] + dx, c0[1] + dy, c0[2] + dz), []))
        return out
    out = []
    for i, (x, y, z) in enumerate(coords):
        acc = 0
        cand = neighbors(x, y, z, rmax + radii[i])
        for px, py, pz in pts:
            sx, sy, sz = x + radii[i] * px, y + radii[i] * py, z + radii[i] * pz
            buried = False
            for j in cand:
                if i == j:
                    continue
                ox, oy, oz = coords[j]
                if (sx - ox) ** 2 + (sy - oy) ** 2 + (sz - oz) ** 2 < radii[j] ** 2:
                    buried = True
                    break
            if not buried:
                acc += 1
        out.append(round(4 * math.pi * radii[i] ** 2 * acc / n_points, 3))
    return {"per_atom_A2": out, "total_A2": round(sum(out), 2), "probe_A": probe,
            "method": "Shrake-Rupley 1973, fibonacci sphere"}


def parse_pdb_atoms(text: str) -> list[dict]:
    """Full-atom parse: [{element, xyz, chain, resnum, atom}] for interface math."""
    atoms = []
    for line in text.splitlines():
        if not line.startswith("ATOM"):
            continue
        el = line[76:78].strip() or line[12:16].strip()[0]
        atoms.append({"element": el,
                      "xyz": (float(line[30:38]), float(line[38:46]), float(line[46:54])),
                      "chain": line[21].strip(), "resnum": int(line[22:26]),
                      "atom": line[12:16].strip()})
    if not atoms:
        raise StructureError("no ATOM records parsed")
    return atoms


def interface_area(pdb_id: str, chain_a: str, chain_b: str,
                   offline: bool = False) -> dict:
    """Buried surface area of a real protein-protein interface (RCSB complex).

    BSA = (SASA(A) + SASA(B) - SASA(AB)) / 2 - the standard interface metric."""
    pdb_id = pdb_id.lower()
    text = _get(f"{RCSB_FILE}/{pdb_id}.pdb", offline=offline).decode(errors="replace")
    atoms = parse_pdb_atoms(text)
    a = [x for x in atoms if x["chain"] == chain_a]
    b = [x for x in atoms if x["chain"] == chain_b]
    if not a or not b:
        raise StructureError(f"chains {chain_a}/{chain_b} not both present; have "
                             f"{sorted({x['chain'] for x in atoms})}")
    s_a = sasa_shrake_rupley(a)["total_A2"]
    s_b = sasa_shrake_rupley(b)["total_A2"]
    s_ab = sasa_shrake_rupley(a + b)["total_A2"]
    bsa = (s_a + s_b - s_ab) / 2
    return {"pdb_id": pdb_id, "chains": [chain_a, chain_b],
            "sasa_A": s_a, "sasa_B": s_b, "sasa_complex": s_ab,
            "buried_surface_area_A2": round(bsa, 1),
            "interface_class": ("strong/stable" if bsa > 1500 else "transient/weak" if bsa > 600 else "minimal contact"),
            "method": "Shrake-Rupley SASA difference; BSA = (SA+SB-SAB)/2",
            "source": "RCSB PDB (live)" if not offline else "RCSB PDB (cache)"}
