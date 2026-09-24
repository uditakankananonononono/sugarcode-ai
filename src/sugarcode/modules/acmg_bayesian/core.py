"""Tavtigian 2018 Bayesian calibration of the ACMG/AMP variant guidelines.

Source: Tavtigian SV et al., "Modeling the ACMG/AMP variant classification
guidelines as a Bayesian classification framework", Genet Med 2018;20:1054-1060,
DOI 10.1038/gim.2017.210, PMID 29300386, free full text PMC6336098.

Model, exactly as published:
  * OddsPath very strong (OP_VSt) = 350, exponent X = 2, so each step down in
    strength halves the log-odds: OP = 350 ** (1 / 2**k) for k = 0..3
    (very strong 350, strong 18.708, moderate 4.3253, supporting 2.0797).
  * Benign evidence gets the reciprocal odds of the matching strength.
  * Prior probability of pathogenicity 0.10.
  * Posterior bands: Pathogenic > 0.99, Likely pathogenic 0.90-0.99,
    Likely benign 0.001-<0.10, Benign < 0.001, otherwise VUS.

Exact arithmetic. Every OP in the model is 350 ** (points / 8) with integer
points (supporting 1, moderate 2, strong 4, very strong 8; benign negative), so
the evidence total is carried as an integer and never drifts. The one band edge
that floating point would get wrong is the likely-pathogenic floor: all five
ACMG likely-pathogenic combining rules (ii-vi) total 6 points, OP = 350 ** 0.75
= 80.92, posterior 0.89991. The paper states OP 81 "are the exact odds required
to convert a Prior_P of 0.10 to a Post_P of 0.90" and reports these rules at
0.900 (Table 2), so at the calibrated prior the bands are applied on the integer
point total: P >= 10, LP 6..9, VUS 0..5, LB -6..-1, B <= -7. Each of these
point bands is exactly the set of point totals whose posterior falls in the
paper's band, with 6 points placed at 0.90 as the paper does.

BA1 (benign stand-alone) is not part of the Bayesian model: the paper excludes
it "because it is used as absolute evidence that a variant is benign,
irrespective of other evidence, which is contrary to Bayesian reasoning". Here
BA1 is a stand-alone override applied outside the math: the classification is
Benign, the posterior is computed from the remaining evidence only and reported
separately, and any coexisting pathogenic evidence is flagged for expert review.
"""
from __future__ import annotations

from typing import Iterable

PRIOR_PROBABILITY = 0.10
OP_VERY_STRONG = 350.0
EXPONENT_X = 2.0

# Integer "points" = log_{OP_supporting}(OP); OP = 350 ** (points / 8).
STRENGTH_POINTS = {"supporting": 1, "moderate": 2, "strong": 4, "very_strong": 8}
STRENGTH_ODDS = {s: OP_VERY_STRONG ** (p / 8) for s, p in STRENGTH_POINTS.items()}

MODEL_PROVENANCE = {
    "publication": "Tavtigian et al., Genet Med 2018;20:1054-1060",
    "doi": "10.1038/gim.2017.210",
    "pmid": "29300386",
    "pmcid": "PMC6336098",
    "op_very_strong": OP_VERY_STRONG,
    "exponent_x": EXPONENT_X,
    "odds": {s: round(v, 6) for s, v in STRENGTH_ODDS.items()},
    "calibrated_prior": PRIOR_PROBABILITY,
    "ba1": "stand-alone benign override outside the Bayesian model (excluded by the paper)",
    "important_limit": ("Posterior is a model-calibrated probability that the variant is "
                        "pathogenic, not penetrance or an individual's disease risk."),
}

# ACMG/AMP 2015 criteria (Richards et al.) with default strengths.
DEFAULT_STRENGTH: dict[str, tuple[str, str]] = {
    "PVS1": ("pathogenic", "very_strong"),
    **{f"PS{i}": ("pathogenic", "strong") for i in range(1, 5)},
    **{f"PM{i}": ("pathogenic", "moderate") for i in range(1, 7)},
    **{f"PP{i}": ("pathogenic", "supporting") for i in range(1, 6)},
    **{f"BS{i}": ("benign", "strong") for i in range(1, 5)},
    **{f"BP{i}": ("benign", "supporting") for i in range(1, 8)},
}
STAND_ALONE_BENIGN = "BA1"

PATHOGENIC = "Pathogenic"
LIKELY_PATHOGENIC = "Likely pathogenic"
VUS = "Uncertain significance"
LIKELY_BENIGN = "Likely benign"
BENIGN = "Benign"


def posterior_from_points(points: int, prior_probability: float = PRIOR_PROBABILITY) -> float:
    """Posterior probability of pathogenicity for an integer point total."""
    prior_odds = prior_probability / (1.0 - prior_probability)
    odds = prior_odds * OP_VERY_STRONG ** (points / 8.0)
    return odds / (1.0 + odds)


def classify_points(points: int) -> str:
    """Five-tier label at the calibrated prior 0.10 (see module docstring)."""
    if points >= 10:
        return PATHOGENIC
    if points >= 6:
        return LIKELY_PATHOGENIC
    if points <= -7:
        return BENIGN
    if points <= -1:
        return LIKELY_BENIGN
    return VUS


