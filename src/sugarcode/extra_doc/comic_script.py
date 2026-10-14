"""Row 277, Comic Script Writing: exact word balance and script layout.

A page is a list of panels; a panel is (description, dialogue) where dialogue is a list
of (speaker, line) balloons. The module counts words exactly and checks the page
against limits the caller supplies:
- max_panels_per_page; max_balloon_words; max_panel_dialogue_words;
- the dialogue share of a page = dialogue words / (dialogue + description words)
  must lie in [min_share, max_share] (exact Fractions).
It returns the script laid out as plain text and every violation by name. Layout:
"PAGE n (k PANELS)" (singular "PANEL" for one), then for each panel "PANEL m",
the description, and "SPEAKER: line" for each balloon (speaker upper-cased), with a
blank line between panels and pages. Words are whitespace-separated tokens.
Caps: 1 to 24 pages, 1 to 9 panels per page and 0 to 6 balloons per panel in the
input, text 1 to 400 printable ASCII characters (speakers 1 to 30), limits 1 to 1000,
shares nonbool int or Fraction in [0, 1] with min_share <= max_share and 32-bit
numerator and denominator. Order of checks: pages in order (each page's structure, then each panel's
text as it is reached), then the three limits, then the shares, and only then any counting.
Descriptions, lines and speakers are whitespace-normalised before lengths are checked.

NOT_CLAIMED: word counts and limits only. It does not judge whether pictures and words
actually work together, whether a description is drawable, or whether the dialogue is
good; no art, lettering, panel layout drawing or storyboard is produced. The limits are
the caller's, not an industry standard. No clinical or wet-lab claim.
"""
from fractions import Fraction

MAX_PAGES, MAX_PANELS, MAX_BALLOONS, MAX_TEXT, MAX_SPEAKER = 24, 9, 6, 400, 30


def _text(v, cap, what):
    if type(v) is not str:
        raise TypeError(what + ' must be str')
    t = ' '.join(v.split())
    if any(not 32 <= ord(c) <= 126 for c in v):
        raise ValueError(what + ' must be printable ASCII')
    if not 1 <= len(t) <= cap:
        raise ValueError('%s must be 1 to %d characters' % (what, cap))
    return t


def _limit(v, name):
    if type(v) is not int:
        raise TypeError(name + ' must be a nonbool int')
    if not 1 <= v <= 1000:
        raise ValueError(name + ' must be between 1 and 1000')


def _share(v):
    if type(v) not in (int, Fraction):
        raise TypeError('shares must be nonbool int or Fraction')
    f = Fraction(v)
    if f.numerator.bit_length() > 32 or f.denominator.bit_length() > 32:
        raise ValueError('rational values must fit 32 bits')
    return f


def check_comic_script(pages, max_panels_per_page, max_balloon_words, max_panel_dialogue_words,
                       min_share, max_share):
    if type(pages) not in (list, tuple):
        raise TypeError('pages must be a list or tuple')
    if not 1 <= len(pages) <= MAX_PAGES:
        raise ValueError('page count must be between 1 and 24')
    clean = []
    for page in pages:
        if type(page) not in (list, tuple):
            raise TypeError('each page must be a list or tuple of panels')
        if not 1 <= len(page) <= MAX_PANELS:
            raise ValueError('each page must have 1 to 9 panels')
        cp = []
        for panel in page:
            if type(panel) not in (list, tuple) or len(panel) != 2:
                raise TypeError('each panel must be a (description, dialogue) pair')
            desc, dia = panel
            if type(dia) not in (list, tuple):
                raise TypeError('dialogue must be a list or tuple of (speaker, line) pairs')
            if len(dia) > MAX_BALLOONS:
                raise ValueError('at most 6 balloons per panel')
            cb = []
            for b in dia:
                if type(b) not in (list, tuple) or len(b) != 2:
                    raise TypeError('dialogue must be a list or tuple of (speaker, line) pairs')
                cb.append((_text(b[0], MAX_SPEAKER, 'speaker'), _text(b[1], MAX_TEXT, 'line')))
            cp.append((_text(desc, MAX_TEXT, 'description'), cb))
        clean.append(cp)
    _limit(max_panels_per_page, 'max_panels_per_page')
    _limit(max_balloon_words, 'max_balloon_words')
    _limit(max_panel_dialogue_words, 'max_panel_dialogue_words')
    lo, hi = _share(min_share), _share(max_share)
    if not (0 <= lo <= 1 and 0 <= hi <= 1):
        raise ValueError('shares must be in [0, 1]')
    if lo > hi:
        raise ValueError('min_share must not exceed max_share')
    lines, violations, stats = [], [], []
    for pn, page in enumerate(clean, 1):
        if pn > 1:
            lines.append('')
        lines.append('PAGE %d (%d PANEL%s)' % (pn, len(page), '' if len(page) == 1 else 'S'))
        dw = sw = 0
        if len(page) > max_panels_per_page:
            violations.append('page %d: more than %d panels' % (pn, max_panels_per_page))
        for qn, (desc, bal) in enumerate(page, 1):
            lines.append('')
            lines.append('PANEL %d' % qn)
            lines.append(desc)
            sw += len(desc.split())
            panel_words = 0
            for bn, (sp, ln) in enumerate(bal, 1):
                lines.append('%s: %s' % (sp.upper(), ln))
                w = len(ln.split())
                panel_words += w
                if w > max_balloon_words:
                    violations.append('page %d panel %d balloon %d: more than %d words' % (pn, qn, bn, max_balloon_words))
            if panel_words > max_panel_dialogue_words:
                violations.append('page %d panel %d: dialogue over %d words' % (pn, qn, max_panel_dialogue_words))
            dw += panel_words
        share = Fraction(dw, dw + sw)
        if share < lo:
            violations.append('page %d: dialogue share below minimum' % pn)
        if share > hi:
            violations.append('page %d: dialogue share above maximum' % pn)
        stats.append({'panels': len(page), 'dialogue_words': dw, 'description_words': sw, 'dialogue_share': share})
    return {'text': '\n'.join(lines), 'pages': stats, 'violations': violations, 'balanced': not violations}
