"""Two literal Parent-cycle shapes, not general graph/annotation validation."""
from copy import deepcopy

from sugarcode.bio import gff


def test_literal_parent_cycles_exclude_root_and_do_not_repeat(monkeypatch):
    real_children = gff.children_of
    calls = []
    def bounded_children(annotation, parent):
        calls.append(parent)
        assert len(calls) <= 6, 'cycle traversal did not stop'
        return real_children(annotation, parent)
    monkeypatch.setattr(gff, 'children_of', bounded_children)
    a = {'attributes': {'ID': ['a'], 'Parent': ['b']}}
    b = {'attributes': {'ID': ['b'], 'Parent': ['a']}}
    annotation = {'records': [a, b]}
    before = deepcopy(annotation)
    assert gff.descendants_of(annotation, 'a') == [b]
    assert calls == ['a', 'b']
    assert annotation == before
    calls.clear()
    self_cycle = {'records': [{'attributes': {'ID': ['a'], 'Parent': ['a']}}]}
    assert gff.descendants_of(self_cycle, 'a') == []
    assert calls == ['a']
