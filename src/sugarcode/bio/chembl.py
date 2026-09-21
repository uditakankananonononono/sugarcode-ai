"""Live ChEMBL REST connector: targets, measured bioactivities, molecules."""
from __future__ import annotations
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://www.ebi.ac.uk/chembl/api/data"
CACHE_DIR = Path.home() / ".sugarcode_cache" / "chembl"
_last_call = 0.0


class ChEMBLError(RuntimeError):
    pass


def _get(url: str, offline: bool = False, retries: int = 3) -> dict:
    global _last_call
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    cache_file = CACHE_DIR / f"{abs(hash(url))}.json"
    if cache_file.exists():
        return json.loads(cache_file.read_bytes())
    if offline:
        raise ChEMBLError(f"offline mode: no cache for {url}")
    wait = 0.34 - (time.monotonic() - _last_call)
    if wait > 0:
        time.sleep(wait)
    _last_call = time.monotonic()
    delay = 0.5
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sugarcode-ai/0.9"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read())
            cache_file.write_bytes(json.dumps(data).encode())
            return data
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            if attempt == retries - 1:
                raise ChEMBLError(f"ChEMBL request failed: {e}") from e
            time.sleep(delay)
            delay *= 2
    raise ChEMBLError("unreachable")


def target_search(name: str, organism: str | None = "Homo sapiens",
                  offline: bool = False) -> list[dict]:
    """Find targets by name; returns chembl_id, pref_name, type, organism.

    Strategy: pref_name__icontains on each word (precise), then free-text q as
    fallback. Entries with unknown organism are kept but sorted last."""
    def norm(d):
        out = []
        for t in d.get("targets", []):
            out.append({"chembl_id": t["target_chembl_id"], "pref_name": t["pref_name"],
                        "type": t.get("target_type"),
                        "organism": t.get("target_organism") or t.get("organism")})
        return out

    word = name.split()[-1] if len(name.split()) > 2 else name
    d = _get(f"{BASE}/target.json?pref_name__icontains={urllib.parse.quote(word)}&limit=20",
             offline=offline)
    hits = norm(d)
    if not hits:
        d = _get(f"{BASE}/target.json?q={urllib.parse.quote(name)}&limit=20", offline=offline)
        hits = norm(d)
    if organism:
        human = [h for h in hits if h["organism"] == organism]
        other = [h for h in hits if h["organism"] != organism]
        hits = human + other
    return hits


def activities_for_target(chembl_id: str, max_n: int = 50,
                          offline: bool = False) -> list[dict]:
    """Measured activities (IC50/Ki/Kd in nM) against a target, best first."""
    url = (f"{BASE}/activity.json?target_chembl_id={chembl_id}"
           f"&standard_type__in=IC50,Ki,Kd&standard_units=nM&limit={max_n}")
    d = _get(url, offline=offline)
    out = []
    for a in d.get("activities", []):
        if a.get("standard_value") is None:
            continue
        try:
            val = float(a["standard_value"])
        except (TypeError, ValueError):
            continue
        out.append({"molecule_chembl_id": a.get("molecule_chembl_id"),
                    "standard_type": a.get("standard_type"),
                    "value_nM": val,
                    "relation": a.get("standard_relation"),
                    "assay_type": a.get("assay_type"),
                    "pchembl": a.get("pchembl_value"),
                    "document_year": a.get("document_year")})
    out.sort(key=lambda x: x["value_nM"])
    return out[:max_n]


def molecule_info(chembl_id: str, offline: bool = False) -> dict:
    """Molecule record: name, max phase, SMILES, properties."""
    d = _get(f"{BASE}/molecule/{chembl_id}.json", offline=offline)
    props = d.get("molecule_properties") or {}
    return {
        "chembl_id": d.get("molecule_chembl_id"),
        "name": d.get("pref_name") or (d.get("molecule_synonyms") or [{}])[0].get("molecule_synonym"),
        "max_phase": d.get("max_phase"),
        "smiles": (d.get("molecule_structures") or {}).get("canonical_smiles"),
        "mw": props.get("full_mwt"), "alogp": props.get("alogp"),
        "hba": props.get("hba"), "hbd": props.get("hbd"),
        "ro5_violations": props.get("num_ro5_violations"),
    }
