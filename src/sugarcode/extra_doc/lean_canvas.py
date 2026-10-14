"""Row 365 Lean Canvas - Rapidly validates ideas: supplied-entry completeness check.

Nine standard blocks each hold 0 to 5 supplied entries of 1 to 64 characters with no control, format, private-use, surrogate or unassigned characters.
Returns per-block entry counts, the empty blocks in canvas order, the number of
filled blocks and whether all nine are filled. Caps are implementation choices.
NOT_CLAIMED: that any idea is validated, customer evidence, market demand,
viability of the entries, researched facts or business execution.
"""
import unicodedata

BLOCKS = ('problem', 'customer_segments', 'unique_value_proposition', 'solution', 'channels',
          'revenue_streams', 'cost_structure', 'key_metrics', 'unfair_advantage')


def _bad(s):
    return any(unicodedata.category(c)[0] == 'C' for c in s)


def check_canvas(blocks):
    if type(blocks) not in (list, tuple):
        raise TypeError('blocks must be a list or tuple')
    if len(blocks) != 9:
        raise ValueError('exactly nine blocks required')
    if any(type(row) not in (list, tuple) or len(row) > 5 for row in blocks):
        raise ValueError('blocks must be lists or tuples of at most five entries')
    if any(type(e) is not str or not 1 <= len(e) <= 64 or _bad(e) for row in blocks for e in row):
        raise ValueError('entries must be strings of length 1 through 64 without control or unassigned characters')
    counts = [len(row) for row in blocks]
    empty = [BLOCKS[i] for i in range(9) if counts[i] == 0]
    return {'counts': counts, 'empty_blocks': empty, 'filled_count': 9 - len(empty),
            'all_filled': not empty, 'idea_validated': False}
