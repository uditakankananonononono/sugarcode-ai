"""Hardened validating wrappers for deepsplice (additive; core.py untouched).

Defects on b363c3b: branchpoint_variant_effect silently accepts index -1 / 100 and multi-base alt
(builds a wrong-length alt window; index=100 appends, scoring an unchanged window), variant_at accepts
bool index; exon_inclusion OverflowError for large negative delta and nan psi; isoform_distribution(psi=2)
returns canonical 2.0 and intron_retained -1.0 (probabilities outside [0,1]); active_learning and
intervention_simulation accept probability 2 / nan / negative off-target risk.
Statistical PWM/logistic heuristics only; no clinical claim.
"""
from __future__ import annotations
import math
from . import core

_ACGT = frozenset("ACGT")


def _num(name, v, lo, hi):
    if isinstance(v, bool):
        raise ValueError(f"{name}: bool is not a number")
    if not isinstance(v, (int, float)):
        raise ValueError(f"{name}: must be int or float")
    if abs(v) > 10**9:
        raise ValueError(f"{name}: magnitude exceeds cap")
    v = float(v)
    if not math.isfinite(v):
        raise ValueError(f"{name}: must be finite")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: out of range [{lo}, {hi}]")
    return v


def _int(name, v, lo, hi):
    if isinstance(v, bool) or not isinstance(v, int):
        raise ValueError(f"{name}: must be int")
    if not lo <= v <= hi:
        raise ValueError(f"{name}: must be in [{lo}, {hi}]")
    return v


def _base(alt_base):
    if not isinstance(alt_base, str) or len(alt_base) != 1 or alt_base.upper() not in _ACGT:
        raise ValueError("alt_base: exactly one of A, C, G, T required")
    return alt_base.upper()


def _seq(name, s, n=None):
    if not isinstance(s, str) or not s or len(s) > 1_000_000:
        raise ValueError(f"{name}: non-empty str required")
    if set(s.upper()) - _ACGT:
        raise ValueError(f"{name}: only A, C, G, T accepted")
    if n is not None and len(s) != n:
        raise ValueError(f"{name}: must be {n} nt")
    return s


def _ok(x):
    if isinstance(x, dict):
        return all(_ok(v) for v in x.values())
    if isinstance(x, (list, tuple)):
        return all(_ok(v) for v in x)
    return not isinstance(x, float) or math.isfinite(x)


def safe_branchpoint_variant_effect(win60, index, alt_base):
    _seq("win60", win60, 60)
    i = _int("index", index, 0, 59)
    return core.branchpoint_variant_effect(win60, i, _base(alt_base))


def safe_variant_at(ref_window, index, alt_base, site_type="donor", matrix="real"):
    _seq("ref_window", ref_window)
    i = _int("index", index, 0, len(ref_window) - 1)
    out = core.variant_at(ref_window, i, _base(alt_base), site_type, matrix)
    if not _ok(out):
        raise ValueError("non-finite output refused")
    return out


def _stable_logistic(x):
    # core uses 1/(1+exp(-x)), which raises OverflowError for x < -709.78; this form never overflows
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def safe_exon_inclusion(ref_site, alt_site, regulatory, calibration_n=100):
    r = _num("ref_site", ref_site, -10.0, 10.0)
    a = _num("alt_site", alt_site, -10.0, 10.0)
    if not isinstance(regulatory, dict):
        raise ValueError("regulatory: dict required")
    sup = _num("exon_definition_support", regulatory.get("exon_definition_support"), -100.0, 100.0)
    n = _int("calibration_n", calibration_n, 1, 10**9)
    # same formula as core.exon_inclusion, evaluated with an overflow-free logistic
    delta = a - r
    logit_ref = -.5 + 5 * r + 2 * sup
    logit = logit_ref + delta * max(5, logit_ref / .15)
    psi = _stable_logistic(logit)
    radius = 1.96 * math.sqrt(psi * (1 - psi) / max(1, n))
    out = {'psi': psi, 'delta_site_strength': delta, 'interval95': [max(0, psi - radius), min(1, psi + radius)],
           'calibration_n': n}
    if not _ok(out) or not 0 <= psi <= 1:
        raise ValueError("output out of range refused")
    return out


def safe_isoform_distribution(psi, frame_preserved=True, cryptic_strength=0, intron_retention=.05):
    p = _num("psi", psi, 0.0, 1.0)
    cs = _num("cryptic_strength", cryptic_strength, 0.0, 1.0)
    ir = _num("intron_retention", intron_retention, 0.0, 1.0)
    if not isinstance(frame_preserved, bool):
        raise ValueError("frame_preserved: bool required")
    out = core.isoform_distribution(p, frame_preserved, cs, ir)
    vals = out["isoforms"].values()
    if not _ok(out) or any(v < -1e-12 for v in vals) or abs(sum(vals) - 1) > 1e-9:
        raise ValueError("output is not a probability distribution; refused")
    return out


def safe_active_learning(candidates):
    if isinstance(candidates, (str, bytes, dict)) or not hasattr(candidates, "__len__") or len(candidates) > 100_000:
        raise ValueError("candidates: list of dicts required")
    for c in candidates:
        if not isinstance(c, dict):
            raise ValueError("candidate: dict required")
        _num("probability", c.get("probability"), 0.0, 1.0)
        _num("impact", c.get("impact", .5), 0.0, 1e6)
    return core.active_learning(list(candidates))


def safe_intervention_simulation(wild_psi, aberrant_psi, strategies):
    w = _num("wild_psi", wild_psi, 0.0, 1.0)
    ab = _num("aberrant_psi", aberrant_psi, 0.0, 1.0)
    if isinstance(strategies, (str, bytes, dict)) or not hasattr(strategies, "__len__") or len(strategies) > 100_000:
        raise ValueError("strategies: list of dicts required")
    for s in strategies:
        if not isinstance(s, dict):
            raise ValueError("strategy: dict required")
        _num("psi_shift", s.get("psi_shift", 0), -1.0, 1.0)
        _num("offtarget_risk", s.get("offtarget_risk", .1), 0.0, 1.0)
    return core.intervention_simulation(w, ab, list(strategies))
