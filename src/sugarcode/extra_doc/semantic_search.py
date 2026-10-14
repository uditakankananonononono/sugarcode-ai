"""Row 568, Semantic Search (PARTIAL: one exact index check): each index is an exact
tuple (index, embeddings, dims) - index an exact string of 1 to 24 lowercase
identifier characters, embeddings an exact integer 0 to 1000000 stored, dims an exact
integer 0 to 4096 per embedding. An index is checked against two meaning bars, and
each bar it fails adds (index, code) to problems:
  embeddings below 1000, else (i, 'underindexed');
  dims below 64, else (i, 'low_dim').
Checks run in this order: indexes must be an exact list; index count must be at most
40; each index must be an exact tuple; each index must have 3 items; index must be an
exact string; index must be 1 to 24 lowercase identifier characters; embeddings must
be an exact integer; embeddings must be 0 to 1000000; dims must be an exact integer;
dims must be 0 to 4096. Returns {'problems': sorted, 'indexes': sorted distinct,
'total': number of indexes}.

NOT_CLAIMED: this checks supplied index numbers against two meaning bars. It does not
say results match meaning, that 1000 embeddings or 64 dims are the right bars, or that
any search succeeds. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_indexes(indexes):
    """Flag indexes outside the meaning bars."""
    if type(indexes) is not list:
        raise TypeError('indexes must be an exact list')
    if len(indexes) > 40:
        fail('index count must be at most 40')
    problems = []
    names = set()
    for i, index in enumerate(indexes):
        if type(index) is not tuple:
            raise TypeError('each index must be an exact tuple')
        if len(index) != 3:
            fail('each index must have 3 items')
        name, embeddings, dims = index
        if type(name) is not str:
            raise TypeError('index must be an exact string')
        if not LABEL.match(name):
            fail('index must be 1 to 24 lowercase identifier characters')
        if type(embeddings) is not int:
            raise TypeError('embeddings must be an exact integer')
        if not 0 <= embeddings <= 1000000:
            fail('embeddings must be 0 to 1000000')
        if type(dims) is not int:
            raise TypeError('dims must be an exact integer')
        if not 0 <= dims <= 4096:
            fail('dims must be 0 to 4096')
        if embeddings < 1000:
            problems.append((i, 'underindexed'))
        if dims < 64:
            problems.append((i, 'low_dim'))
        names.add(name)
    return {'problems': sorted(problems), 'indexes': sorted(names), 'total': len(indexes)}
