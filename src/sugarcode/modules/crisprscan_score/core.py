"""CRISPRscan on-target activity model and genomic target discovery.

This is the exact additive model published with Moreno-Mateos et al. (2015),
using the 35 nt context ``[6 upstream][20 spacer][NGG PAM][6 downstream]``.
The model was trained for T7-transcribed guides in zebrafish. It is not a
calibrated probability and should not be silently generalized to U6 guides,
other nucleases, or other PAMs.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib.resources import files
import csv
import math
import re
from typing import Iterable

_DNA = re.compile(r"^[ACGT]+$")
_COMPLEMENT = str.maketrans("ACGT", "TGCA")


@dataclass(frozen=True)
class FeatureContribution:
    """One active position-specific feature in the linear model."""

    label: str
    motif: str
    position_1_based: int
    coefficient: float


@dataclass(frozen=True)
class CRISPRscanResult:
    """Auditable result for a single 35 nt context."""

    context: str
    spacer: str
    pam: str
    score: float
    intercept: float
    feature_sum: float
    contributions: tuple[FeatureContribution, ...]
    model: str = "CRISPRscan / Moreno-Mateos 2015"
    applicability: str = "T7-transcribed SpCas9 sgRNAs; trained in zebrafish"

    def to_dict(self) -> dict:
        return asdict(self)


@lru_cache(maxsize=1)
def _coefficients() -> tuple[float, tuple[tuple[str, str, int, float], ...]]:
    """Read and parse the immutable vendored coefficient artifact."""
    path = files(__package__).joinpath("data/coefficients.csv")
    intercept: float | None = None
    features: list[tuple[str, str, int, float]] = []
    with path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            label, value = row["Label"], float(row["Value"])
            if label == "Intercept":
                intercept = value
                continue
            match = re.fullmatch(r"([ACGT]+)(\d{2})", label)
            if not match:
                raise RuntimeError(f"invalid vendored CRISPRscan feature {label!r}")
            motif, position = match.groups()
            features.append((label, motif, int(position), value))
    if intercept is None or len(features) != 91:
        raise RuntimeError("incomplete vendored CRISPRscan model")
    return intercept, tuple(features)


def _normalize_context(context: str) -> str:
    if not isinstance(context, str):
        raise TypeError("context must be a DNA string")
    context = context.upper().replace(" ", "").replace("\n", "")
    if len(context) != 35:
        raise ValueError("CRISPRscan requires exactly 35 nt: 6 + 20 spacer + 3 PAM + 6")
    if not _DNA.fullmatch(context):
        raise ValueError("context must contain only unambiguous A/C/G/T bases")
    if context[27:29] != "GG":
        raise ValueError("CRISPRscan requires a canonical NGG PAM at context positions 27-29")
    return context


def score(context: str) -> CRISPRscanResult:
    """Score one 35 nt CRISPRscan context with an auditable feature breakdown.

    CRISPRscan is a published linear score. Values are normally in [0, 1], but
    clipping would alter the original model, so this implementation returns the
    raw sum and reports out-of-range values unchanged.
    """
    context = _normalize_context(context)
    intercept, features = _coefficients()
    active: list[FeatureContribution] = []
    for label, motif, position, coefficient in features:
        start = position - 1
        if context[start:start + len(motif)] == motif:
            active.append(FeatureContribution(label, motif, position, coefficient))
    feature_sum = math.fsum(item.coefficient for item in active)
    raw_score = intercept + feature_sum
    return CRISPRscanResult(
        context=context,
        spacer=context[6:26],
        pam=context[26:29],
        score=raw_score,
        intercept=intercept,
        feature_sum=feature_sum,
        contributions=tuple(active),
    )


def score_many(contexts: Iterable[str], *, errors: str = "raise") -> list[CRISPRscanResult | None]:
    """Score contexts in order; optionally mark invalid records as Missing.

    ``errors='missing'`` yields ``None`` for an invalid context. It never
    fabricates a score. ``errors='raise'`` is the strict default.
    """
    if errors not in {"raise", "missing"}:
        raise ValueError("errors must be 'raise' or 'missing'")
    results: list[CRISPRscanResult | None] = []
    for context in contexts:
        try:
            results.append(score(context))
        except (TypeError, ValueError):
            if errors == "raise":
                raise
            results.append(None)
    return results


def _reverse_complement(sequence: str) -> str:
    return sequence.translate(_COMPLEMENT)[::-1]


def scan_sequence(sequence: str) -> list[dict]:
    """Discover and score all NGG sites with complete context on both strands.

    Coordinates are zero-based, half-open spacer coordinates on the supplied
    forward sequence. Edge targets lacking the model's complete 6 nt flanks are
    omitted rather than padded or assigned simulated scores.
    """
    if not isinstance(sequence, str):
        raise TypeError("sequence must be a DNA string")
    seq = sequence.upper().replace(" ", "").replace("\n", "")
    if not _DNA.fullmatch(seq):
        raise ValueError("sequence must contain only unambiguous A/C/G/T bases")
    hits: list[dict] = []
    # A context begins six bases before a spacer and is 35 bases long.
    for strand, oriented in (("+", seq), ("-", _reverse_complement(seq))):
        for context_start in range(0, len(oriented) - 34):
            context = oriented[context_start:context_start + 35]
            if context[27:29] != "GG":
                continue
            result = score(context)
            oriented_spacer_start = context_start + 6
            if strand == "+":
                start = oriented_spacer_start
                end = start + 20
            else:
                end = len(seq) - oriented_spacer_start
                start = end - 20
            hits.append({
                "start": start,
                "end": end,
                "strand": strand,
                "spacer": result.spacer,
                "pam": result.pam,
                "context": result.context,
                "score": result.score,
                "model": result.model,
                "applicability": result.applicability,
            })
    return sorted(hits, key=lambda h: (-h["score"], h["start"], h["strand"]))
