"""Input-boundary wrappers for OpenClinVar evidence arithmetic (additive, new file).

Defects probed at b363c3b9 in openclinvar/core.py (all reproduced):
* bayesian_acmg: 200 very_strong items overflow odds to inf, posterior NaN; an
  unknown strength is silently weight 1 and any direction other than
  'pathogenic' (including typos) is silently treated as benign.
* federated_evidence: supporting > total gives negative beta and posterior mean
  2.2; negative counts and NaN pass; zero priors give ZeroDivisionError.
* forward_trajectory: penetrance -3 gives negative cumulative risk, negative
  ages likewise; unknown classification silently uses factor 0.35.
* evidence_consensus: negative quality gives negative weights and negative
  support; negative sample_size raises a math domain error; bool/NaN accepted.
* phenotype_match / reverse_inference: a str is iterated as characters
  ('HP:1' becomes 4 terms); duplicate terms; probability 5 gives score 1.75.
* reasoning_graph: str phenotypes/pathways split into characters; node ids
  may collide (duplicate nodes/edges).
Wrappers validate then delegate to unchanged core. These are illustrative
evidence-arithmetic guards, not clinical validation.

Enforced limits (choices made in this wrapper, not spec values; the core
accepts wider inputs, and these inputs are refused with ValueError):
  MAX_ITEMS = 10000 (updates, records, candidates), MAX_EVIDENCE = 100,
  MAX_TERMS = 1000 (phenotype/pathway terms), MAX_AGES = 100,
  MAX_COUNT = 1e12 (counts, sample_size), _PRE = 1e15 (absolute-value cap
  applied to numeric inputs before arithmetic).
  Ranges: prior in [1e-6, 1 - 1e-6]; prior_alpha and prior_beta > 0;
  supporting <= total; penetrance, quality, variant_probability in [0, 1];
  age <= 120 (and >= 0); years 1900..2026.  Strengths, directions and
  classes outside the named sets are refused, not defaulted.
"""
from __future__ import annotations

import math
from collections.abc import Mapping

from . import core

MAX_ITEMS = 10_000
MAX_EVIDENCE = 100          # 350**100 * 1e6 stays far below float max
MAX_TERMS = 1000
MAX_AGES = 100
MAX_COUNT = 1e12
_PRE = 1e15
STRENGTHS = ("very_strong", "strong", "moderate", "supporting")
DIRECTIONS = ("pathogenic", "benign")
CLASSES = ("pathogenic", "likely_pathogenic", "uncertain_significance", "likely_benign", "benign")


def _num(v, name, lo=None, hi=None, *, lo_open=False):
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
    if lo is not None and (v <= lo if lo_open else v < lo):
        raise ValueError(f"{name} below allowed range")
    if hi is not None and v > hi:
        raise ValueError(f"{name} above allowed range")
    return v


def _seq(v, name, cap):
    if not isinstance(v, (list, tuple)):
        raise TypeError(f"{name} must be a list or tuple")
    if len(v) > cap:
        raise ValueError(f"{name} exceeds {cap} items")
    return v


def _text(v, name):
    if not isinstance(v, str) or not v:
        raise TypeError(f"{name} must be non-empty text")
    return v


def _terms(v, name):
    if not isinstance(v, (list, tuple, set, frozenset)):
        raise TypeError(f"{name} must be a list, tuple or set of text terms")
    if len(v) > MAX_TERMS:
        raise ValueError(f"{name} exceeds {MAX_TERMS} terms")
    for t in v:
        _text(t, f"{name} term")
    if len(set(v)) != len(v):
        raise ValueError(f"{name} contains duplicate terms")
    return v


def bayesian_acmg_checked(evidence, prior=0.1):
    ev = _seq(evidence, "evidence", MAX_EVIDENCE)
    p = _num(prior, "prior", 1e-6, 1 - 1e-6)
    for i, e in enumerate(ev):
        if not isinstance(e, Mapping):
            raise TypeError(f"evidence[{i}] must be a mapping")
        if "strength" in e and e["strength"] not in STRENGTHS:
            raise ValueError(f"evidence[{i}] strength must be one of {STRENGTHS}")
        if "direction" in e and e["direction"] not in DIRECTIONS:
            raise ValueError(f"evidence[{i}] direction must be one of {DIRECTIONS}")
    return core.bayesian_acmg([dict(e) for e in ev], prior if isinstance(prior, float) else p)


