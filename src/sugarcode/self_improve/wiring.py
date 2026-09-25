"""Wire the self-improvement engine into every Sugarcode module.

Modules are enumerated from the sugarcode.modules package directory, so new
modules are covered automatically the day they are added.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Callable

from .engine import SelfImprovementEngine
from .gate import ApprovalGate, ManualApprovalGate

DEFAULT_STATE_ENV = "SUGARCODE_SELF_IMPROVE_HOME"
_MODULES_PKG = Path(__file__).resolve().parent.parent / "modules"


def list_module_slugs() -> list[str]:
    """All real module packages under sugarcode.modules."""
    return sorted(
        d.name for d in _MODULES_PKG.iterdir()
        if d.is_dir() and (d / "__init__.py").exists()
    )


def default_state_dir() -> Path:
    return Path(os.environ.get(DEFAULT_STATE_ENV,
                               Path.home() / ".sugarcode" / "self_improve"))


_engines: dict[str, SelfImprovementEngine] = {}


def attach_all(*, state_dir: Path | str | None = None,
               gate_factory: Callable[[str], ApprovalGate] | None = None,
               min_occurrences: int = 2) -> dict[str, SelfImprovementEngine]:
    root = Path(state_dir) if state_dir else default_state_dir()
    engines: dict[str, SelfImprovementEngine] = {}
    for index, slug in enumerate(list_module_slugs()):
        gate = gate_factory(slug) if gate_factory else ManualApprovalGate(
            root / "approvals" / f"{slug}.json")
        engines[slug] = SelfImprovementEngine(
            module_id=index, module_slug=slug, state_dir=root,
            gate=gate, min_occurrences=min_occurrences)
    return engines


def engine_for(slug: str, *, state_dir: Path | str | None = None) -> SelfImprovementEngine:
    global _engines
    if not _engines or state_dir is not None:
        _engines = attach_all(state_dir=state_dir)
    if slug not in _engines:
        raise KeyError(f"unknown module slug {slug!r}")
    return _engines[slug]


def reset_engines() -> None:
    global _engines
    _engines = {}
