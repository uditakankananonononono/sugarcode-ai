"""Row 1192: Behavior Change Support.

PARTIAL: summarizes supplied abstract binary values with longest one-run
and zero-to-one transitions. Cap 40 is a module-local choice.
No behavior effectiveness claims, psychological assessment or care advice.
"""
NOT_CLAIMED = ('behavior_effectiveness', 'psychological_assessment', 'care_advice')


def runs(bits):
    if type(bits) is not tuple or not 1 <= len(bits) <= 40:
        raise ValueError('bits: tuple of 1 to 40 integer bits required')
    for i,value in enumerate(bits):
        if type(value) is not int or value not in (0,1):
            raise ValueError(f'bits[{i}]: integer zero or one required')
    longest = 0
    current = 0
    for value in bits:
        current = current+1 if value == 1 else 0
        if current > longest:
            longest = current
    transitions = tuple(i for i in range(1,len(bits)) if bits[i-1] == 0 and bits[i] == 1)
    return {'abstract_bit_runs_validated': False, 'not_claimed': NOT_CLAIMED,
            'longest_one_run': longest, 'start_positions': transitions, 'one_count': sum(bits)}
