"""Row 472: Business Process Reengineering - Redesigns fundamentally.

PARTIAL: compares adjacent department-index changes in supplied before
and after process sequences. No process redesign, organization outcome
or execution claim. Caps of 1-30 steps in each sequence and department
indices 0-100 are this module's own choices, not a domain standard.
"""
MAX_STEPS = 30
MAX_DEPARTMENT = 100
NOT_CLAIMED = ('process_redesign', 'organization_outcome', 'execution')


def handoffs(before, after):
    for name,sequence in (('before',before),('after',after)):
        if type(sequence) is not tuple or not 1 <= len(sequence) <= MAX_STEPS:
            raise ValueError(f'{name}: tuple of 1 to 30 department indices required')
        for i,value in enumerate(sequence):
            if type(value) is not int or not 0 <= value <= MAX_DEPARTMENT:
                raise ValueError(f'{name}[{i}]: whole number 0 to 100 required')
    old = tuple(i for i in range(1,len(before)) if before[i] != before[i-1])
    new = tuple(i for i in range(1,len(after)) if after[i] != after[i-1])
    return {'handoff_redesign_validated': False, 'not_claimed': NOT_CLAIMED,
            'before_handoffs': old, 'after_handoffs': new,
            'handoffs_saved': len(old) - len(new),
            'steps_saved': len(before) - len(after), 'fewer_handoffs': len(new) < len(old)}
