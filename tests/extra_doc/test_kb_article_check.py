"""Independent structural oracle. No accuracy or solution-quality claim."""
import itertools
import re
import pytest
from sugarcode.extra_doc.kb_article_check import check

class Text(str): pass
class Items(tuple): pass

def oracle(title, sections, tags):
    blanks = []
    count = len(title)
    for pos, body in enumerate(sections):
        count += len(body)
        if not body.strip():
            blanks.append(pos)
    return {'kb_article_check_validated': False,
            'not_claimed': ('accuracy', 'clarity', 'problem_solved'),
            'section_count': len(sections), 'tag_count': len(tags),
            'blank_sections': tuple(blanks), 'total_chars': count,
            'complete': not blanks}

def refuse(args, message):
    with pytest.raises(ValueError, match=re.escape(message) + '$') as exc:
        check(*args)
    assert re.fullmatch(re.escape(message), str(exc.value))

def test_independent_oracle_non_ascii_and_positions():
    alphabet = ('a', 'é', 'ａ', 'Ж', ' ', '\t\n', '\u2003')
    for sections in itertools.product(alphabet, repeat=3):
        for title in alphabet[:4]:
            tags = ('Ж', 'é', 'ａ')
            assert check(title, sections, tags) == oracle(title, sections, tags)
    for sections in ((' ', 'a'), ('a', ' '), (' ', ' '), ('é', 'ａ')):
        assert check('Ж', sections, ('é',)) == oracle('Ж', sections, ('é',))

def test_exact_caps_and_units():
    args = ('é'*80, ('Ж'*2000,)*20, ('ａ'*30,)*8)
    assert check(*args) == oracle(*args)
    args = ('a', ('a', 'b'), ('c',))
    assert check(*args) == oracle(*args)
    for n in (19,20):
        args = ('a', ('Ж',)*n, ('é',)*8)
        assert check(*args) == oracle(*args)

def test_title_types_and_bounds():
    for value in ('', 'a'*81, None, True, 1, [], Text('a')):
        refuse((value, ('a','b'), ('x',)), 'title: text of 1 to 80 characters required')

def test_section_container_types_and_bounds():
    for value in ((), ('a',), ('a',)*21, ['a','b'], Items(('a','b')), None):
        refuse(('a',value,('x',)), 'sections: tuple of 2 to 20 bodies required')

def test_section_body_types_and_bounds():
    for pos in (0,1,19):
        for value in ('', 'a'*2001, None, 1, True, Text('a'), []):
            bodies = ['a']*20; bodies[pos] = value
            refuse(('a',tuple(bodies),('x',)), f'sections[{pos}]: body of 1 to 2000 characters required')

def test_tag_container_types_and_bounds():
    for value in ((), ('a',)*9, ['a'], Items(('a',)), None):
        refuse(('a',('a','b'),value), 'tags: tuple of 1 to 8 entries required')

def test_tag_types_and_bounds():
    for pos in (0,1,7):
        for value in ('', 'a'*31, None, 1, True, Text('a'), []):
            tags = ['a']*8; tags[pos] = value
            refuse(('a',('a','b'),tuple(tags)), f'tags[{pos}]: text of 1 to 30 characters required')

def test_check_order():
    refuse(('', (), ()), 'title: text of 1 to 80 characters required')
    refuse(('a',('bad',)*21, ()), 'sections: tuple of 2 to 20 bodies required')
    refuse(('a',('', 'a'),()), 'sections[0]: body of 1 to 2000 characters required')
    refuse(('a',('a','b'), (None,)*9), 'tags: tuple of 1 to 8 entries required')
