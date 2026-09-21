"""Exact, auditable CRISPRater linear sgRNA efficacy model."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib.resources import files
import json
import math
import re
from typing import Iterable

_DNA = re.compile(r"^[ACGT]+$")


@dataclass(frozen=True)
class FeatureValue:
    name: str
    value: float
    coefficient: float
    contribution: float


@dataclass(frozen=True)
class CRISPRaterResult:
    spacer: str
    score: float
    efficacy_class: str
    intercept: float
    feature_sum: float
    features: tuple[FeatureValue, ...]
    model: str = "CRISPRater / Labuhn 2018"
    applicability: str = "20-nt SpCas9 spacer; model trained on 426 mammalian-cell sgRNAs"

    def to_dict(self) -> dict:
        return asdict(self)


@lru_cache(maxsize=1)
def _model() -> dict:
    path = files(__package__).joinpath("data/model.json")
    with path.open("r", encoding="utf-8") as handle:
        model = json.load(handle)
    if len(model.get("features", [])) != 10:
        raise RuntimeError("incomplete vendored CRISPRater model")
    return model


def _spacer(value: str) -> str:
    if not isinstance(value, str):
        raise TypeError("spacer must be a DNA string")
    value = value.upper().replace(" ", "").replace("\n", "")
    if len(value) != 20:
        raise ValueError("CRISPRater requires an exact 20 nt spacer")
    if not _DNA.fullmatch(value):
        raise ValueError("spacer must contain only unambiguous A/C/G/T bases")
    return value


def score(spacer: str) -> CRISPRaterResult:
    """Apply the published ten-feature linear model and discrete thresholds."""
    spacer = _spacer(spacer)
    model = _model()
    values: list[FeatureValue] = []
    for feature in model["features"]:
        if feature["kind"] == "gc_fraction":
            segment = spacer[feature["start"] - 1:feature["end"]]
            value = (segment.count("G") + segment.count("C")) / len(segment)
        elif feature["kind"] == "base":
            value = float(spacer[feature["position"] - 1] in feature["bases"])
        else:
            raise RuntimeError(f"unknown CRISPRater feature kind {feature['kind']!r}")
        coefficient = float(feature["coefficient"])
        values.append(FeatureValue(feature["name"], value, coefficient, value * coefficient))
    feature_sum = math.fsum(x.contribution for x in values)
    raw = float(model["intercept"]) + feature_sum
    thresholds = model["classes"]
    efficacy_class = ("low" if raw < thresholds["low_max_exclusive"] else
                      "high" if raw > thresholds["high_min_exclusive"] else "medium")
    return CRISPRaterResult(spacer, raw, efficacy_class, float(model["intercept"]),
                           feature_sum, tuple(values))


def score_many(spacers: Iterable[str], *, errors: str = "raise") -> list[CRISPRaterResult | None]:
    """Score in order; ``errors='missing'`` marks invalid sequences as Missing."""
    if errors not in {"raise", "missing"}:
        raise ValueError("errors must be 'raise' or 'missing'")
    output: list[CRISPRaterResult | None] = []
    for spacer in spacers:
        try:
            output.append(score(spacer))
        except (TypeError, ValueError):
            if errors == "raise":
                raise
            output.append(None)
    return output
