import pytest
from sugarcode.extra_doc.question_answering import check_systems as ck

NM = 'system must be 1 to 24 lowercase identifier characters'


def test_first_char_z_accepted():
    assert ck([('z', 90, 100)]) == {'problems': [], 'systems': ['z'], 'total': 1}


def test_body_z_accepted():
    assert ck([('az', 90, 100)]) == {'problems': [], 'systems': ['az'], 'total': 1}


def test_interior_uppercase_rejected():
    with pytest.raises(ValueError) as e:
        ck([('aB', 90, 100)])
    assert str(e.value) == NM
