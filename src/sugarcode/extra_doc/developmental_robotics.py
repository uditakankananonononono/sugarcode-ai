"""Row 943, Developmental Robotics: gating practice by developmental stage.

A developing robot learner can only master the stage directly ahead of
it, the way a child cannot skip from babbling to sentences.  develop()
walks the supplied practice records and, for each learner, advances on a
record at exactly the next stage, counts a repeat at or below the current
stage as review, and counts an attempt further ahead as skipped.

Input rows: (learner 1-8, stage int 0-4).  Each learner starts at stage
0.  Output: {'total', 'advanced', 'review', 'skipped', 'stage': {learner:
final stage}, 'graduated': sorted learners at stage 4}.  Reported: a
record at stage 0 counts as review; attempting stage 3 from stage 1 is
skipped and changes nothing; graduation takes four in-order advances;
a learner that never advances is reported at stage 0.
"""

from typing import Any

MAX_ROWS = 100
MAX_NAME = 8
MIN_STAGE = 0
MAX_STAGE = 4

SCOPE = 'PARTIAL: stage gating only; no motor babbling or reward signals modeled'
NOT_CLAIMED = (
    'does not model intrinsic motivation or curiosity',
    'does not simulate sensorimotor control',
    'does not implement scaffolding from a caregiver',
    'does not regress stages once advanced',
)


def _check_name(learner: Any, row: int, field: str) -> None:
    if not isinstance(learner, str) or type(learner) is not str:
        raise TypeError(
            f'row {row}: {field} must be str, got {type(learner).__name__}')
    if not 1 <= len(learner) <= MAX_NAME:
        raise ValueError(f'row {row}: {field} must be 1-8 chars')


def _check_stage(stage: Any, row: int) -> None:
    if type(stage) is not int:
        raise TypeError(
            f'row {row}: stage must be int, got {type(stage).__name__}')
    if not MIN_STAGE <= stage <= MAX_STAGE:
        raise ValueError(
            f'row {row}: stage must be {MIN_STAGE}-{MAX_STAGE}, got {stage}')


def develop(rows: Any) -> dict:
    """Return the stage-gated practice summary for the supplied records."""
    if type(rows) not in (list, tuple):
        raise TypeError(f'rows must be list or tuple, got {type(rows).__name__}')
    if len(rows) > MAX_ROWS:
        raise ValueError(f'rows must contain at most {MAX_ROWS} entries')
    stages: dict = {}
    advanced = 0
    review = 0
    skipped = 0
    for index, row in enumerate(rows, 1):
        if type(row) not in (list, tuple):
            raise TypeError(
                f'row {index}: expected (learner, stage) tuple, got {type(row).__name__}')
        if len(row) != 2:
            raise ValueError(
                f'row {index}: expected 2 fields, got {len(row)}')
        learner, stage = row
        _check_name(learner, index, 'learner')
        _check_stage(stage, index)
        stages.setdefault(learner, MIN_STAGE)
        current = stages[learner]
        if stage == current + 1:
            advanced += 1
            stages[learner] = stage
        elif stage <= current:
            review += 1
        else:
            skipped += 1
    graduated = sorted(
        learner for learner, stage in stages.items() if stage == MAX_STAGE)
    return {'total': len(rows), 'advanced': advanced, 'review': review,
            'skipped': skipped, 'stage': dict(stages), 'graduated': graduated}
