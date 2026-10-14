"""Row 405, Messaging Framework (PARTIAL: one exact priority rule): check a ranked list of key messages.

check_framework(messages) takes messages as a list of 0 to 8 tuples (rank, label, text): rank an exact int from 1 to 8,
label 1 to 24 lowercase identifier characters, text an exact string of 1 to 120 characters. The rules, applied to each
message i (0-based), are:
  a rank already used by an earlier message, else (i, 'rank_repeat');
  a label already used by an earlier message, else (i, 'same_label');
  the same text as an earlier message, else (i, 'repeat');
  more than 25 words in the text, else (i, 'too_long').
One message can break several rules; all are reported. It returns {'problems': sorted (index, code), 'ordered': the
labels sorted by (rank, index), 'top': the first label in that order or None when the list is empty}.
Order of checks: messages (list type, count, then each in order: tuple type, 3 items, rank type and range, label type
and shape, text type and length), and only then the rules.

NOT_CLAIMED: this checks a supplied ranked list. It does not say the messages are persuasive, that the ranking is the
right one, or that any audience read them. No clinical or wet-lab claim.
"""
import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def check_framework(messages):
    if type(messages) is not list:
        raise TypeError('messages must be an exact list')
    if len(messages) > 8:
        raise ValueError('message count must be at most 8')
    for m in messages:
        if type(m) is not tuple:
            raise TypeError('each message must be an exact tuple')
        if len(m) != 3:
            raise ValueError('each message must have 3 items')
        if type(m[0]) is not int:
            raise TypeError('rank must be an exact int')
        if not 1 <= m[0] <= 8:
            raise ValueError('rank must be between 1 and 8')
        if type(m[1]) is not str:
            raise TypeError('label must be an exact string')
        if LABEL.fullmatch(m[1]) is None:
            raise ValueError('label must be 1 to 24 lowercase identifier characters')
        if type(m[2]) is not str:
            raise TypeError('text must be an exact string')
        if not 1 <= len(m[2]) <= 120:
            raise ValueError('text length must be 1 to 120 characters')
    problems = []
    seen_ranks = set()
    seen_labels = set()
    seen_texts = set()
    for i, (rank, label, text) in enumerate(messages):
        if rank in seen_ranks:
            problems.append((i, 'rank_repeat'))
        seen_ranks.add(rank)
        if label in seen_labels:
            problems.append((i, 'same_label'))
        seen_labels.add(label)
        if text in seen_texts:
            problems.append((i, 'repeat'))
        seen_texts.add(text)
        if len(text.split()) > 25:
            problems.append((i, 'too_long'))
    ordered = [label for _, _, label in sorted((r, i, l) for i, (r, l, _) in enumerate(messages))]
    return {'problems': sorted(problems), 'ordered': ordered, 'top': ordered[0] if ordered else None}
