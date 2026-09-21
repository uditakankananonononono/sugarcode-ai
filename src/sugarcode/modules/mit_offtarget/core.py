"""MIT/Hsu 2013 SpCas9 pairwise off-target and guide specificity scoring."""
from __future__ import annotations

from dataclasses import asdict, dataclass
from functools import lru_cache
from importlib.resources import files
import math
import re
from typing import Iterable

_DNA = re.compile(r"^[ACGT]+$")


@dataclass(frozen=True)
class MITResult:
    guide: str
    off_target: str
    pam: str
    score: float
    mismatch_positions: tuple[int, ...]
    mismatch_count: int
    mean_mismatch_distance: float | None
    position_penalty_product: float
    count_penalty: float
    distance_penalty: float
    pam_penalty: float
    model: str = "MIT / Hsu 2013"

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class SpecificityResult:
    specificity: float
    off_target_sum: float
    scored_sites: int
    excluded_on_targets: int
    pair_scores: tuple[MITResult, ...]
    aggregation: str = "100 / (100 + sum(100 * pairwise MIT score))"

    def to_dict(self) -> dict:
        return asdict(self)


@lru_cache(maxsize=1)
def _model() -> tuple[tuple[float, ...], dict[str, float]]:
    base = files(__package__).joinpath("data")
    positions: dict[int, float] = {}
    with base.joinpath("position_weights.tsv").open("r", encoding="utf-8") as handle:
        next(handle)
        for line in handle:
            pos, weight = line.split()
            positions[int(pos)] = float(weight)
    pams: dict[str, float] = {}
    with base.joinpath("pam_weights.tsv").open("r", encoding="utf-8") as handle:
        for line in handle:
            pam, weight = line.split()
            pams[pam] = float(weight)
    if set(positions) != set(range(1, 21)) or len(pams) != 16:
        raise RuntimeError("incomplete vendored MIT model")
    return tuple(positions[i] for i in range(1, 21)), pams


def _dna(value: str, length: int, field: str) -> str:
    if not isinstance(value, str):
        raise TypeError(f"{field} must be a DNA string")
    value = value.upper().replace(" ", "").replace("\n", "")
    if len(value) != length:
        raise ValueError(f"{field} must be exactly {length} nt")
    if not _DNA.fullmatch(value):
        raise ValueError(f"{field} must contain only unambiguous A/C/G/T bases")
    return value


def score(guide: str, off_target: str, pam: str = "NGG", *, include_distance: bool = True) -> MITResult:
    """Score likelihood of cleavage at one genomic off-target.

    Positions are 1-based from the spacer's 5' end; position 20 is
    PAM-proximal. ``pam`` may be a full 3 nt PAM (only its last two bases enter
    the model) or the two modeled bases. ``N`` is accepted only as the first,
    unmodeled character in a 3 nt PAM.
    """
    guide = _dna(guide, 20, "guide")
    off_target = _dna(off_target, 20, "off_target")
    if not isinstance(pam, str):
        raise TypeError("pam must be a DNA string")
    pam = pam.upper()
    if len(pam) == 3 and (pam[0] in "ACGTN") and _DNA.fullmatch(pam[1:]):
        pam2 = pam[1:]
    elif len(pam) == 2 and _DNA.fullmatch(pam):
        pam2 = pam
    else:
        raise ValueError("pam must be 2 A/C/G/T bases or a 3 nt PAM with optional leading N")
    position_weights, pam_weights = _model()
    mismatches = tuple(i + 1 for i, (a, b) in enumerate(zip(guide, off_target)) if a != b)
    count = len(mismatches)
    position_product = math.prod(1.0 - position_weights[i - 1] for i in mismatches)
    count_penalty = 1.0 if count == 0 else 1.0 / (count * count)
    if count <= 1:
        mean_distance = None if count == 0 else 19.0
        distance_penalty = 1.0
    else:
        mean_distance = (mismatches[-1] - mismatches[0]) / (count - 1)
        distance_penalty = 1.0 / (((19.0 - mean_distance) / 19.0) * 4.0 + 1.0)
    if not include_distance:
        distance_penalty = 1.0
    pam_penalty = pam_weights[pam2]
    value = position_product * count_penalty * distance_penalty * pam_penalty
    return MITResult(guide, off_target, pam, value, mismatches, count, mean_distance,
                     position_product, count_penalty, distance_penalty, pam_penalty)


def score_many(guide: str, sites: Iterable[tuple[str, str]], *,
               include_distance: bool = True, errors: str = "raise") -> list[MITResult | None]:
    """Score ``(protospacer, PAM)`` pairs; invalid rows can be explicit Missing."""
    if errors not in {"raise", "missing"}:
        raise ValueError("errors must be 'raise' or 'missing'")
    output: list[MITResult | None] = []
    for site in sites:
        try:
            off_target, pam = site
            output.append(score(guide, off_target, pam, include_distance=include_distance))
        except (TypeError, ValueError):
            if errors == "raise":
                raise
            output.append(None)
    return output


def aggregate_specificity(guide: str, sites: Iterable[tuple[str, str]], *,
                          exclude_exact_on_target: bool = True) -> SpecificityResult:
    """Compute the established MIT aggregate guide specificity score (0-100).

    Exact spacer + GG PAM sites are excluded by default because they normally
    represent the intended target. Callers must still supply all relevant
    genomic candidates; this function performs no genome search.
    """
    guide = _dna(guide, 20, "guide")
    pair_scores: list[MITResult] = []
    excluded = 0
    for off_target, pam in sites:
        result = score(guide, off_target, pam)
        if exclude_exact_on_target and result.mismatch_count == 0 and result.pam[-2:] == "GG":
            excluded += 1
        else:
            pair_scores.append(result)
    total = math.fsum(x.score for x in pair_scores)
    specificity = 100.0 / (1.0 + total)
    return SpecificityResult(specificity, total, len(pair_scores), excluded, tuple(pair_scores))
