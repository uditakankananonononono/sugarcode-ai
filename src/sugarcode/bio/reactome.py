"""Live Reactome ContentService connector: curated pathways for a UniProt accession.

Free and keyless (https://reactome.org/ContentService). Responses are cached on disk like the
other connectors; ``offline=True`` serves only cached responses and raises otherwise.
"""
from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

BASE = "https://reactome.org/ContentService"
CACHE_DIR = Path.home() / ".sugarcode_cache" / "reactome"


class ReactomeError(RuntimeError):
    pass


def _get(path: str, params: dict, offline: bool = False, retries: int = 3) -> bytes | None:
    """GET ``path``; returns None for a 404 (Reactome's answer for 'no pathways')."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    query = urllib.parse.urlencode(sorted(params.items()))
    cache_file = CACHE_DIR / (hashlib.sha256(f"{path}?{query}".encode()).hexdigest()[:32] + ".json")
    if cache_file.exists():
        data = cache_file.read_bytes()
        return None if data == b"null" else data
    if offline:
        raise ReactomeError(f"offline mode: no cache for {path}?{query}")
    delay = 0.5
    for attempt in range(retries):
        try:
            request = urllib.request.Request(f"{BASE}/{path}?{query}", headers={"Accept": "application/json", "User-Agent": "sugarcode-ai (+https://github.com/uditakankananonononono)"})
            with urllib.request.urlopen(request, timeout=20) as response:  # default urllib UA gets 403
                data = response.read()
            cache_file.write_bytes(data)
            return data
        except urllib.error.HTTPError as e:
            if e.code == 404:
                cache_file.write_bytes(b"null")
                return None
            if attempt == retries - 1:
                raise ReactomeError(f"Reactome request failed: HTTP {e.code}") from e
        except (urllib.error.URLError, TimeoutError, ConnectionError) as e:
            if attempt == retries - 1:
                raise ReactomeError(f"Reactome request failed after {retries} tries: {e}") from e
        time.sleep(delay)
        delay *= 2
    raise ReactomeError("unreachable")


def pathways_for_uniprot(accession: str, species_taxon: int = 9606, offline: bool = False) -> list[dict]:
    """Lowest-level Reactome pathways that contain the protein, e.g. P04637 -> TP53 pathways."""
    data = _get(f"data/mapping/UniProt/{urllib.parse.quote(accession)}/pathways",
                {"species": species_taxon}, offline=offline)
    if data is None:
        return []
    return [{"pathway": item.get("displayName"), "id": item.get("stId"), "source": "Reactome (live)",
             "in_disease": bool(item.get("isInDisease"))} for item in json.loads(data)]
