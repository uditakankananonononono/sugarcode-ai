"""Row 464: Fishbone Diagram Creation - Maps causes.

PARTIAL: counts caller-assigned category indices for candidate causes,
reports populated and empty categories, and positions per category.
No diagram rendering, causality or correctness of assignments claimed.
Caps of 1-30 assignments and 1-8 categories are this module's choices.
"""
MAX_ASSIGNMENTS = 30
MAX_CATEGORIES = 8
NOT_CLAIMED = ('diagram_rendering', 'causality', 'assignment_correctness')


def groups(assignments, categories):
    if type(assignments) is not tuple or not 1 <= len(assignments) <= MAX_ASSIGNMENTS:
        raise ValueError('assignments: tuple of 1 to 30 indices required')
    if type(categories) is not int or not 1 <= categories <= MAX_CATEGORIES:
        raise ValueError('categories: whole number 1 to 8 required')
    for i,value in enumerate(assignments):
        if type(value) is not int or not 0 <= value < categories:
            raise ValueError(f'assignments[{i}]: whole number 0 to categories minus 1 required')
    positions = tuple(tuple(i for i in range(len(assignments)) if assignments[i] == category)
                      for category in range(categories))
    counts = tuple(len(p) for p in positions)
    empty = tuple(i for i in range(categories) if counts[i] == 0)
    return {'fishbone_groups_validated': False, 'not_claimed': NOT_CLAIMED,
            'positions': positions, 'counts': counts, 'empty_categories': empty,
            'covered_count': categories - len(empty)}
