"""Experimental task-distinct gap evidence, not a quality probability."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass


@dataclass(frozen=True)
class GapObservation:
    module_slug: str
    signature: str
    task_id: str
    partition: str
    outcome: str
    source_ref: str

    def __post_init__(self) -> None:
        for name in ("module_slug", "signature", "task_id", "source_ref"):
            value = getattr(self, name)
            if type(value) is not str or not value.strip() or len(value) > 512:
                raise ValueError("evidence identifiers must be nonempty bounded strings")
        if type(self.partition) is not str or self.partition not in ("development", "held_out"):
            raise ValueError("evidence partition must be explicit")
        if type(self.outcome) is not str or self.outcome not in ("pass", "fail"):
            raise ValueError("evidence outcome must be pass or fail")


def preview_evidence(module_slug: str, observations: list[GapObservation]) -> list[dict]:
    """Rank reported gaps lexicographically by held-out then development failures.

    A task must have one partition throughout this preview, even across gaps.
    Conflicting outcomes within a gap are refused rather than silently resolved.
    References and identifiers are supplied claims, not authenticated evidence.
    """
    if type(module_slug) is not str or not module_slug.strip():
        raise ValueError("module must be explicit")
    if type(observations) is not list or len(observations) > 10_000:
        raise ValueError("at most 10000 observations in a list")
    tasks: dict[str, str] = {}
    outcomes: dict[tuple[str, str], str] = {}
    grouped: dict[str, list[GapObservation]] = defaultdict(list)
    for observation in observations:
        if type(observation) is not GapObservation:
            raise ValueError("expected GapObservation")
        if observation.module_slug != module_slug:
            raise ValueError("evidence module mismatch")
        if tasks.setdefault(observation.task_id, observation.partition) != observation.partition:
            raise ValueError("task overlaps development and held-out partitions")
        key = (observation.signature, observation.task_id)
        if outcomes.setdefault(key, observation.outcome) != observation.outcome:
            raise ValueError("conflicting task outcomes; provide versioned task identifiers")
        grouped[observation.signature].append(observation)
    result = []
    for signature, rows in grouped.items():
        counts = {
            f"{partition}_{outcome}_tasks": len({r.task_id for r in rows
                if r.partition == partition and r.outcome == outcome})
            for partition in ("development", "held_out") for outcome in ("pass", "fail")
        }
        result.append({"signature": signature, **counts,
                       "reported_observations": len(rows),
                       "distinct_tasks": len({r.task_id for r in rows}),
                       "source_refs": sorted({r.source_ref for r in rows}),
                       "status": "experimental_reported_evidence_not_authenticated",
                       "priority_basis": "held_out_fail_tasks_then_development_fail_tasks"})
    return sorted(result, key=lambda r: (-r["held_out_fail_tasks"],
                                        -r["development_fail_tasks"], r["signature"]))
