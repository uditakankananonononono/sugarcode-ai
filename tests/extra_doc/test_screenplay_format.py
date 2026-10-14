import random
import textwrap
import pytest
from sugarcode.extra_doc.screenplay_format import format_screenplay as fmt

SAMPLE = [('scene_heading', 'int. kitchen - day'), ('action', 'Mara pours coffee. ' * 5), ('character', 'mara'),
          ('parenthetical', 'quietly'), ('dialogue', 'We are out of time and I know it, but we keep pretending.'),
          ('transition', 'cut to:')]


def test_hand_case_exact_text():
    r = fmt(SAMPLE)
    assert r['lines'] == [
        'INT. KITCHEN - DAY', '',
        'Mara pours coffee. Mara pours coffee. Mara pours coffee.',
        'Mara pours coffee. Mara pours coffee.', '',
        ' ' * 20 + 'MARA', ' ' * 15 + '(quietly)',
        ' ' * 10 + 'We are out of time and I know it,', ' ' * 10 + 'but we keep pretending.', '',
        ' ' * 53 + 'CUT TO:']
    assert r['text'] == '\n'.join(r['lines']) and r['line_count'] == 11 and r['pages'] == 1 and r['elements'] == 6


def _expected(items):
    # independent builder: textwrap for wrapping, layout spelled out per kind
    out, prev = [], None
    for kind, text in items:
        text = ' '.join(text.split())
        block_continues = prev in ('character', 'parenthetical') or (prev == 'dialogue' and kind == 'parenthetical')
        if out and not block_continues:
            out.append('')
        if kind == 'transition':
            out.append(text.upper().rjust(60))
        elif kind == 'character':
            out.append(' ' * 20 + text.upper())
        else:
            body = text.upper() if kind == 'scene_heading' else text
            if kind == 'parenthetical' and not (body[0] == '(' and body[-1] == ')'):
                body = '(' + body + ')'
            width, ind = {'scene_heading': (60, 0), 'action': (60, 0), 'parenthetical': (25, 15), 'dialogue': (35, 10)}[kind]
            out += [' ' * ind + l for l in textwrap.wrap(body, width, break_long_words=True, break_on_hyphens=False)]
        prev = kind
    return out


WORDS = 'the a night door she he runs quiet storm letter will not go home why because remember never always'.split()


def _random_script(rnd):
    def words(n):
        return ' '.join(rnd.choice(WORDS) for _ in range(n))
    items = [('scene_heading', rnd.choice(['INT.', 'ext.', 'I/E.', 'EST.', 'INT./EXT.']) + ' ' + words(rnd.randint(1, 4)))]
    for _ in range(rnd.randint(0, 12)):
        k = rnd.choice(['action', 'dialogue_block', 'transition', 'scene_heading'])
        if k == 'action':
            items.append(('action', words(rnd.randint(1, 30))))
        elif k == 'transition':
            items.append(('transition', words(rnd.randint(1, 2)) + rnd.choice([':', '.'])))
        elif k == 'scene_heading':
            items.append(('scene_heading', 'EXT. ' + words(2)))
        else:
            items.append(('character', words(1)))
            if rnd.random() < 0.5:
                items.append(('parenthetical', words(rnd.randint(1, 5))))
            items.append(('dialogue', words(rnd.randint(1, 25))))
            if rnd.random() < 0.3:
                items.append(('parenthetical', '(' + words(2) + ')'))
                items.append(('dialogue', words(rnd.randint(1, 9))))
    return items


