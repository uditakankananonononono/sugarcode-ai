"""Row499 Pitch Deck Creation - Crafts investor presentation.
Supplied-data helper only. Rows (label, section 0..5 = problem/solution/market/team/traction/ask, slides 0..10). Return slides per section and section indexes with zero slides.
Rows are exact lists or tuples, 1..32; labels are 1..24 ASCII word characters.
NOT_CLAIMED: an effective pitch, investor response or external effects.
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


def analyze_pitch_sections(rows):
    _rows(rows, 'sections', 32, 3)
    for row in rows:
        _label(row[0])
        _integer(row[1], 0, 5)
        _integer(row[2], 0, 10)
    if len({row[0] for row in rows}) != len(rows):
        raise ValueError('section labels must be unique')
    slides=[0,0,0,0,0,0]
    for row in rows:
        slides[row[1]]+=row[2]
    return {'slides':slides,'missing':[index for index,value in enumerate(slides) if value==0],'pitch_effective':False}
