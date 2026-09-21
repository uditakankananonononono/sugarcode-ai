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
