"""Row 473: Change Management - Guides transitions.

PARTIAL: reports the first supplied checkpoint reaching a target adopter
count, consecutive gains, and remaining people to target. Counts must
be nondecreasing and no greater than a supplied population. No transition
management, adoption prediction or readiness inference. Caps of 1-20
checkpoints and population 1-10000 are this module's own choices.
"""
MAX_CHECKPOINTS = 20
MAX_POPULATION = 10000
NOT_CLAIMED = ('transition_management', 'adoption_prediction', 'readiness')


def checkpoints(adopters, population, target):
    if type(adopters) is not tuple or not 1 <= len(adopters) <= MAX_CHECKPOINTS:
        raise ValueError('adopters: tuple of 1 to 20 counts required')
    if type(population) is not int or not 1 <= population <= MAX_POPULATION:
        raise ValueError('population: whole number 1 to 10000 required')
    if type(target) is not int or not 0 <= target <= population:
        raise ValueError('target: whole number 0 to population required')
    for i,value in enumerate(adopters):
        if type(value) is not int or not 0 <= value <= population:
            raise ValueError(f'adopters[{i}]: whole number 0 to population required')
    for i in range(1,len(adopters)):
        if adopters[i] < adopters[i-1]:
            raise ValueError(f'adopters[{i}]: count must not decrease')
    reached = tuple(i for i in range(len(adopters)) if adopters[i] >= target)
    gains = tuple(adopters[i] - adopters[i-1] for i in range(1,len(adopters)))
    remaining = target - adopters[-1] if adopters[-1] < target else 0
    return {'adoption_checkpoints_validated': False, 'not_claimed': NOT_CLAIMED,
            'first_reached': reached[0] if reached else None,
            'gains': gains, 'remaining': remaining, 'reached': bool(reached)}
