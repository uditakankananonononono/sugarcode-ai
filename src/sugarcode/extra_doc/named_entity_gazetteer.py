"""Row 562, Named Entity Recognition: tagging supplied names found in supplied text.

Identifies entities by lookup. The gazetteer is a dict from a name to its
type. Names are 1 to 40 characters from ASCII letters, digits and single
spaces (no leading or trailing space); types are 1 to 20 character
lowercase ASCII words. Text is a str of 0 to 2000 characters. Scan left
to right; at each position the longest gazetteer name that matches
case-sensitively and sits on word boundaries wins, and the scan resumes
after it, so entities never overlap. A boundary is the text edge or a
character that is not an ASCII letter or digit. Reported: a list of
(start, end, name, type) rows with end exclusive. Caps (checked before
any work): 0 to 50 gazetteer names.
NOT_CLAIMED: statistical or neural recognition, disambiguation, aliases,
coreference, multilingual text, accuracy, production readiness.
"""
SCOPE = 'PARTIAL: longest-match gazetteer lookup over supplied text, no learned recognition'
NOT_CLAIMED = ('statistical or neural recognition', 'disambiguation', 'aliases',
               'coreference', 'multilingual text', 'accuracy',
               'production readiness')

MAX_NAMES = 50
MAX_NAME = 40
MAX_TYPE = 20
MAX_TEXT = 2000
_ALNUM = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
_LOWER = 'abcdefghijklmnopqrstuvwxyz'


def tag(gazetteer, text):
    if type(gazetteer) is not dict:
        raise TypeError('gazetteer must be a dict')
    if len(gazetteer) > MAX_NAMES:
        raise ValueError('gazetteer must contain at most 50 names')
    for name, kind in gazetteer.items():
        if (type(name) is not str or not 1 <= len(name) <= MAX_NAME
                or any(ch not in _ALNUM + ' ' for ch in name)
                or name[0] == ' ' or name[-1] == ' ' or '  ' in name):
            raise ValueError('names must be 1 to 40 characters of letters, digits, single spaces')
        if type(kind) is not str or not 1 <= len(kind) <= MAX_TYPE or any(ch not in _LOWER for ch in kind):
            raise ValueError('types must be 1 to 20 lowercase letters')
    if type(text) is not str:
        raise TypeError('text must be a str')
    if len(text) > MAX_TEXT:
        raise ValueError('text must be at most 2000 characters')
    names = sorted(gazetteer, key=lambda n: (-len(n), n))
    found = []
    i = 0
    while i < len(text):
        hit = None
        if i == 0 or text[i - 1] not in _ALNUM:
            for name in names:
                j = i + len(name)
                if text.startswith(name, i) and (j == len(text) or text[j] not in _ALNUM):
                    hit = name
                    break
        if hit is None:
            i += 1
        else:
            found.append((i, i + len(hit), hit, gazetteer[hit]))
            i += len(hit)
    return found