def federated_evidence_checked(updates, prior_alpha=1, prior_beta=1):
    ups = _seq(updates, "updates", MAX_ITEMS)
    a0 = _num(prior_alpha, "prior_alpha", 0.0, MAX_COUNT, lo_open=True)
    b0 = _num(prior_beta, "prior_beta", 0.0, MAX_COUNT, lo_open=True)
    for i, u in enumerate(ups):
        if not isinstance(u, Mapping) or "supporting" not in u or "total" not in u:
            raise TypeError(f"updates[{i}] needs supporting and total")
        t = _num(u["total"], "total", 0.0, MAX_COUNT)
        _num(u["supporting"], "supporting", 0.0, t)
    return core.federated_evidence([dict(u) for u in ups], a0, b0)


def forward_trajectory_checked(classification, penetrance=0.5, ages=(20, 40, 60)):
    if not isinstance(classification, str) or classification not in CLASSES:
        raise ValueError(f"classification must be one of {CLASSES}")
    pen = _num(penetrance, "penetrance", 0.0, 1.0)
    ag = _seq(ages, "ages", MAX_AGES)
    if not ag:
        raise ValueError("ages must not be empty")
    for a in ag:
        _num(a, "age", 0.0, 120.0)
    return core.forward_trajectory(classification, pen, tuple(ag))


def evidence_consensus_checked(records):
    rs = _seq(records, "records", MAX_ITEMS)
    for i, r in enumerate(rs):
        if not isinstance(r, Mapping):
            raise TypeError(f"records[{i}] must be a mapping")
        _text(r.get("classification"), "classification")
        if "quality" in r:
            _num(r["quality"], "quality", 0.0, 1.0)
        if "sample_size" in r:
            _num(r["sample_size"], "sample_size", 0.0, MAX_COUNT)
        if "year" in r:
            y = r["year"]
            if isinstance(y, bool) or not isinstance(y, int):
                raise TypeError("year must be an integer")
            if not 1900 <= y <= 2026:
                raise ValueError("year must be between 1900 and 2026")
    return core.evidence_consensus([dict(r) for r in rs])


def _ancestors(m):
    if m is None:
        return None
    if not isinstance(m, Mapping):
        raise TypeError("ancestor_map must be a mapping")
    out = {}
    for k, v in m.items():
        _text(k, "ancestor_map key")
        if not isinstance(v, (list, tuple, set, frozenset)):
            raise TypeError("ancestor_map values must be collections of text")
        for t in v:
            _text(t, "ancestor_map term")
        out[k] = v
    return out


def phenotype_match_checked(patient_hpo, disease_hpo, ancestor_map=None):
    p = _terms(patient_hpo, "patient_hpo")
    d = _terms(disease_hpo, "disease_hpo")
    return core.phenotype_match(p, d, _ancestors(ancestor_map))


def reverse_inference_checked(patient_hpo, candidates):
    p = _terms(patient_hpo, "patient_hpo")
    cs = _seq(candidates, "candidates", MAX_ITEMS)
    for i, c in enumerate(cs):
        if not isinstance(c, Mapping):
            raise TypeError(f"candidates[{i}] must be a mapping")
        _terms(c.get("phenotypes", []), "candidate phenotypes")
        _ancestors(c.get("ancestor_map"))
        if "variant_probability" in c:
            _num(c["variant_probability"], "variant_probability", 0.0, 1.0)
    return core.reverse_inference(p, [dict(c) for c in cs])


def reasoning_graph_checked(gene, variant, consequence, phenotypes=(), pathways=(), structure_effect=None):
    ids = [_text(variant, "variant"), _text(gene, "gene"), _text(consequence, "consequence")]
    ph = _terms(phenotypes, "phenotypes")
    pw = _terms(pathways, "pathways")
    ids += list(pw) + list(ph)
    if structure_effect is not None:
        ids.append(_text(structure_effect, "structure_effect"))
    if len(set(ids)) != len(ids):
        raise ValueError("graph node ids must be unique")
    return core.reasoning_graph(gene, variant, consequence, tuple(ph) if isinstance(ph, (set, frozenset)) else ph,
                                tuple(pw) if isinstance(pw, (set, frozenset)) else pw, structure_effect)
