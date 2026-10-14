"""Row 937, Artificial Life: feeding supplied cells.

Simulates living systems. Each row pairs a cell name of 1 to 8
characters with a meal, feed or starve.
Reported: the two meal counts, the row total, and starved - the
sorted cells whose energy drops below zero at any supplied row,
where energy starts at zero, feed adds one, and starve takes
one. Caps (checked before any work): 0 to 100 rows.
NOT_CLAIMED: real artificial life, living systems, biology,
simulation, cellular automata, production readiness.
"""
SCOPE = 'PARTIAL: meal walking over supplied rows, no real life'
NOT_CLAIMED = ('real artificial life', 'living systems', 'biology',
               'simulation', 'cellular automata', 'production readiness')

MAX_ROWS = 100
MAX_NAME = 8
MEALS = ('feed', 'starve')


def live(cells):
    """Walk energy over named cells and find starved ones."""
    if type(cells) not in (list, tuple):
        raise TypeError('cells must be a list or tuple')
    if len(cells) > MAX_ROWS:
        raise ValueError('cells must contain at most 100 entries')
    rows = []
    for row in cells:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each row must be a (cell, meal) row')
        cell, meal = row
        if type(cell) is not str or not 1 <= len(cell) <= MAX_NAME:
            raise ValueError('cell must be a string of 1 to 8 characters')
        if type(meal) is not str or meal not in MEALS:
            raise ValueError("meal must be 'feed' or 'starve'")
        rows.append((cell, meal))
    energy = {}
    starved = set()
    for cell, meal in rows:
        level = energy.get(cell, 0) + (1 if meal == 'feed' else -1)
        energy[cell] = level
        if level < 0:
            starved.add(cell)
    feed = sum(1 for cell, meal in rows if meal == 'feed')
    return {'feed': feed, 'starve': len(rows) - feed,
            'total': len(rows), 'starved': sorted(starved)}
