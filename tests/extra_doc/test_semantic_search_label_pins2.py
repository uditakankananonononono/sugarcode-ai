import pytest
from sugarcode.extra_doc.semantic_search import check_indexes as ck

NM = 'index must be 1 to 24 lowercase identifier characters'


def test_first_char_z_accepted():
    assert ck([('z', 5000, 256)]) == {'problems': [], 'indexes': ['z'], 'total': 1}


def test_body_z_accepted():
    assert ck([('az', 5000, 256)]) == {'problems': [], 'indexes': ['az'], 'total': 1}


def test_interior_uppercase_rejected():
    with pytest.raises(ValueError) as e:
        ck([('aB', 5000, 256)])
    assert str(e.value) == NM
