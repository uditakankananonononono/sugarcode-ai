"""Per-module registry of self-built features.

Activated features live as files under the module's own extensions dir and
are recorded in registry.json with sha256 digests. Dispatch re-verifies the
digest on every call, so tampered or hand-edited feature files refuse to run.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
import threading
import time
from pathlib import Path
from typing import Any


from .atomic_file import AtomicDurabilityError, atomic_write_text
from .proposal_preflight_r01 import preflight_proposal
from .registry_validation import decode_registry_json, validate_registry_state, RegistryValidationError
from .capped_readers import read_capped_bytes, InputLimitExceeded, REGISTRY_FILE_BYTES


class RegistryError(RuntimeError):
    pass


class FeatureRegistry:
    def __init__(self, module_slug: str, state_dir: Path) -> None:
        if not module_slug.replace("-", "").replace("_", "").isalnum():
            raise ValueError(f"unsafe module slug {module_slug!r}")
        self.module_slug = module_slug
        self._dir = Path(state_dir) / "modules" / module_slug
        self._ext_dir = self._dir / "extensions"
        self._ext_dir.mkdir(parents=True, exist_ok=True)
        self._path = self._dir / "registry.json"
        self._lock = threading.Lock()
        if not self._path.exists():
            self._save({"module": module_slug, "features": {}, "proposals": {}})

    def _load(self) -> dict[str, Any]:
        try:
            return decode_registry_json(read_capped_bytes(self._path, max_file_bytes=REGISTRY_FILE_BYTES), expected_module=self.module_slug)
        except (RegistryValidationError, InputLimitExceeded) as exc:
            raise RegistryError("invalid registry state; repair required") from exc

    def _save(self, data: dict[str, Any]) -> None:
        try:
            validate_registry_state(data, expected_module=self.module_slug)
            encoded = json.dumps(data, indent=2, sort_keys=True, allow_nan=False)
        except (ValueError, TypeError, RecursionError) as exc:
            raise RegistryError("invalid registry write; state unchanged") from exc
        if len(encoded.encode("utf-8")) > REGISTRY_FILE_BYTES:
            raise InputLimitExceeded("file", REGISTRY_FILE_BYTES)
        atomic_write_text(self._path, encoded)

    def _contained(self, path: Path) -> Path:
        resolved = path.resolve()
        if self._dir.resolve() not in resolved.parents:
            raise RegistryError(f"feature path {resolved} escapes module state dir")
        return resolved

    # -- proposals ---------------------------------------------------------
    def save_proposal(self, key: str, *, name: str, kind: str, code: str,
                      test_code: str, gap_signature: str) -> dict[str, Any]:
        with self._lock:
            plan = preflight_proposal(self._dir, module_slug=self.module_slug,
                key=key, name=name, kind=kind, code=code, test_code=test_code,
                gap_signature=gap_signature, validate_registry=decode_registry_json)
            data = self._load()
            if hashlib.sha256(read_capped_bytes(self._path, max_file_bytes=REGISTRY_FILE_BYTES)).hexdigest() != plan.registry_sha256:
                raise RegistryError("registry changed during proposal preflight")
            plan.code_path.parent.mkdir(exist_ok=True)
            created: list[Path] = []
            committed = False
            try:
                for path, content in ((plan.code_path, plan.code_bytes), (plan.test_path, plan.test_bytes)):
                    with path.open("xb") as stream:
                        created.append(path)
                        stream.write(content)
                record = {
                    "name": name, "kind": kind, "gap_signature": gap_signature,
                    "code_sha256": plan.code_sha256, "test_sha256": plan.test_sha256,
                    "code_file": str(plan.code_path), "test_file": str(plan.test_path),
                    "approval_id": None, "status": "proposed", "created_at": time.time(),
                }
                data["proposals"][key] = record
                try:
                    self._save(data)
                except AtomicDurabilityError:
                    committed = True  # new registry is present; keep its candidate files
                    raise
                committed = True
                return record
            finally:
                if not committed:
                    for path in created:
                        try:
                            path.unlink()
                        except OSError:
                            pass

    def get_proposal(self, key: str) -> dict[str, Any]:
        proposal = self._load()["proposals"].get(key)
        if proposal is None:
            raise KeyError(f"unknown proposal {key!r}")
        return proposal

    def set_proposal_approval(self, key: str, approval_id: str) -> None:
        with self._lock:
            data = self._load()
            if key not in data["proposals"]:
                raise KeyError(f"unknown proposal {key!r}")
            data["proposals"][key]["approval_id"] = approval_id
            self._save(data)

    # -- activation ----------------------------------------------------------
    def activate(self, proposal_key: str, *, approval_id: str) -> dict[str, Any]:
        proposal = self.get_proposal(proposal_key)
        code_path = self._contained(Path(proposal["code_file"]))
        code = code_path.read_text(encoding="utf-8")
        digest = hashlib.sha256(code.encode()).hexdigest()
        if digest != proposal["code_sha256"]:
            raise RegistryError("candidate code changed since proposal; refusing activation")
        name = proposal["name"]
        with self._lock:
            data = self._load()
            feature = data["features"].setdefault(name, {"versions": [], "active_version": None})
            version = len(feature["versions"]) + 1
            dest = self._contained(self._ext_dir / f"{name}_v{version}.py")
            shutil.copyfile(code_path, dest)
            entry = {
                "version": version, "file": str(dest), "sha256": digest,
                "kind": proposal["kind"], "gap_signature": proposal["gap_signature"],
                "approval_id": approval_id, "activated_at": time.time(),
                "dispatch_count": 0,
            }
            feature["versions"].append(entry)
            feature["active_version"] = version
            data["proposals"][proposal_key]["status"] = "activated"
            self._save(data)
        return entry

    def rollback(self, name: str, *, approval_id: str, expected_active_version: int | None = None) -> dict[str, Any]:
        with self._lock:
            data = self._load()
            feature = data["features"].get(name)
            if feature is None or feature["active_version"] is None:
                raise KeyError(f"no active feature {name!r}")
            current = feature["active_version"]
            if expected_active_version is not None and (type(expected_active_version) is not int or current != expected_active_version):
                raise PermissionError("rollback approval version does not match active version")
            earlier = [v["version"] for v in feature["versions"] if v["version"] < current]
            feature["active_version"] = max(earlier) if earlier else None
            for v in feature["versions"]:
                if v["version"] == current:
                    v["rolled_back_at"] = time.time()
                    v["rollback_approval_id"] = approval_id
            self._save(data)
            return {"name": name, "rolled_back_from": current,
                    "active_version": feature["active_version"]}

    # -- dispatch ------------------------------------------------------------
    def _active_entry(self, name: str) -> dict[str, Any]:
        feature = self._load()["features"].get(name)
        if feature is None or feature["active_version"] is None:
            raise KeyError(f"feature {name!r} is not active in module {self.module_slug}")
        return next(v for v in feature["versions"] if v["version"] == feature["active_version"])

    def dispatch(self, name: str, items: list, params: dict | None = None) -> dict:
        entry = self._active_entry(name)
        path = self._contained(Path(entry["file"]))
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            raise RegistryError(
                f"feature file {path.name} failed its integrity check; refusing to run")
        spec = importlib.util.spec_from_file_location(
            f"atlas_ext_{self.module_slug.replace('-', '_')}_{name}_v{entry['version']}", path)
        if spec is None or spec.loader is None:
            raise RegistryError(f"cannot load feature module {path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        run = getattr(module, "run", None)
        if not callable(run):
            raise RegistryError(f"feature {name!r} exposes no callable run()")
        result = run(items, params)
        with self._lock:
            data = self._load()
            for v in data["features"][name]["versions"]:
                if v["version"] == entry["version"]:
                    v["dispatch_count"] = v.get("dispatch_count", 0) + 1
                    v["last_dispatched_at"] = time.time()
            self._save(data)
        return result

    # -- inspection ----------------------------------------------------------
    def features(self) -> dict[str, Any]:
        return self._load()["features"]

    def proposals(self) -> dict[str, Any]:
        return self._load()["proposals"]

    def covers_gap(self, gap_signature: str) -> bool:
        data = self._load()
        for feature in data["features"].values():
            for v in feature["versions"]:
                if v["gap_signature"] == gap_signature:
                    return True
        for proposal in data["proposals"].values():
            if proposal["gap_signature"] == gap_signature and proposal["status"] in ("proposed", "activated"):
                return True
        return False