def test_independent_oracle_random_scripts():
    rnd = random.Random(75)
    for _ in range(300):
        items = _random_script(rnd)
        r = fmt(items)
        exp = _expected(items)
        assert r['lines'] == exp
        assert r['line_count'] == len(exp) and r['pages'] == max(1, -(-len(exp) // 55))
        assert all(len(l) <= 60 and l == l.rstrip() for l in exp if l)


def test_page_count_edges_and_long_words():
    one = [('scene_heading', 'INT. A - DAY')] + [('action', 'x')] * 26        # 1 + 26 * 2 - 1 = 52 lines... computed below
    r = fmt(one)
    assert r['line_count'] == 1 + 26 * 2 and r['pages'] == 1
    r = fmt(one + [('action', 'y')])
    assert r['line_count'] == 55 and r['pages'] == 1
    r = fmt(one + [('character', 'a'), ('dialogue', 'b')])
    assert r['line_count'] == 56 and r['pages'] == 2
    r = fmt(one + [('action', 'y'), ('action', 'z')])
    assert r['line_count'] == 57 and r['pages'] == 2
    # an overlong word is cut into 60 character pieces; a short remainder can share a line with the next word
    r = fmt([('scene_heading', 'INT. A - DAY'), ('action', 'a ' + 'x' * 130 + ' b')])
    assert r['lines'][2:] == ['a', 'x' * 60, 'x' * 60, 'x' * 10 + ' b']
    r = fmt([('scene_heading', 'INT. A - DAY'), ('action', 'x' * 120)])
    assert r['lines'][2:] == ['x' * 60, 'x' * 60]
    r = fmt([('scene_heading', 'INT. A - DAY'), ('action', 'x' * 60 + ' y')])
    assert r['lines'][2:] == ['x' * 60, 'y']
    assert fmt([('scene_heading', 'INT. A')])['pages'] == 1


def test_boundaries_of_text_and_name_length():
    base = [('scene_heading', 'INT. A - DAY')]
    assert fmt(base + [('action', 'a' * 500)])
    assert fmt(base + [('character', 'A' * 30), ('dialogue', 'hi')])
    assert fmt(base * 200)['elements'] == 200
    assert fmt(base + [('action', ' a   b c ')])['lines'][-1] == 'a b c'
    assert fmt(base + [('character', 'bob (v.o.)'), ('dialogue', 'hi')])['lines'][-2] == ' ' * 20 + 'BOB (V.O.)'
    assert fmt(base + [('character', 'bob'), ('parenthetical', '(already)'), ('dialogue', 'hi')])['lines'][-2] == ' ' * 15 + '(already)'
    assert fmt(base + [('transition', 'FADE OUT.')])['lines'][-1].endswith('FADE OUT.')
    for prefix in ('INT.', 'EXT.', 'INT./EXT.', 'I/E.', 'EST.', 'int.', 'Int./Ext.'):
        assert fmt([('scene_heading', prefix + ' x')])['lines'][0] == (prefix + ' x').upper()


BASE = [('scene_heading', 'INT. A - DAY')]


@pytest.mark.parametrize('arg,err,msg', [
    ('x', TypeError, 'elements must be a list or tuple'),
    ([], ValueError, 'element count must be between 1 and 200'),
    (BASE * 201, ValueError, 'element count must be between 1 and 200'),
    (['x'], TypeError, r'each element must be a \(kind, text\) pair'),
    ([('action', 'a', 'b')], TypeError, r'each element must be a \(kind, text\) pair'),
    ([('action', 5)], TypeError, 'kind and text must be str'),
    ([(5, 'a')], TypeError, 'kind and text must be str'),
    ([('shout', 'a')], ValueError, 'element 1: unknown kind'),
    (BASE + [('action', 'caf\u00e9')], ValueError, 'element 2: text must be printable ASCII'),
    (BASE + [('action', 'a\x00b')], ValueError, 'element 2: text must be printable ASCII'),
    (BASE + [('action', '   ')], ValueError, 'element 2: text must be 1 to 500 characters'),
    (BASE + [('action', 'a' * 501)], ValueError, 'element 2: text must be 1 to 500 characters'),
    ([('action', 'a')], ValueError, 'element 1: the first element must be a scene_heading'),
    ([('scene_heading', 'KITCHEN')], ValueError, 'element 1: scene_heading must start with INT., EXT., INT./EXT., I/E. or EST.'),
    ([('scene_heading', 'INT.KITCHEN')], ValueError, 'element 1: scene_heading must start with INT., EXT., INT./EXT., I/E. or EST.'),
    (BASE + [('character', 'A' * 31), ('dialogue', 'hi')], ValueError, 'element 2: character name must be at most 30 characters'),
    (BASE + [('transition', 'CUT TO')], ValueError, "element 2: transition must end with ':' or '.'"),
    (BASE + [('dialogue', 'hi')], ValueError, 'element 2: dialogue must follow a character or parenthetical'),
    (BASE + [('action', 'x'), ('dialogue', 'hi')], ValueError, 'element 3: dialogue must follow a character or parenthetical'),
    (BASE + [('parenthetical', 'x')], ValueError, 'element 2: parenthetical must follow a character or dialogue'),
    (BASE + [('character', 'A'), ('action', 'x')], ValueError, 'element 2: a character must be followed by a parenthetical or dialogue'),
    (BASE + [('character', 'A')], ValueError, 'element 2: a character must be followed by a parenthetical or dialogue'),
    (BASE + [('character', 'A'), ('parenthetical', 'x'), ('action', 'y')], ValueError, 'element 3: a parenthetical must be followed by dialogue'),
    (BASE + [('character', 'A'), ('parenthetical', 'x')], ValueError, 'element 3: a parenthetical must be followed by dialogue'),
    (BASE + [('character', 'A'), ('dialogue', 'x'), ('character', 'B'), ('character', 'C')], ValueError, 'element 4: a character must be followed by a parenthetical or dialogue'),
])
def test_exact_errors(arg, err, msg):
    with pytest.raises(err, match='^' + msg + '$'):
        fmt(arg)


def test_checks_run_before_any_formatting_and_report_the_first_problem():
    bad = BASE + [('action', 'ok'), ('dialogue', 'x'), ('shout', 'y')]
    with pytest.raises(ValueError, match='^element 4: unknown kind$'):      # kinds are checked before structure
        fmt(bad)
    bad = BASE + [('dialogue', 'x'), ('action', 'caf\u00e9')]
    with pytest.raises(ValueError, match='^element 3: text must be printable ASCII$'):  # text before structure
        fmt(bad)


def test_tabs_and_newlines_are_refused():
    for bad in ('a\tb', 'a\nb', 'a\rb'):
        with pytest.raises(ValueError, match='^element 2: text must be printable ASCII$'):
            fmt(BASE + [('action', bad)])


H = ('scene_heading', 'INT. A')


def body(kind, text):
    """Lines produced by one element of `kind`, with a legal context around it."""
    ctx = {'action': [H], 'scene_heading': [H], 'parenthetical': [H, ('character', 'a')],
           'dialogue': [H, ('character', 'a')]}[kind]
    els = ctx + [(kind, text)]
    if kind == 'parenthetical':
        els.append(('dialogue', 'z'))
    lines = fmt(els)['lines']
    skip = {'action': 2, 'scene_heading': 2, 'parenthetical': 3, 'dialogue': 3}[kind]
    n_after = 1 if kind == 'parenthetical' else 0
    return lines[skip:len(lines) - n_after]


def test_exact_wrap_widths_per_kind():
    for kind, width, indent in [('action', 60, 0), ('scene_heading', 60, 0), ('parenthetical', 25, 15), ('dialogue', 35, 10)]:
        inner = width - 2 if kind == 'parenthetical' else width
        pre = 'INT. ' if kind == 'scene_heading' else ''
        k = inner - len(pre)
        fits = body(kind, pre + 'a' * (k - 2) + ' b')
        assert len(fits) == 1 and len(fits[0]) - indent == (inner + 2 if kind == 'parenthetical' else inner)
        assert len(body(kind, pre + 'a' * (k - 1) + ' b')) == 2
    assert body('parenthetical', 'x' * 23) == [' ' * 15 + '(' + 'x' * 23 + ')']


def test_element_and_text_caps_exact():
    fmt([H] + [('action', 'a')] * 199)
    with pytest.raises(ValueError) as e:
        fmt([H] + [('action', 'a')] * 200)
    assert str(e.value) == 'element count must be between 1 and 200'
    fmt([H, ('action', 'a' * 500)])
    with pytest.raises(ValueError):
        fmt([H, ('action', 'a' * 501)])


def test_character_class_edges():
    assert fmt([H, ('action', '~ !')])['lines'][-1] == '~ !'
    for bad in ('\x1f', '\x7f', '\u00e9'):
        with pytest.raises(ValueError) as e:
            fmt([H, ('action', 'a' + bad)])
        assert str(e.value) == 'element 2: text must be printable ASCII'


def test_parenthetical_bracket_rule():
    for t, want in [('(a', '((a)'), ('a)', '(a))'), ('(a)', '(a)'), ('a', '(a)')]:
        assert body('parenthetical', t) == [' ' * 15 + want]


def test_long_transition_refused_at_61_accepted_at_60():
    ok = 'a' * 59 + ':'
    assert fmt([H, ('transition', ok)])['lines'][-1] == ok.upper()
    bad = 'a' * 60 + ':'
    with pytest.raises(ValueError) as e:
        fmt([H, ('transition', bad)])
    assert str(e.value) == 'element 2: transition must be at most 60 characters'
    with pytest.raises(ValueError) as e:  # length is checked before the ending rule
        fmt([H, ('transition', 'a' * 70)])
    assert str(e.value) == 'element 2: transition must be at most 60 characters'
