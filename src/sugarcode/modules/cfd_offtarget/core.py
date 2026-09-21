"""Exact, auditable Cutting Frequency Determination (CFD) scoring."""
from __future__ import annotations
from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib.resources import files
import math
import re
from typing import Iterable

_DNA = re.compile(r"^[ACGT]+$")


@dataclass(frozen=True)
class MismatchFactor:
    position_1_based: int
    guide_base: str
    off_target_base: str
    key: str
    weight: float


@dataclass(frozen=True)
class CFDResult:
    guide: str
    off_target: str
    pam: str
    score: float
    pam_weight: float
    mismatch_product: float
    mismatch_count: int
    mismatches: tuple[MismatchFactor, ...]
    model: str = "CFD / Doench 2016"
    interpretation: str = "predicted off-target activity relative to on-target; higher is riskier"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class RiskSummary:
    total_cfd_activity: float
    normalized_specificity: float
    scored_sites: int
    excluded_on_targets: int
    high_risk_sites: int
    pair_scores: tuple[CFDResult, ...]
    aggregation: str = "specificity = 100 / (1 + sum(pairwise CFD activity))"

    def to_dict(self) -> dict:
        return asdict(self)


@lru_cache(maxsize=1)
def _model() -> tuple[dict[str, float], dict[str, float]]:
    base = files(__package__).joinpath("data")
    mismatch: dict[str, float] = {}
    with base.joinpath("mismatch_weights.tsv").open("r", encoding="utf-8") as handle:
        for line in handle:
            key, value = line.split()
            mismatch[key] = float(value)
    pam: dict[str, float] = {}
    with base.joinpath("pam_weights.tsv").open("r", encoding="utf-8") as handle:
        for line in handle:
            key, value = line.split()
            pam[key] = float(value)
    if len(mismatch) != 240 or len(pam) != 16:
        raise RuntimeError("incomplete vendored CFD model")
    return mismatch, pam


def _dna(value: str, length: int, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a DNA string")
    value = value.upper().replace(" ", "").replace("\n", "")
    if len(value) != length:
        raise ValueError(f"{field} must be exactly {length} nt")
    if not _DNA.fullmatch(value):
        raise ValueError(f"{field} must contain only unambiguous A/C/G/T bases")
    return value


def _pam_core(pam: str) -> tuple[str, str]:
    if not isinstance(pam, str):
        raise TypeError("pam must be a DNA string")
    pam = pam.upper()
    if len(pam) == 3 and pam[0] in "ACGTN" and _DNA.fullmatch(pam[1:]):
        return pam, pam[1:]
    if len(pam) == 2 and _DNA.fullmatch(pam):
        return pam, pam
    raise ValueError("pam must be 2 A/C/G/T bases or a 3 nt PAM with optional leading N")


def score(guide: str, off_target: str, pam: str = "NGG") -> CFDResult:
    """Score one 20-nt guide/off-target pair using published CFD matrices.

    Mismatch positions are one-based from the guide's 5' end; position 20 is
    PAM-proximal. The returned score is not rounded, preserving exact products.
    """
    guide = _dna(guide, 20, "guide")
    off_target = _dna(off_target, 20, "off_target")
    pam_label, pam2 = _pam_core(pam)
    mismatch_weights, pam_weights = _model()
    factors: list[MismatchFactor] = []
    for position, (guide_base, off_base) in enumerate(zip(guide, off_target), 1):
        if guide_base == off_base:
            continue
        key = f"{guide_base}{off_base}{position}"
        factors.append(MismatchFactor(position, guide_base, off_base, key, mismatch_weights[key]))
    mismatch_product = math.prod(x.weight for x in factors)
    pam_weight = pam_weights[pam2]
    return CFDResult(guide, off_target, pam_label, mismatch_product * pam_weight,
                     pam_weight, mismatch_product, len(factors), tuple(factors))


def score_many(guide: str, sites: Iterable[tuple[str, str]], *,
               errors: str = "raise") -> list[CFDResult | None]:
    """Score ``(protospacer, PAM)`` pairs; invalid rows can be explicit Missing."""
    if errors not in {"raise", "missing"}:
        raise ValueError("errors must be 'raise' or 'missing'")
    output: list[CFDResult | None] = []
    for site in sites:
        try:
            off_target, pam = site
            output.append(score(guide, off_target, pam))
        except (TypeError, ValueError):
            if errors == "raise":
                raise
            output.append(None)
    return output


def summarize_risk(guide: str, sites: Iterable[tuple[str, str]], *,
                   exclude_exact_on_target: bool = True,
                   high_risk_threshold: float = 0.2) -> RiskSummary:
    """Aggregate caller-supplied genomic candidates without claiming a genome scan.

    ``normalized_specificity`` is an explicitly labeled monotonic summary, not
    part of the pairwise CFD publication. Pair scores remain available for
    inspection. Completeness depends entirely on supplied candidate sites.
    """
    if not 0 <= high_risk_threshold <= 1:
        raise ValueError("high_risk_threshold must be between 0 and 1")
    guide = _dna(guide, 20, "guide")
    results: list[CFDResult] = []
    excluded = 0
    for off_target, pam in sites:
        result = score(guide, off_target, pam)
        if exclude_exact_on_target and result.mismatch_count == 0 and result.pam[-2:] == "GG":
            excluded += 1
        else:
            results.append(result)
    total = math.fsum(x.score for x in results)
    return RiskSummary(total, 100.0 / (1.0 + total), len(results), excluded,
                       sum(x.score >= high_risk_threshold for x in results), tuple(results))
