"""Hardened validating wrappers for phage_designer (additive; core.py untouched).

Defects on b363c3b: design_fiber emits the literal text "{host_pathogen}" and "{target_receptor}" in its engineering
steps (missing f-prefix on the third string), so the advice never names the host; design_lysin silently treats any
unknown gram_type as 'gram+', counts a repeated domain twice in the potency mean, and raises a raw TypeError for
unhashable domains; adsorption_kinetics accepts nan/inf/bool and returns nan 'free'; escape_probability returns nan
for nan inputs, negative rates give 'probabilities' below 0 and 10**400 raises OverflowError; host_range and
cocktail_design raise raw AttributeError/KeyError for malformed profiles or designs. Curated heuristic tables only;
no wet-lab, procedural, clinical or efficacy claim.
"""
from __future__ import annotations
import math
from . import core

MAX_ITEMS = 1000


def _num(name, v, lo, hi, lo_open=False):
    if isinstance(v, bool) or not isinstance(v, (int, float)):
        raise ValueError(f"{name}: must be int or float (not bool)")
    try:
        f = float(v)
    except OverflowError:
        raise ValueError(f"{name}: magnitude too large") from None
    if not math.isfinite(f):
        raise ValueError(f"{name}: must be finite")
    if (f <= lo if lo_open else f < lo) or f > hi:
        raise ValueError(f"{name}: must be in {'(' if lo_open else '['}{lo}, {hi}]")
    return f


def _finite(x):
    if isinstance(x, dict):
        return all(_finite(v) for v in x.values())
    if isinstance(x, (list, tuple)):
        return all(_finite(v) for v in x)
    return not isinstance(x, float) or math.isfinite(x)


def _str(name, v, n=200):
    if not isinstance(v, str) or not v.strip() or len(v) > n:
        raise ValueError(f"{name}: non-empty str up to {n} characters required")
    return v


def safe_design_fiber(target_receptor, host_pathogen="Escherichia_coli"):
    if not isinstance(target_receptor, str) or target_receptor not in core.RECEPTOR_BINDERS:
        raise ValueError(f"target_receptor: must be one of {sorted(core.RECEPTOR_BINDERS)}")
    host = _str("host_pathogen", host_pathogen)
    out = core.design_fiber(target_receptor, host)
    # core forgets the f-prefix on its third step; fill the placeholders it left behind
    out["engineering"] = [s.replace("{host_pathogen}", host).replace("{target_receptor}", target_receptor) for s in out["engineering"]]
    return out


def safe_design_lysin(gram_type="gram+", domains=None):
    if gram_type not in ("gram+", "gram-") or not isinstance(gram_type, str):
        raise ValueError("gram_type: must be 'gram+' or 'gram-'")
    if domains is not None:
        if not isinstance(domains, (list, tuple)) or not 1 <= len(domains) <= len(core.LYSIN_DOMAINS):
            raise ValueError(f"domains: list of 1..{len(core.LYSIN_DOMAINS)} names required")
        for d in domains:
            if not isinstance(d, str) or d not in core.LYSIN_DOMAINS:
                raise ValueError(f"domains: unknown domain {d!r}; choose from {sorted(core.LYSIN_DOMAINS)}")
        if len(set(domains)) != len(domains):
            raise ValueError("domains: duplicates not allowed (a repeated domain would be counted twice)")
        domains = list(domains)
    return core.design_lysin(gram_type, domains)


def safe_adsorption_kinetics(phage, bacteria, k_ads, time_min=60):
    p = _num("phage", phage, 0.0, 1e18, lo_open=True)
    b = _num("bacteria", bacteria, 0.0, 1e18)
    k = _num("k_ads", k_ads, 0.0, 1e6)
    t = _num("time_min", time_min, 0.0, 1e6)
    out = core.adsorption_kinetics(p, b, k, t)
    if not _finite(out):
        raise ValueError("non-finite output refused")
    return out


def safe_escape_probability(mutation_rate, target_sites, population):
    m = _num("mutation_rate", mutation_rate, 0.0, 1.0)
    s = _num("target_sites", target_sites, 0.0, 1e6)
    n = _num("population", population, 0.0, 1e15)
    out = core.escape_probability(m, s, n)
    if not _finite(out) or not 0.0 <= out["escape_probability"] <= 1.0:
        raise ValueError("non-finite or out-of-range output refused")
    return out


def _design(design):
    if not isinstance(design, dict):
        raise ValueError("design: dict required")
    tr = design.get("target_receptor")
    if not isinstance(tr, str) or not tr:
        raise ValueError("design['target_receptor']: str required")
    rate = _num("design['predicted_adsorption_rate']", design.get("predicted_adsorption_rate"), 0.0, 1.0)
    return {**design, "predicted_adsorption_rate": rate}


def safe_host_range(receptor_profile, design):
    d = _design(design)
    if not isinstance(receptor_profile, dict) or len(receptor_profile) > MAX_ITEMS:
        raise ValueError(f"receptor_profile: dict of up to {MAX_ITEMS} strains required")
    prof = {}
    for strain, expr in receptor_profile.items():
        if not isinstance(strain, str) or not isinstance(expr, dict) or len(expr) > 100:
            raise ValueError("receptor_profile: {strain(str): {receptor(str): expression}} required")
        prof[strain] = {r: _num(f"expression[{strain}][{r}]", v, 0.0, 1.0) for r, v in expr.items() if isinstance(r, str)}
        if len(prof[strain]) != len(expr):
            raise ValueError("receptor_profile: receptor names must be str")
    out = core.host_range(prof, d)
    if not _finite(out):
        raise ValueError("non-finite output refused")
    return out


def safe_cocktail_design(phages, strains):
    if not isinstance(phages, (list, tuple)) or not 1 <= len(phages) <= 100:
        raise ValueError("phages: list of 1..100 designs required")
    ph = []
    for p in phages:
        if not isinstance(p, dict) or not isinstance(p.get("target_receptor"), str):
            raise ValueError("phage: dict with str 'target_receptor' required")
        hosts = p.get("predicted_hosts", [])
        if not isinstance(hosts, (list, tuple)) or not all(isinstance(x, str) for x in hosts) or len(hosts) > MAX_ITEMS:
            raise ValueError("phage predicted_hosts: list of str required")
        ph.append(p)
    if not isinstance(strains, (list, tuple)) or not 1 <= len(strains) <= MAX_ITEMS or not all(isinstance(s, str) for s in strains):
        raise ValueError(f"strains: list of 1..{MAX_ITEMS} str required")
    if len(set(strains)) != len(strains):
        raise ValueError("strains: duplicates not allowed")
    return core.cocktail_design(ph, list(strains))


def safe_phage_report(receptor, profiles):
    if not isinstance(receptor, str) or receptor not in core.RECEPTOR_BINDERS:
        raise ValueError(f"receptor: must be one of {sorted(core.RECEPTOR_BINDERS)}")
    d = safe_design_fiber(receptor)
    hr = safe_host_range(profiles, d)
    out = core.phage_report(receptor, profiles)
    out["engineering"] = d["engineering"]
    out["host_range"] = hr
    if not _finite(out):
        raise ValueError("non-finite output refused")
    return out
