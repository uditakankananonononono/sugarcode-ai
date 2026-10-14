"""Doc row1758 output list ownership and closed kind literal witness."""
import pytest
from sugarcode.extra_doc.actor_network1758 import audit_network


def test_kinds_container_is_independent_from_input():
    entities=[('a','human'),('b','nonhuman')];links=[('a','b')]
    result=audit_network(entities,links)
    assert result['kinds'] is not entities
    result['kinds'].append(('z','human'))
    result['reachable'].append(('z',[]))
    result['reachable'][0][1].append('z')
    assert entities==[('a','human'),('b','nonhuman')]
    assert links==[('a','b')]
    assert audit_network(entities,links)['reachable']==[('a',['b']),('b',[])]


def test_extra_kind_literal_is_refused_exactly():
    with pytest.raises(ValueError) as exc:audit_network([('a','x'),('b','human')],[])
    assert str(exc.value)=='kind must be an exact human or nonhuman string'
