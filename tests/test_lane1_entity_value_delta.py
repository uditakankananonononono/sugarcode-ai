import pytest
from sugarcode.extra_doc.entity_design675 import apply
from sugarcode.extra_doc.value_object676 import FractionValue,make


def test_event_cap_and_extra_field():
    for events,message in [([('a',0,'')]*101,'events must be an exact list with 0..100 entries'),
                           ([('a',0,'',1)],'event must be an id, expected version, value tuple')]:
        with pytest.raises(ValueError) as exc:apply(events)
        assert str(exc.value)==message


def test_value_all_numerator_endpoints_constructor_and_make():
    for numerator in (-1000000,1000000):
        assert make(numerator,1)==FractionValue(numerator,1)
    for numerator in (-1000001,1000001):
        with pytest.raises(ValueError) as exc:make(numerator,1)
        assert str(exc.value)=='inputs exceed bounds or denominator is zero'
        with pytest.raises(ValueError) as exc:FractionValue(numerator,1)
        assert str(exc.value)=='normalized fields exceed bounds'
    assert FractionValue(1,1000000).denominator==1000000
    with pytest.raises(ValueError) as exc:FractionValue(1,1000001)
    assert str(exc.value)=='normalized fields exceed bounds'
