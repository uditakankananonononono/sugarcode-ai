"""One literal nonroot cycle, not general graph/annotation validation."""
from copy import deepcopy

from sugarcode.bio import gff


def test_literal_nonroot_cycle_returns_each_descendant_once(monkeypatch):
    real_children = gff.children_of
    calls = []
    def bounded_children(annotation, parent):
        calls.append(parent)
        assert len(calls) <= 6, 'nonroot cycle traversal did not stop'
        return real_children(annotation, parent)
    monkeypatch.setattr(gff, 'children_of', bounded_children)
    a = {'attributes': {'ID': ['a']}}
    b = {'attributes': {'ID': ['b'], 'Parent': ['a', 'c']}}
    c = {'attributes': {'ID': ['c'], 'Parent': ['b']}}
    annotation = {'records': [a, b, c]}
    before = deepcopy(annotation)
    assert gff.descendants_of(annotation, 'a') == [b, c]
    assert calls == ['a', 'b', 'c']
    assert annotation == before
