import copy
import itertools
import random
import string

import pytest

from sugarcode.extra_doc import contact_trace1189 as m

NC = [
    'does not identify real contacts',
    'does not estimate infection or exposure risk',
    'does not recommend testing, treatment or quarantine',
    'does not contact people or update public-health records',
]
SCOPE = 'PARTIAL: supplied undirected graph hops only; no exposure assessment'


def oracle(edges, seeds, budget):
    # Independent all-pairs Floyd-Warshall, not a queue traversal.
    nodes = sorted(set(seeds) | {x for e in edges for x in e})
    d = {(a, b): (0 if a == b else 1000) for a in nodes for b in nodes}
    for a, b in edges:
        d[a, b] = d[b, a] = 1
    for k in nodes:
        for a in nodes:
            for b in nodes:
                d[a, b] = min(d[a, b], d[a, k] + d[k, b])
    minima = {a: min(d[s, a] for s in seeds) for a in nodes}
    return {
        'distances': [(a, minima[a]) for a in nodes if minima[a] <= budget],
        'unreached': [a for a in nodes if minima[a] > budget],
        'scope': SCOPE, 'not_claimed': NC,
    }


def test_known_and_freshness():
    edges = [('a', 'b'), ['b', 'c'], ('c', 'd'), ('x', 'y')]
    before = copy.deepcopy(edges)
    result = m.trace_contacts(edges, ['a'])
    assert result == {'distances': [('a', 0), ('b', 1), ('c', 2)],
                      'unreached': ['d', 'x', 'y'], 'scope': SCOPE, 'not_claimed': NC}
    assert edges == before
    result['not_claimed'][0] += 'x'
    result['distances'].append(('fake', 9))
    assert m.trace_contacts(edges, ['a']) == oracle(edges, ['a'], 2)
    assert m.NOT_CLAIMED == tuple(NC)
    assert m.SCOPE == SCOPE
    assert m.trace_contacts([], ['z'], 0) == oracle([], ['z'], 0)
    assert m.trace_contacts(edges, ['d', 'a', 'isolated'], 16) == oracle(edges, ['d', 'a', 'isolated'], 16)


def test_exhaustive_small_graphs():
    pairs = list(itertools.combinations('abcd', 2))
    for mask in range(64):
        edges = [e for i, e in enumerate(pairs) if mask & (1 << i)]
        for seeds in [('a',), ('d',), ('a', 'c')]:
            for budget in range(5):
                assert m.trace_contacts(edges, seeds, budget) == oracle(edges, seeds, budget)


def test_random_graphs():
    rng = random.Random(1189)
    for _ in range(150):
        names = ['0', '_', 'A', 'z', 'id9', 'A_' , 'b', 'q', 'isolated']
        pairs = list(itertools.combinations(names[:-1], 2))
        rng.shuffle(pairs)
        edges = [list(e) if i % 2 else e for i, e in enumerate(pairs[:rng.randrange(29)])]
        seeds = rng.sample(names, rng.randrange(1, 5))
        budget = rng.randrange(17)
        assert m.trace_contacts(tuple(edges), tuple(seeds), budget) == oracle(edges, seeds, budget)


class L(list): pass
class T(tuple): pass
class S(str): pass
class I(int): pass


def refused(exc, message, contacts, seeds=('a',), budget=2):
    with pytest.raises(exc) as e:
        m.trace_contacts(contacts, seeds, budget)
    assert str(e.value) == message


def test_validation_containers():
    for bad in (None, {}, 'ab', L([]), T(())):
        refused(TypeError, 'contacts must be an exact list or tuple', bad)
    refused(ValueError, 'at most 64 contacts required', [None] * 65)
    for bad in (None, {}, 'ab', L(['a','b']), T(('a','b'))):
        refused(TypeError, 'contact must be an exact list or tuple', [bad])
    for bad in ([], ['a'], ['a','b','c']):
        refused(ValueError, 'contact must contain exactly two identifiers', [bad])
    for bad in (None, {}, 'a', L(['a']), T(('a',))):
        refused(TypeError, 'seeds must be an exact list or tuple', [], bad)
    for bad in ([], ['a']*17):
        refused(ValueError, 'seeds must contain 1..16 identifiers', [], bad)
    refused(ValueError, 'self contact is not allowed', [('a','a')])
    refused(ValueError, 'duplicate undirected contact', [('a','b'),('b','a')])
    refused(ValueError, 'seeds must be unique', [], ['a','a'])
    for bad in (True, False, I(2), 2., None, '2'):
        refused(TypeError, 'max_hops must be an exact int', [], ['a'], bad)
    for bad in (-1, 17):
        refused(ValueError, 'max_hops must be 0..16', [], ['a'], bad)


def test_labels_full_printable_unicode():
    alphabet = string.ascii_letters + string.digits + '_'
    for c in string.printable + 'éΑＡЖ🙂\u200b\x00':
        for label in (c, 'a'+c):
            if all(x in alphabet for x in label):
                assert m.trace_contacts([], [label], 0)['distances'] == [(label,0)]
            else:
                refused(ValueError, 'identifier must be 1..24 ASCII word characters', [], [label])
                refused(ValueError, 'identifier must be 1..24 ASCII word characters', [(label,'valid')])
    for bad in (None, 1, b'a', S('a')):
        refused(TypeError, 'identifier must be an exact string', [], [bad])
        refused(TypeError, 'identifier must be an exact string', [(bad,'b')])
        refused(TypeError, 'identifier must be an exact string', [('a',bad)])
    for bad in ('', 'a'*25):
        refused(ValueError, 'identifier must be 1..24 ASCII word characters', [], [bad])
    assert m.trace_contacts([], ['a'*24])['distances'] == [('a'*24,0)]


def test_caps_and_precedence():
    nodes = ['n'+str(i) for i in range(64)]
    edges = list(zip(nodes, nodes[1:]))
    assert len(m.trace_contacts(edges, nodes[:16], 16)['distances']) == 32
    # 64 edges and exactly64 vertices accepted.
    assert m.trace_contacts(edges+[(nodes[0],nodes[-1])], [nodes[0]], 0)['distances'] == [(nodes[0],0)]
    refused(ValueError, 'at most 64 distinct identifiers required', edges, ['new'])
    refused(ValueError, 'at most 64 distinct identifiers required', [(str(i),str(i+1)) for i in range(64)])
    refused(ValueError, 'contact must contain exactly two identifiers', [('a',)], None, None)
    refused(ValueError, 'self contact is not allowed', [('a','a')], None, None)
    refused(ValueError, 'seeds must be unique', [], ['a','a'], None)
    refused(TypeError, 'max_hops must be an exact int', edges, ['new'], None)
    assert m.trace_contacts([('b','a')], ['b'], 0) == oracle([('b','a')], ['b'], 0)


def test_module_disclaimer_exact():
    assert m.__doc__.split('\n\n')[1] == (
        'PARTIAL: enumerate shortest hop distances in a caller-supplied undirected\n'
        'contact graph. No inference about infection, exposure risk, or real people.'
    )
