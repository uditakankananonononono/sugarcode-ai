"""Row 474 Kotter's 8 Steps: exact progress and ordering check over the eight named steps.

The caller supplies eight statuses, one per step in the commonly cited order (1 Create a sense
of urgency, 2 Build a guiding coalition, 3 Form a strategic vision, 4 Enlist a volunteer army, 5
Enable action by removing barriers, 6 Generate short-term wins, 7 Sustain acceleration, 8
Institute change), each an int: 0 not started, 1 in progress, 2 done. Reported: the done and
in-progress counts, the done share (Fraction), the first step not done (number and name, None when
all are done), and the out-of-order steps: a step that is started or done while an earlier step is
not started, so the sequence the model describes was skipped (listed by step number). The
statuses are the caller's. Caps are implementation choices, not spec values.
NOT_CLAIMED: that a status is accurate, that doing the steps in order leads to successful change,
that skipping a step is wrong for this organisation, effects on people or results, employment or
consultation obligations, approval-gate clearance, deployment.
"""
from fractions import Fraction

STEPS = ('Create a sense of urgency', 'Build a guiding coalition', 'Form a strategic vision',
         'Enlist a volunteer army', 'Enable action by removing barriers', 'Generate short-term wins',
         'Sustain acceleration', 'Institute change')
NOT_CLAIMED = ('a status accurate', 'doing the steps in order leads to successful change',
               'skipping a step is wrong for this organisation', 'effects on people or results',
               'employment or consultation obligations', 'approval-gate clearance', 'deployment')


def kotter_progress(statuses):
    if type(statuses) not in (list, tuple):
        raise TypeError('statuses must be a list or tuple')
    if len(statuses) != 8:
        raise ValueError('statuses must hold 8 entries')
    for s in statuses:
        if type(s) is not int:
            raise TypeError('statuses must be nonbool int')
        if s not in (0, 1, 2):
            raise ValueError('statuses must be 0, 1 or 2')
    done = sum(1 for s in statuses if s == 2)
    first = next((i for i, s in enumerate(statuses) if s != 2), None)
    out_of_order = tuple(i + 1 for i, s in enumerate(statuses) if s > 0 and 0 in statuses[:i])
    return {'done': done, 'in_progress': sum(1 for s in statuses if s == 1), 'done_share': Fraction(done, 8),
            'first_not_done': first + 1 if first is not None else None,
            'first_not_done_name': STEPS[first] if first is not None else None,
            'out_of_order': out_of_order, 'change_validated': False, 'not_claimed': NOT_CLAIMED}
