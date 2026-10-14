"""Row 935, Whale Optimization: netting supplied bubbles.

Bubble-net feeding-inspired. Each row pairs a whale name of 1
to 8 characters with a bubble, an integer from 0 to 10.
Reported: the row total, the distinct whale count, the bubble
sum, and nets - how many windows of three consecutive rows name
one whale with strictly increasing bubbles. Caps (checked
before any work): 0 to 100 rows.
NOT_CLAIMED: real whale optimization, bubble-net feeding, swarm
intelligence, optimization, marine biology, production
readiness.
"""
SCOPE = 'PARTIAL: bubble windowing over supplied rows, no real whales'
NOT_CLAIMED = ('real whale optimization', 'bubble-net feeding',
               'swarm intelligence', 'optimization', 'marine biology',
               'production readiness')

MAX_ROWS = 100
MAX_NAME = 8
MAX_BUBBLE = 10


def bubble(whales):
    """Count rising bubble windows over named whales."""
    if type(whales) not in (list, tuple):
        raise TypeError('whales must be a list or tuple')
    if len(whales) > MAX_ROWS:
        raise ValueError('whales must contain at most 100 entries')
    rows = []
    for row in whales:
        if type(row) not in (list, tuple) or len(row) != 2:
            raise ValueError('each row must be a (whale, bubble) row')
        whale, amount = row
        if type(whale) is not str or not 1 <= len(whale) <= MAX_NAME:
            raise ValueError('whale must be a string of 1 to 8 characters')
        if type(amount) is not int or not 0 <= amount <= MAX_BUBBLE:
            raise ValueError('bubble must be an integer from 0 to 10')
        rows.append((whale, amount))
    named = set()
    for whale, amount in rows:
        named.add(whale)
    nets = 0
    for i in range(len(rows) - 2):
        (first, one), (second, two), (third, three) = rows[i:i + 3]
        if first == second == third and one < two < three:
            nets += 1
    return {'total': len(rows), 'whales': len(named),
            'bubbles': sum(amount for whale, amount in rows),
            'nets': nets}
