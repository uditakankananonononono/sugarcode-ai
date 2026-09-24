"""Connector cache keys must be stable across processes. They used
abs(hash(url)); Python salts str hashes per process (PYTHONHASHSEED), so
caches never hit in a new process and offline mode could never work."""
import subprocess, sys

def test_no_salted_hash_cache_keys():
    import pathlib
    for p in ["uniprot", "chembl", "gnomad", "structures"]:
        src = pathlib.Path(f"src/sugarcode/bio/{p}.py").read_text()
        assert "abs(hash(" not in src, p
        assert "hashlib.sha256" in src, p
