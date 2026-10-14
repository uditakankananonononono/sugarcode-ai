import pytest
from sugarcode.extra_doc.natural_language_processing import check_pipelines as ck

NM = 'pipeline must be 1 to 24 lowercase identifier characters'


def test_first_char_z_accepted():
    assert ck([('z', 1000, 5)]) == {'problems': [], 'pipelines': ['z'], 'total': 1}


def test_body_z_accepted():
    assert ck([('az', 1000, 5)]) == {'problems': [], 'pipelines': ['az'], 'total': 1}


def test_interior_uppercase_rejected():
    with pytest.raises(ValueError) as e:
        ck([('aB', 1000, 5)])
    assert str(e.value) == NM
