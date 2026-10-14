"""Row 499, Pitch Deck Creation (PARTIAL: one exact deck check): each deck is an exact
tuple (deck, slides, minutes) - deck an exact string of 1 to 24 lowercase identifier
characters, slides an exact integer 0 to 40, minutes an exact integer 0 to 60 of
planned talk time. A deck is checked against two presentation bars, and each bar it
fails adds (index, code) to problems:
  slides below 10, else (i, 'thin_deck');
  minutes over 20, else (i, 'overlong').
Checks run in this order: decks must be an exact list; deck count must be at most 40;
each deck must be an exact tuple; each deck must have 3 items; deck must be an exact
string; deck must be 1 to 24 lowercase identifier characters; slides must be an exact
integer; slides must be 0 to 40; minutes must be an exact integer; minutes must be 0
to 60. Returns {'problems': sorted, 'decks': sorted distinct, 'total': number of
decks}.

NOT_CLAIMED: this checks supplied deck numbers against two presentation bars. It does
not say the presentation persuades, that 10 slides or 20 minutes are the right bars,
or that any investor signs. No clinical or wet-lab claim.
"""

import re

LABEL = re.compile(r'[a-z][a-z0-9_]{0,23}\Z')


def fail(message):
    raise ValueError(message)


def check_decks(decks):
    """Flag decks outside the presentation bars."""
    if type(decks) is not list:
        raise TypeError('decks must be an exact list')
    if len(decks) > 40:
        fail('deck count must be at most 40')
    problems = []
    names = set()
    for i, deck in enumerate(decks):
        if type(deck) is not tuple:
            raise TypeError('each deck must be an exact tuple')
        if len(deck) != 3:
            fail('each deck must have 3 items')
        name, slides, minutes = deck
        if type(name) is not str:
            raise TypeError('deck must be an exact string')
        if not LABEL.match(name):
            fail('deck must be 1 to 24 lowercase identifier characters')
        if type(slides) is not int:
            raise TypeError('slides must be an exact integer')
        if not 0 <= slides <= 40:
            fail('slides must be 0 to 40')
        if type(minutes) is not int:
            raise TypeError('minutes must be an exact integer')
        if not 0 <= minutes <= 60:
            fail('minutes must be 0 to 60')
        if slides < 10:
            problems.append((i, 'thin_deck'))
        if minutes > 20:
            problems.append((i, 'overlong'))
        names.add(name)
    return {'problems': sorted(problems), 'decks': sorted(names), 'total': len(decks)}
