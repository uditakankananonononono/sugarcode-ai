"""Row 275, Screenplay Formatting: exact layout of structured screenplay elements.

Takes a list of (kind, text) elements and returns the formatted monospace lines.
Fixed layout (this module's own choice, a common 10-characters-per-inch layout;
columns are counted from the left margin):
- scene_heading: upper case, must start with INT., EXT., INT./EXT., I/E. or EST.
  followed by a space; column 0, width 60.
- action: column 0, width 60, text as given (whitespace collapsed).
- character: upper case, column 20, at most 30 characters.
- parenthetical: wrapped in ( ) if not already, column 15, width 25.
- dialogue: column 10, width 35.
- transition: upper case, must end in ':' or '.', right aligned to column 60, at most 60 characters (longer is refused, not wrapped).
Blank line between blocks; no blank line inside a character / parenthetical /
dialogue block. Words are wrapped greedily; a word longer than the width starts its
own line and is cut into width-sized pieces (a remainder shorter than the width may
share its line with the next words). Page count = ceil(lines / 55).
Structure rules (each raises ValueError naming the 1-based element number): the first
element is a scene_heading; a character is followed by a parenthetical or dialogue;
a parenthetical follows a character or dialogue and is followed by dialogue;
dialogue follows a character or parenthetical.
Caps: 1 to 200 elements; text printable ASCII (32 to 126), 1 to 500 characters after
whitespace is collapsed. Order of checks: container and element types, kinds, text
characters and lengths, then structure, and only then any formatting.

NOT_CLAIMED: this is one fixed layout, not the layout of any studio, union, software or
standard; no PDF, font, page break placement or rendering; no judgement of whether
the writing is good; no clinical or wet-lab claim.
"""

KINDS = ('scene_heading', 'action', 'character', 'parenthetical', 'dialogue', 'transition')
PREFIXES = ('INT./EXT.', 'INT.', 'EXT.', 'I/E.', 'EST.')
MAX_ELEMENTS, MAX_TEXT, LINES_PER_PAGE, PAGE_WIDTH = 200, 500, 55, 60
INDENT = {'scene_heading': 0, 'action': 0, 'character': 20, 'parenthetical': 15, 'dialogue': 10}
WIDTH = {'scene_heading': 60, 'action': 60, 'parenthetical': 25, 'dialogue': 35}


def _wrap(text, width):
    lines, cur = [], ''
    for word in text.split(' '):
        while len(word) > width:                 # overlong word: cut into width-sized pieces
            if cur:
                lines.append(cur)
                cur = ''
            lines.append(word[:width])
            word = word[width:]
        if not word:
            continue
        if not cur:
            cur = word
        elif len(cur) + 1 + len(word) <= width:
            cur += ' ' + word
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def format_screenplay(elements):
    if type(elements) not in (list, tuple):
        raise TypeError('elements must be a list or tuple')
    if not 1 <= len(elements) <= MAX_ELEMENTS:
        raise ValueError('element count must be between 1 and 200')
    items = []
    for n, e in enumerate(elements, 1):
        if type(e) not in (list, tuple) or len(e) != 2:
            raise TypeError('each element must be a (kind, text) pair')
        kind, text = e
        if type(kind) is not str or type(text) is not str:
            raise TypeError('kind and text must be str')
        if kind not in KINDS:
            raise ValueError('element %d: unknown kind' % n)
        if any(not 32 <= ord(ch) <= 126 for ch in text):
            raise ValueError('element %d: text must be printable ASCII' % n)
        text = ' '.join(text.split())
        if not 1 <= len(text) <= MAX_TEXT:
            raise ValueError('element %d: text must be 1 to 500 characters' % n)
        items.append((kind, text))
    prev = None
    for n, (kind, text) in enumerate(items, 1):
        if n == 1 and kind != 'scene_heading':
            raise ValueError('element 1: the first element must be a scene_heading')
        if kind == 'scene_heading':
            up = text.upper()
            if not any(up.startswith(p + ' ') for p in PREFIXES):
                raise ValueError('element %d: scene_heading must start with INT., EXT., INT./EXT., I/E. or EST.' % n)
        if kind == 'character' and len(text) > 30:
            raise ValueError('element %d: character name must be at most 30 characters' % n)
        if kind == 'transition' and len(text) > PAGE_WIDTH:
            raise ValueError('element %d: transition must be at most 60 characters' % n)
        if kind == 'transition' and text[-1] not in ':.':
            raise ValueError("element %d: transition must end with ':' or '.'" % n)
        if kind == 'dialogue' and prev not in ('character', 'parenthetical'):
            raise ValueError('element %d: dialogue must follow a character or parenthetical' % n)
        if kind == 'parenthetical' and prev not in ('character', 'dialogue'):
            raise ValueError('element %d: parenthetical must follow a character or dialogue' % n)
        if prev == 'character' and kind not in ('parenthetical', 'dialogue'):
            raise ValueError('element %d: a character must be followed by a parenthetical or dialogue' % (n - 1))
        if prev == 'parenthetical' and kind != 'dialogue':
            raise ValueError('element %d: a parenthetical must be followed by dialogue' % (n - 1))
        prev = kind
    if prev == 'character':
        raise ValueError('element %d: a character must be followed by a parenthetical or dialogue' % len(items))
    if prev == 'parenthetical':
        raise ValueError('element %d: a parenthetical must be followed by dialogue' % len(items))
    out, last = [], None
    for kind, text in items:
        if out and not (last in ('character', 'parenthetical') or (last == 'dialogue' and kind == 'parenthetical')):
            out.append('')
        if kind == 'transition':
            out.append(' ' * (PAGE_WIDTH - len(text.upper())) + text.upper())
        elif kind == 'character':
            out.append(' ' * INDENT[kind] + text.upper())
        else:
            body = text.upper() if kind == 'scene_heading' else text
            if kind == 'parenthetical' and not (body.startswith('(') and body.endswith(')')):
                body = '(' + body + ')'
            for line in _wrap(body, WIDTH[kind]):
                out.append(' ' * INDENT[kind] + line)
        last = kind
    return {'lines': out, 'text': '\n'.join(out), 'line_count': len(out),
            'pages': -(-len(out) // LINES_PER_PAGE), 'elements': len(items)}
