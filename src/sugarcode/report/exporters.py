"""CSV/TSV exporters and sha256-checksummed evidence bundles."""
from __future__ import annotations

import csv
import hashlib
import io
import json
from datetime import datetime, timezone
from pathlib import Path


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _columns(rows: list[dict], columns: list[str] | None) -> list[str]:
    if columns is not None:
        if not columns or not all(isinstance(c, str) and c for c in columns):
            raise ValueError("columns must be a non-empty list of names")
        return list(columns)
    seen: set[str] = set()
    for r in rows:
        seen.update(r)
    return sorted(seen)


def to_csv(rows: list[dict], columns: list[str] | None = None, *,
           delimiter: str = ",") -> str:
    """Serialize row dicts to CSV text. Deterministic column order: the
    explicit list, else the sorted union of keys. csv-module quoting rules
    apply, so commas, quotes and newlines in values are safe. A row key
    outside the column set raises ValueError (silent data loss is worse)."""
    if not isinstance(rows, list) or not all(isinstance(r, dict) for r in rows):
        raise TypeError("rows must be a list of dicts")
    cols = _columns(rows, columns)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, delimiter=delimiter,
                       lineterminator="\n", extrasaction="raise")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if v is None else v) for k, v in r.items()})
    return buf.getvalue()


def to_tsv(rows: list[dict], columns: list[str] | None = None) -> str:
    """Tab-separated variant of to_csv."""
    return to_csv(rows, columns, delimiter="\t")


def make_bundle(name: str, artifacts: dict[str, str], *,
                metadata: dict | None = None,
                created_utc: str | None = None) -> dict:
    """Package named text artifacts with per-file sha256 checksums and byte
    sizes, so a receiving lab can verify the bundle byte-for-byte."""
    if not isinstance(name, str) or not name.strip():
        raise ValueError("bundle name must be non-empty")
    if not artifacts:
        raise ValueError("artifacts must be non-empty")
    files: dict[str, dict] = {}
    for fn, content in artifacts.items():
        if not isinstance(fn, str) or not fn or "/" in fn or "\\" in fn or fn in (".", ".."):
            raise ValueError(f"unsafe artifact filename {fn!r}")
        if not isinstance(content, str):
            raise TypeError(f"artifact {fn!r} content must be text")
        data = content.encode("utf-8")
        files[fn] = {"content": content, "sha256": hashlib.sha256(data).hexdigest(),
                     "bytes": len(data)}
    return {
        "name": name,
        "created_utc": created_utc or _utc_now(),
        "generator": "sugarcode-ai report engine",
        "artifacts": files,
        "metadata": metadata or {},
    }


def write_bundle(bundle: dict, out_dir: str | Path) -> dict:
    """Write a bundle to a directory: every artifact plus MANIFEST.json
    carrying checksums, sizes, metadata and creation time."""
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    manifest = {
        "name": bundle["name"],
        "created_utc": bundle["created_utc"],
        "generator": bundle["generator"],
        "metadata": bundle["metadata"],
        "files": {fn: {"sha256": a["sha256"], "bytes": a["bytes"]}
                  for fn, a in bundle["artifacts"].items()},
    }
    written = []
    for fn, a in bundle["artifacts"].items():
        p = out / fn
        p.write_text(a["content"], encoding="utf-8")
        written.append(str(p))
    mp = out / "MANIFEST.json"
    mp.write_text(json.dumps(manifest, indent=1) + "\n", encoding="utf-8")
    written.append(str(mp))
    return {"dir": str(out), "files": written, "manifest": manifest}
