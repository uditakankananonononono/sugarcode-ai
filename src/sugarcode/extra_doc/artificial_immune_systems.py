"""Row 936, Artificial Immune Systems: selecting supplied cells.

Immune-inspired computing. Each row pairs a cell name of 1 to 8
characters with a response, attack or patrol.
Reported: the two response counts, the row total, and selected
- the name of the cell supplied with the most attack responses,
ties broken by name, or None when no row is an attack. Caps
(checked before any work): 0 to 100 rows.
NOT_CLAIMED: real artificial immune systems, immunology,
immune-inspired computing, optimization, anomaly detection,
production readiness.
"""
SCOPE = 'PARTIAL: response selection over supplied rows, no real immunity'
NOT_CLAIMED = ('real artificial immune systems', 'immunology',
               'immune-inspired computing', 'optimization',
               'anomaly detection', 'production readiness')

MAX_ROWS = 100
MAX_NAME = 8
RESPONSES = ('attack', 'patrol')


def select(cells):
    """Select the named cell with the most attack rows."""
    if type(cells) not in (list, tuple):
        raise TypeError('cells must be a list or tuple')
    if len(cells) > MAX_ROWS:
        raise ValueError('cells must contain at most 100 entries')
    rows = []
    for row in cells:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each row must be a (cell, response) row')
        cell, response = row
        if type(cell) is not str or not 1 <= len(cell) <= MAX_NAME:
            raise ValueError('cell must be a string of 1 to 8 characters')
        if type(response) is not str or response not in RESPONSES:
            raise ValueError("response must be 'attack' or 'patrol'")
        rows.append((cell, response))
    attacks = {}
    for cell, response in rows:
        if response == 'attack':
            attacks[cell] = attacks.get(cell, 0) + 1
    if attacks:
        selected = sorted(attacks, key=lambda c: (-attacks[c], c))[0]
    else:
        selected = None
    attack = sum(1 for cell, response in rows if response == 'attack')
    return {'attack': attack, 'patrol': len(rows) - attack,
            'total': len(rows), 'selected': selected}
