"""Checked entry points for biofactory_1_a dbtl_report and factory_diagnostics (PARTIAL; core unchanged).

Core defects reproduced (see tests): dbtl_report(["x"]) raises a raw 'unhashable type' TypeError,
n_constructs=0 or 10**9 is accepted (0 plates; 10**9 gives a 10.4 million plate protocol), an empty
observations tuple silently returns the prior, NaN observations return a NaN posterior, one assay
replicate or equal means raise ZeroDivisionError; factory_diagnostics raises a raw KeyError or
TypeError on a malformed report. Unknown workflow names keep the module's KeyError.
Ranges are choices made here, not spec values."""
from __future__ import annotations
from collections.abc import Mapping

from . import core
from .boundary_ops import _num, _series

MAX_CONSTRUCTS = 100_000
MAX_OBS = 1_000
MAX_VALUE = 1e6
_PRE = 1e15


def dbtl_report_checked(workflow, n_constructs=8, observations=(0.6, 0.8, 0.9),
                        assay_signal=(10, 11, 9.5), assay_background=(1, 1.2, 0.8)) -> dict:
    if not isinstance(workflow, str):
        raise TypeError("workflow must be text")
    if workflow not in core.WORKFLOWS:
        raise KeyError(f"unknown workflow {workflow!r}; have {sorted(core.WORKFLOWS)}")
    if isinstance(n_constructs, bool) or not isinstance(n_constructs, int):
        raise TypeError("n_constructs must be an int")
    if not 1 <= n_constructs <= MAX_CONSTRUCTS:
        raise ValueError(f"n_constructs must be in [1, {MAX_CONSTRUCTS}]")
    obs = _series(observations, "observations", 1, MAX_VALUE)
    if len(obs) > MAX_OBS:
        raise ValueError(f"observations must have at most {MAX_OBS} values")
    sig = _series(assay_signal, "assay_signal", 2, 1e9)
    bg = _series(assay_background, "assay_background", 2, 1e9)
    if len(sig) > MAX_OBS or len(bg) > MAX_OBS:
        raise ValueError(f"assay series must have at most {MAX_OBS} values")
    if sum(sig) / len(sig) == sum(bg) / len(bg):
        raise ValueError("signal and background means are equal")
    return core.dbtl_report(workflow, n_constructs, obs, sig, bg)


def _field(m, key, what):
    if not isinstance(m, Mapping) or key not in m:
        raise TypeError(f"{what} must be a mapping with {key}")
    return m[key]


def _seq(v, name):
    if not isinstance(v, (list, tuple)):
        raise TypeError(f"{name} must be a list")
    return v


def factory_diagnostics_checked(report) -> dict:
    if not isinstance(report, Mapping):
        raise TypeError("report must be a mapping")
    p = _field(report, "protocol", "report")
    d = _field(report, "dag", "report")
    s = _field(report, "schedule", "report")
    b = _field(report, "condition_update", "report")
    q = _field(report, "assay_quality", "report")
    for k in ("n_constructs", "plates", "estimated_runtime_min"):
        _num(_field(p, k, "protocol"), f"protocol {k}", 0.0, _PRE)
    _seq(_field(p, "steps", "protocol"), "protocol steps")
    _seq(_field(p, "equipment_required", "protocol"), "protocol equipment_required")
    _seq(_field(d, "nodes", "dag"), "dag nodes")
    _seq(_field(d, "edges", "dag"), "dag edges")
    _num(_field(s, "makespan_min", "schedule"), "schedule makespan_min", 0.0, _PRE)
    for k in ("posterior_mean", "posterior_variance"):
        _num(_field(b, k, "condition_update"), f"condition_update {k}", -_PRE, _PRE)
    for k in ("z_prime", "signal_background"):
        _num(_field(q, k, "assay_quality"), f"assay_quality {k}", -_PRE, _PRE)
    return core.factory_diagnostics(report)
