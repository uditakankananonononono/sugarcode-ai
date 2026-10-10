"""Structural findings only; no notebook execution or schema certification."""
from sugarcode.report import new_notebook, validate_notebook


def test_exact_ordered_structural_problems():
    assert validate_notebook({'nbformat': 3, 'cells': [5,
        {'cell_type': 'alien', 'source': 5}, {'cell_type': 'code', 'source': 'x'}]}) == [
        'nbformat must be 4', 'nbformat_minor missing or not an int',
        'cell 0 is not an object', "cell 1: invalid cell_type 'alien'",
        'cell 1: source must be a string or list of strings',
        'cell 2: code cell needs an outputs list',
        'cell 2: code cell needs execution_count',
    ]


def test_raw_cell_literal_source_segments_and_no_code_fields():
    nb = new_notebook([{'cell_type': 'raw', 'source': 'first\nsecond\n'}])
    assert nb['cells'] == [{'cell_type': 'raw', 'metadata': {},
                           'source': ['first\n', 'second\n']}]


def test_source_list_non_string_member_exact_problem():
    assert validate_notebook({'nbformat': 4, 'nbformat_minor': 5,
        'cells': [{'cell_type': 'markdown', 'source': ['x', 5]}]}) == [
        'cell 0: source must be a string or list of strings']
