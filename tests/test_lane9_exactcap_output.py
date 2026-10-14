"""Exact-cap output correctness, beyond mere acceptance of 64 rows."""
import importlib
import json
from fractions import Fraction as F
import pytest


def battery(name, mod):
    for size in (63, 64):
        labels = ['r%02d' % i for i in range(size)]
        if name == 'soil_weighted1639':
            rows = [(n, 1, i+1) for i,n in enumerate(labels)]
            got = mod.layers(rows)
            assert got['weighted'] == tuple((n, i+1) for i,n in enumerate(labels))
            expected = size*(size+1)//2
            assert got['weighted_total'] == expected
            assert got['weight_total'] == size
            assert got['mean'] == F(expected,size)
        elif name == 'solar_balance1634':
            rows = [(n, 2*(i+1), 1, 2) for i,n in enumerate(labels)]
            got = mod.balance(rows)
            assert got['balance'] == tuple((n,F(i+1),F(i+1)) for i,n in enumerate(labels))
            expected = size*(size+1)//2
            assert got['reflected_total'] == expected
            assert got['remainder_total'] == expected
            assert got['incoming_total'] == 2*expected
        elif name == 'ocean_limits1635':
            rows = [(n,i+1,1) for i,n in enumerate(labels)]
            got = mod.limits(rows)
            assert got['limits'] == tuple((n,F(i+1)) for i,n in enumerate(labels))
            assert got['supported_units'] == 1
            assert got['limiting'] == (labels[0],)
        else:
            rows = [(n,i+1,1) for i,n in enumerate(labels)]
            got = mod.means(rows)
            assert got['means'] == tuple((n,1,F(i+1)) for i,n in enumerate(labels))
        # A reversed, mixed-container input must preserve the full sorted output.
        mixed = [list(row) if i%2 else row for i,row in enumerate(reversed(rows))]
        fn = {'soil_weighted1639':'layers','solar_balance1634':'balance',
              'ocean_limits1635':'limits','air_weighted1661':'means'}[name]
        assert getattr(mod,fn)(tuple(mixed)) == got


@pytest.mark.parametrize('name', ['soil_weighted1639','solar_balance1634','ocean_limits1635','air_weighted1661'])
def test_exact_cap_preserves_every_result_and_total(name):
    battery(name, importlib.import_module('sugarcode.extra_doc.'+name))
