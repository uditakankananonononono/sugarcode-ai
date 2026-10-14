"""Row814 Retrieval Practice - Tests recall.
Supplied exact answer-token pairs only. Rows(label,expected_token,answer_token),
1..32. Tokens exact strings0..24 ASCII word characters;empty allowed. Exact
case-sensitive equality determines matched/mismatched labels and Fraction score.
NOT_CLAIMED: actual recall, semantic correctness, question validity, learning
assessment, grading authority or external effects.
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


def _token(value):
    if type(value) is not str:raise TypeError('answer tokens must be exact strings')
    if len(value)>24 or not value.isascii() or not all(c.isalnum() or c=='_' for c in value):raise ValueError('answer tokens must be 0..24 ASCII word characters')


def compare_answer_tokens(rows):
    _rows(rows,'answers',32,3)
    for label,expected,answer in rows:_label(label);_token(expected);_token(answer)
    if len({r[0] for r in rows})!=len(rows):raise ValueError('answer labels must be unique')
    matched=[label for label,expected,answer in sorted(rows) if expected==answer]
    mismatched=[label for label,expected,answer in sorted(rows) if expected!=answer]
    from fractions import Fraction
    return {'matched':matched,'mismatched':mismatched,'score':Fraction(len(matched),len(rows)),'recall_evaluated':False}
