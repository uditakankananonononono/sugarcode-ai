import pytest
from sugarcode.extra_doc.data_lake_design import check_datasets as ck

NM = 'dataset must be 1 to 24 lowercase identifier characters'


def test_first_char_z_accepted():
    assert ck([('z', 1000, 3)]) == {'problems': [], 'datasets': ['z'], 'total': 1}


def test_body_z_accepted():
    assert ck([('az', 1000, 3)]) == {'problems': [], 'datasets': ['az'], 'total': 1}


def test_interior_uppercase_rejected():
    with pytest.raises(ValueError) as e:
        ck([('aB', 1000, 3)])
    assert str(e.value) == NM