def classify_posterior(posterior: float) -> str:
    """Paper's posterior bands, used only for a caller-chosen non-default prior."""
    if posterior > 0.99:
        return PATHOGENIC
    if posterior >= 0.90:
        return LIKELY_PATHOGENIC
    if posterior < 0.001:
        return BENIGN
    if posterior < 0.10:
        return LIKELY_BENIGN
    return VUS


def _normalise(raw) -> dict:
    item = {"code": raw} if isinstance(raw, str) else dict(raw)
    item["code"] = str(item.get("code", "")).strip().upper()
    return item


def bayesian_acmg(criteria: Iterable[str | dict], *,
                  prior_probability: float = PRIOR_PROBABILITY) -> dict:
    """Score explicitly supplied ACMG/AMP criteria with the Tavtigian 2018 model.

    Each item is a code ("PM2") or a mapping {"code", "strength"?, "provenance"?}.
    ``strength`` re-weights a criterion to one of supporting / moderate / strong /
    very_strong (e.g. PM2 applied at supporting); the change is recorded.
    Unknown codes or strengths are returned under ``rejected_evidence`` and do
    not affect the score.
    """
    if not 0.0 < prior_probability < 1.0:
        raise ValueError("prior_probability must be strictly between 0 and 1")
    accepted, rejected, ba1 = [], [], []
    for raw in criteria:
        item = _normalise(raw)
        code = item["code"]
        prov = item.get("provenance", "user-supplied; not independently validated")
        if code == STAND_ALONE_BENIGN:
            if "strength" in item and str(item["strength"]).lower() not in ("stand_alone", "stand-alone"):
                rejected.append({"input": raw, "reason": "BA1 is stand-alone only; it has no graded strength"})
            else:
                ba1.append({"code": code, "direction": "benign", "strength": "stand_alone",
                            "provenance": prov})
            continue
        if code not in DEFAULT_STRENGTH:
            rejected.append({"input": raw, "reason": "unknown ACMG/AMP evidence code"})
            continue
        direction, default = DEFAULT_STRENGTH[code]
        strength = str(item.get("strength", default)).lower().replace("-", "_").replace(" ", "_")
        if strength not in STRENGTH_POINTS:
            rejected.append({"input": raw, "reason": f"unknown evidence strength {strength!r}"})
            continue
        pts = STRENGTH_POINTS[strength] * (1 if direction == "pathogenic" else -1)
        accepted.append({"code": code, "direction": direction, "strength": strength,
                         "default_strength": default, "modified": strength != default,
                         "points": pts, "odds_of_pathogenicity": OP_VERY_STRONG ** (pts / 8.0),
                         "provenance": prov})

    points = sum(x["points"] for x in accepted)
    combined_op = OP_VERY_STRONG ** (points / 8.0)
    posterior = posterior_from_points(points, prior_probability)
    calibrated = prior_probability == PRIOR_PROBABILITY
    has_path = any(x["direction"] == "pathogenic" for x in accepted)
    has_benign = any(x["direction"] == "benign" for x in accepted) or bool(ba1)

    if ba1:
        label, basis = BENIGN, "BA1 stand-alone override (outside the Bayesian model)"
    elif not accepted:
        label, basis = VUS, "no accepted evidence; posterior equals prior"
    elif calibrated:
        label, basis = classify_points(points), "integer point bands at the calibrated prior 0.10"
    else:
        label, basis = classify_posterior(posterior), "posterior bands at a caller-chosen prior"

    reasons = []
    if not accepted and not ba1:
        reasons.append("No valid ACMG/AMP criteria were supplied; posterior equals prior.")
    if ba1 and has_path:
        reasons.append("BA1 coexists with pathogenic evidence; BA1 overrides by rule, but this "
                       "conflict needs expert review (e.g. ClinGen SVI BA1 exception list).")
    elif has_path and has_benign:
        reasons.append("Pathogenic and benign evidence coexist; the model combines them, but "
                       "independent expert review is advised.")
    if rejected:
        reasons.append(f"{len(rejected)} evidence item(s) were rejected and did not affect the score.")
    if not calibrated:
        reasons.append("Non-default prior: the paper calibrated its bands at prior 0.10.")
    if label == VUS:
        reasons.append("VUS is not actionable and must not be treated as pathogenic or benign.")

    return {
        "classification": label,
        "classification_basis": basis,
        "points": points,
        "combined_odds_of_pathogenicity": combined_op,
        "posterior_probability_pathogenic": posterior,
        "posterior_excludes_ba1": bool(ba1),
        "prior_probability": prior_probability,
        "accepted_evidence": accepted,
        "stand_alone_evidence": ba1,
        "rejected_evidence": rejected,
        "directional_conflict": has_path and has_benign,
        "uncertainty": {"is_vus": label == VUS, "reasons": reasons or ["No model-specific warning."]},
        "model_provenance": MODEL_PROVENANCE,
    }
