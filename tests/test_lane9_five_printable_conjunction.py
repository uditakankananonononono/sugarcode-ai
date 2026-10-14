"""Tests-only mixed-character label validation pins for landed rows1641/1642/1643/1645/1646.

Each documented label must consist entirely of printable Unicode characters.
These pins distinguish all from any, without imposing an ASCII label regex.
"""
import importlib
import types
from pathlib import Path
import pytest

CASES = [('renewable_mix1641', 'mix', (2, True), ()),
         ('efficiency_delta1642', 'changes', (2, 1), ()),
         ('transport_load1643', 'trips', (2, 1), ()),
         ('hydrogen_chain1645', 'chain', (1,2), (10,)),
         ('circular_flows1646', 'flows', (2,1), ())]
BAD = ['a\n', '\na', 'a\t', 'a\x00', 'a\x7f', 'Ω\r', '\x0b中', 'É\x1b']
MESSAGE = 'label must be exactstr printable Unicode length1..40'


def _reject(fn, rows):
    try:
        fn(rows)
    except ValueError as exc:
        assert str(exc) == MESSAGE
    else:
        raise AssertionError('mixed printable/nonprintable label accepted')


def _battery(mod, fn_name, tail, extra):
    raw = getattr(mod, fn_name)
    def fn(rows): return raw(rows, *extra)
    for bad in BAD:
        for row_type in (list, tuple):
            for outer in (list, tuple):
                for later in (False, True):
                    rows = ([('valid', *tail)] if later else []) + [row_type((bad, *tail))]
                    _reject(fn, outer(rows))
    # Preserve the actual Unicode-printable contract, including spaces.
    for label in ('a_b', 'a b', ' ', 'Ω中', 'É９！'):
        fn([(label, *tail)])


@pytest.mark.parametrize('name,fn_name,tail,extra', CASES)
def test_every_label_character_must_be_printable(name, fn_name, tail, extra):
    _battery(importlib.import_module('sugarcode.extra_doc.' + name), fn_name, tail, extra)


@pytest.mark.parametrize('name,fn_name,tail,extra', CASES)
def test_previously_surviving_all_to_any_mutant_is_killed(name, fn_name, tail, extra):
    real = importlib.import_module('sugarcode.extra_doc.' + name)
    source = Path(real.__file__).read_text()
    old = 'all(ch.isprintable() for ch in label)'
    assert source.count(old) == 1
    mutant = types.ModuleType('isolated_label_mutant')
    exec(compile(source.replace(old, 'any(ch.isprintable() for ch in label)'), '<mutant>', 'exec'), mutant.__dict__)
    with pytest.raises(AssertionError, match='mixed printable/nonprintable label accepted'):
        _battery(mutant, fn_name, tail, extra)
