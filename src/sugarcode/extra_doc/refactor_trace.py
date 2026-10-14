"""Row 689: Refactoring - Improves without changing behavior.

PARTIAL: compares supplied before/after integer traces position by
position. Returns first differing position, including missing positions
when lengths differ. No behavior equivalence proof, code transformation
or quality improvement. Caps of 0-30 trace entries and values -1000 to
1000 are this module's own choices, not a domain standard.
"""
MAX_TRACE = 30
LIMIT = 1000
NOT_CLAIMED = ('behavior_equivalence', 'code_transformation', 'quality_improvement')


def compare(before, after):
    for name,trace in (('before',before),('after',after)):
        if type(trace) is not tuple or not 0 <= len(trace) <= MAX_TRACE:
            raise ValueError(f'{name}: tuple of 0 to 30 entries required')
        for i,value in enumerate(trace):
            if type(value) is not int or not -LIMIT <= value <= LIMIT:
                raise ValueError(f'{name}[{i}]: whole number -1000 to 1000 required')
    differences = tuple(i for i in range(max(len(before),len(after)))
                        if i >= len(before) or i >= len(after) or before[i] != after[i])
    return {'refactor_trace_validated': False, 'not_claimed': NOT_CLAIMED,
            'difference_positions': differences,
            'first_difference': differences[0] if differences else None,
            'same_trace': not differences, 'length_change': len(after) - len(before)}
