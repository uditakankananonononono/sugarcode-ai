"""SC-R01 read-only preparation, not wired into FeatureRegistry.

The validator seam and refusal-only retry policy are proposals for integration.
See docs/prep/sc-r01-proposal-preflight-contract.md before using this module.
"""
from __future__ import annotations

import hashlib
import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class ProposalPreflightError(ValueError):
    """No candidate may be written after this refusal."""


class StrictRegistryValidator(Protocol):
    """Call shape of SC-J02 decode_registry_json, injected to keep prep disjoint."""

    def __call__(self, raw: bytes, *, expected_module: str) -> dict[str, Any]:
        ...


_KEY = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z", re.ASCII)
_NAME = re.compile(r"[a-z][a-z0-9_]{0,127}\Z", re.ASCII)
_MODULE = re.compile(r"[A-Za-z0-9][A-Za-z0-9_-]{0,127}\Z", re.ASCII)
_KINDS = frozenset(("keyword_filter", "scoring_rule", "text_transform",
                    "aggregator", "threshold_alert", "field_extractor"))


@dataclass(frozen=True)
class ProposalWritePlan:
    """Validated input bytes and destinations. This does not authorize a write."""

    key: str
    name: str
    kind: str
    gap_signature: str
    code_path: Path
    test_path: Path
    code_bytes: bytes
    test_bytes: bytes
    code_sha256: str
    test_sha256: str
    registry_sha256: str


def _text(value: object, field: str) -> str:
    if type(value) is not str:
        raise ProposalPreflightError(f"{field} must be an exact string")
    return value


def _identity(value: object, field: str, pattern: re.Pattern[str]) -> str:
    text = _text(value, field)
    if not pattern.fullmatch(text):
        raise ProposalPreflightError(f"unsafe {field}")
    return text


def _plain_directory_chain(path: Path) -> None:
    # Inspect every ancestor, not merely resolve() and accept a symlink target.
    for part in (*reversed(path.parents), path):
        mode = part.lstat().st_mode
        if not stat.S_ISDIR(mode):
            raise ProposalPreflightError("module directory chain is not plain directories")


def _absent(path: Path) -> None:
    try:
        path.lstat()
    except FileNotFoundError:
        return
    raise ProposalPreflightError("candidate destination already exists")


def preflight_proposal(
    module_dir: Path,
    *,
    module_slug: str,
    key: str,
    name: str,
    kind: str,
    code: str,
    test_code: str,
    gap_signature: str,
    validate_registry: StrictRegistryValidator,
) -> ProposalWritePlan:
    """Read/validate registry and paths without mkdir, writes, or replacements.

    The validator is called with raw bytes and keyword-only expected_module.
    It must strictly decode JSON and check the full SC-J02 schema before returning an exact built-in dict. It must
    raise on any malformed/ambiguous/invalid state. Exceptions propagate unchanged
    so the integration can preserve J02's error/cause contract. No permissive
    fallback decoder exists here. Filesystem/input refusals use our own error.

    All existing keys are refused, even identical retries. Both destinations must
    be absent, including broken symlinks. A returned plan is a snapshot, not a
    reservation: the integration must close the concurrent-create/replace races.
    """
    module_slug = _identity(module_slug, "module_slug", _MODULE)
    key = _identity(key, "key", _KEY)
    name = _identity(name, "name", _NAME)
    kind = _text(kind, "kind")
    if kind not in _KINDS:
        raise ProposalPreflightError("unsupported kind")
    gap_signature = _text(gap_signature, "gap_signature")
    code = _text(code, "code")
    test_code = _text(test_code, "test_code")
    try:
        code_bytes = code.encode("utf-8", errors="strict")
        test_bytes = test_code.encode("utf-8", errors="strict")
    except UnicodeEncodeError as exc:
        raise ProposalPreflightError("candidate is not UTF-8 encodable") from exc

    # abspath is lexical normalization, not symlink resolution.
    directory = Path(os.path.abspath(module_dir))
    registry_path = directory / "registry.json"
    candidates = directory / "candidates"
    code_path = candidates / f"{key}.py"
    test_path = candidates / f"{key}.test.py"
    try:
        _plain_directory_chain(directory)
        if not stat.S_ISREG(registry_path.lstat().st_mode):
            raise ProposalPreflightError("registry must be a plain regular file")
        raw = registry_path.read_bytes()
    except OSError as exc:
        raise ProposalPreflightError("cannot inspect existing registry") from exc

    data = validate_registry(raw, expected_module=module_slug)
    # Seam postconditions only; these are not a replacement for SC-J02.
    if (type(data) is not dict or type(data.get("module")) is not str
            or data["module"] != module_slug):
        raise ProposalPreflightError("validator returned wrong module/object")
    proposals = data.get("proposals")
    if type(proposals) is not dict:
        raise ProposalPreflightError("validator returned no proposals object")
    if key in proposals:
        raise ProposalPreflightError("proposal key already registered; retries refused")
    try:
        try:
            mode = candidates.lstat().st_mode
        except FileNotFoundError:
            pass
        else:
            if not stat.S_ISDIR(mode):
                raise ProposalPreflightError("candidates must be a plain directory")
            _absent(code_path)
            _absent(test_path)
    except OSError as exc:
        raise ProposalPreflightError("cannot inspect candidate destinations") from exc

    return ProposalWritePlan(
        key=key, name=name, kind=kind, gap_signature=gap_signature,
        code_path=code_path, test_path=test_path,
        code_bytes=code_bytes, test_bytes=test_bytes,
        code_sha256=hashlib.sha256(code_bytes).hexdigest(),
        test_sha256=hashlib.sha256(test_bytes).hexdigest(),
        registry_sha256=hashlib.sha256(raw).hexdigest(),
    )
