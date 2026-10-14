"""Checked entry points for biofactory_1_a pid_control, assay_quality, reroute_on_failure,
experiment_log and workflow_dag (PARTIAL; core.py unchanged).

Core defects reproduced (see tests): experiment_log(protocol, <100000-deep nested results>) raises
RecursionError and emits invalid JSON ('NaN') for non-finite results; pid_control([]) raises
IndexError and dt=0 ZeroDivisionError, NaN passes silently; assay_quality with one replicate or equal
means raises ZeroDivisionError and NaN passes; reroute_on_failure accepts a failed_step that is not in
the DAG, a bool step, and a fallback whose own 'id' overrides the new node id.
All ranges and caps are choices made here, not spec values.

Enforced limits (choices made here, not spec values; the core accepts wider inputs):
  MAX_SERIES = 10000, MAX_STEPS = 10000, MAX_VALUE = 1e6, MAX_DEPTH = 64,
  MAX_NODES = 100000, MAX_FALLBACK_KEYS = 50, _PRE = 1e15.
  pid_control: kp, ki and kd in 0..1000.  NEGATIVE GAINS ARE REFUSED although the
  core accepts them; reverse-acting loops are therefore not supported here (a
  narrowing decision kept on purpose, not a claim that negative gains are invalid);
  dt in 1e-6..1e6; setpoint and measurements within +-MAX_VALUE.
  assay_quality: signal and background series of 2..MAX_SERIES values, each within +-1e9.
  experiment_log: the node cap is checked before a container's children are queued.
"""
from __future__ import annotations
import math
from collections.abc import Mapping

from . import core

MAX_SERIES = 10_000
MAX_STEPS = 10_000
MAX_VALUE = 1e6
MAX_DEPTH = 64
MAX_NODES = 100_000
MAX_FALLBACK_KEYS = 50
_PRE = 1e15


def _num(v, name, lo, hi):
    if isinstance(v, bool):
        raise TypeError(f"{name} must be a number, not bool")
    if not isinstance(v, (int, float)):
        raise TypeError(f"{name} must be a number")
    if isinstance(v, int):
        if abs(v) > _PRE:
            raise ValueError(f"{name} magnitude too large")
        v = float(v)
    elif math.isfinite(v) and abs(v) > _PRE:
        raise ValueError(f"{name} magnitude too large")
    if not math.isfinite(v):
        raise ValueError(f"{name} must be finite")
    if v < lo or v > hi:
        raise ValueError(f"{name} must be between {lo:g} and {hi:g}")
    return float(v)


def _series(v, name, min_len, hi):
    if not isinstance(v, (list, tuple)):
        raise TypeError(f"{name} must be a list or tuple of numbers")
    if len(v) < min_len or len(v) > MAX_SERIES:
        raise ValueError(f"{name} must have {min_len}..{MAX_SERIES} values")
    return [_num(x, f"{name} value", -hi, hi) for x in v]


def pid_control_checked(setpoint, measurements, kp=0.5, ki=0.1, kd=0.05, dt=1) -> dict:
    sp = _num(setpoint, "setpoint", -MAX_VALUE, MAX_VALUE)
    ms = _series(measurements, "measurements", 1, MAX_VALUE)
    gains = [_num(g, n, 0.0, 1000.0) for g, n in ((kp, "kp"), (ki, "ki"), (kd, "kd"))]
    step = _num(dt, "dt", 1e-6, 1e6)
    return core.pid_control(sp, ms, gains[0], gains[1], gains[2], step)


def assay_quality_checked(signal, background) -> dict:
    s = _series(signal, "signal", 2, 1e9)
    b = _series(background, "background", 2, 1e9)
    if sum(s) / len(s) == sum(b) / len(b):
        raise ValueError("signal and background means are equal")
    return core.assay_quality(s, b)


def _steps(steps):
    if not isinstance(steps, (list, tuple)):
        raise TypeError("steps must be a list or tuple of mappings")
    if not 1 <= len(steps) <= MAX_STEPS:
        raise ValueError(f"steps must have 1..{MAX_STEPS} entries")
    for i, s in enumerate(steps):
        if not isinstance(s, Mapping):
            raise TypeError(f"step {i} must be a mapping")
    return list(steps)


def workflow_dag_checked(steps) -> dict:
    return core.workflow_dag(_steps(steps))


def reroute_on_failure_checked(dag, failed_step, fallback) -> dict:
    if not isinstance(dag, Mapping) or "nodes" not in dag or "edges" not in dag:
        raise TypeError("dag must be a mapping with nodes and edges")
    nodes, edges = dag["nodes"], dag["edges"]
    if not isinstance(nodes, (list, tuple)) or not isinstance(edges, (list, tuple)):
        raise TypeError("dag nodes and edges must be lists")
    if not 1 <= len(nodes) <= MAX_STEPS or len(edges) > MAX_STEPS:
        raise ValueError(f"dag must have 1..{MAX_STEPS} nodes and at most {MAX_STEPS} edges")
    for e in edges:
        if not isinstance(e, Mapping) or "source" not in e:
            raise TypeError("each edge must be a mapping with source")
    if isinstance(failed_step, bool) or not isinstance(failed_step, int):
        raise TypeError("failed_step must be an int")
    if not 0 <= failed_step < len(nodes):
        raise ValueError(f"failed_step must be in [0, {len(nodes) - 1}]")
    if not isinstance(fallback, Mapping):
        raise TypeError("fallback must be a mapping")
    if len(fallback) > MAX_FALLBACK_KEYS:
        raise ValueError(f"fallback has more than {MAX_FALLBACK_KEYS} keys")
    if any(not isinstance(k, str) for k in fallback):
        raise TypeError("fallback keys must be text")
    if "id" in fallback:
        raise ValueError("fallback must not set 'id'")
    return core.reroute_on_failure(dag, failed_step, dict(fallback))


def _check_json(v):
    """Iterative walk (no recursion): depth, node count, types, finite floats, text keys."""
    stack = [(v, 0)]
    count = 0
    while stack:
        x, depth = stack.pop()
        count += 1
        if count > MAX_NODES:
            raise ValueError(f"results has more than {MAX_NODES} values")
        if depth > MAX_DEPTH:
            raise ValueError(f"results nested deeper than {MAX_DEPTH}")
        if x is None or isinstance(x, (bool, str)):
            continue
        if isinstance(x, int):
            if abs(x) > _PRE:
                raise ValueError("results integer magnitude too large")
            continue
        if isinstance(x, float):
            if not math.isfinite(x):
                raise ValueError("results must be finite")
            continue
        if isinstance(x, (list, tuple, dict)) and count + len(stack) + len(x) > MAX_NODES:
            # visited + pending + about to be added already exceeds the cap: refuse before allocating the children
            raise ValueError(f"results has more than {MAX_NODES} values")
        if isinstance(x, (list, tuple)):
            stack.extend((y, depth + 1) for y in x)
        elif isinstance(x, dict):
            for k, y in x.items():
                if not isinstance(k, str):
                    raise TypeError("results keys must be text")
                stack.append((y, depth + 1))
        else:
            raise TypeError(f"results contains unsupported type {type(x).__name__}")


def experiment_log_checked(protocol, results) -> dict:
    if not isinstance(protocol, Mapping) or not isinstance(protocol.get("workflow"), str):
        raise TypeError("protocol must be a mapping with a text workflow")
    _check_json(results)
    return core.experiment_log(protocol, results)
