"""Row505 Board Management - Works with directors.
Supplied-data helper only. Rows (label, meeting 0..11, member 0..15, present 0 or 1), unique meeting/member pairs. Quorum holds when present count is strictly more than half of listed seats.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: board effectiveness, legal quorum or external effects.
"""
def _rows(value, name, cap, arity):
    if type(value) not in (list, tuple): raise TypeError(name + ': exact list or tuple required')
    if not 1 <= len(value) <= cap: raise ValueError(name + ': row count outside declared range')
    for row in value:
        if type(row) not in (list, tuple): raise TypeError(name + ': exact list or tuple row required')
        if len(row) != arity: raise ValueError(name + ': wrong row arity')


def _label(value):
    if type(value) is not str: raise TypeError('exact string label required')
    if not 1 <= len(value) <= 24 or not value.isascii() or not all(c.isalnum() or c == '_' for c in value):
        raise ValueError('label must be 1..24 ASCII word characters')


def _integer(value, lo, hi):
    if type(value) is not int: raise TypeError('exact nonbool integer required')
    if not lo <= value <= hi: raise ValueError('integer outside declared range')


def analyze_board_quorum(rows):
    _rows(rows, 'attendances', 32, 4)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 11)
        _integer(row[2], 0, 15)
        _integer(row[3], 0, 1)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('attendance labels must be unique')
    if len({(row[1], row[2]) for row in rows}) != len(rows):
        raise ValueError('meeting members must be unique')
    seats={}
    present={}
    for row in rows:
        seats[row[1]]=seats.get(row[1],0)+1
        present[row[1]]=present.get(row[1],0)+row[3]
    return {'meetings':[(meeting,present[meeting],seats[meeting],2*present[meeting]>seats[meeting]) for meeting in sorted(seats)],'board_effective':False}
