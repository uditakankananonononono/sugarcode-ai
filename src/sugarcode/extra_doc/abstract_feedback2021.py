"""Row 2021: Cybernetics.

PARTIAL: exact discrete integer proportional feedback recurrence with
supplied initial state, target, gain and step count. Caps local; no physical
control, stability, convergence or safety claim. Gain may overshoot.
"""
NOT_CLAIMED = ('physical_control', 'stability', 'convergence', 'safety')


def feedback(initial, target, gain, steps):
    for name,value in (('initial',initial),('target',target)):
        if type(value) is not int or not -100 <= value <= 100:
            raise ValueError(f'{name}: integer -100 to 100 required')
    if type(gain) is not int or not 0 <= gain <= 2:
        raise ValueError('gain: integer 0 to 2 required')
    if type(steps) is not int or not 1 <= steps <= 20:
        raise ValueError('steps: integer 1 to 20 required')
    states = [initial]
    errors = []
    for _ in range(steps):
        error = target-states[-1]
        errors.append(error)
        states.append(states[-1]+gain*error)
    return {'abstract_feedback_validated': False, 'not_claimed': NOT_CLAIMED,
            'states': tuple(states), 'pre_update_errors': tuple(errors),
            'final_error': target-states[-1], 'final_exact': states[-1] == target}
