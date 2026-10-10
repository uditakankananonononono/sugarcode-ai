"""Literal TSV findings, not independent CSV/TSV standard validation."""
from sugarcode.report import to_tsv


def test_tsv_embedded_tab_newline_quote_and_none_exact_literal():
    rows = [{'a': 'x\ty', 'b': None}, {'a': 'line\nbreak', 'b': 'say "hi"'}]
    assert to_tsv(rows, ['a', 'b']) == 'a\tb\n"x\ty"\t\n"line\nbreak"\t"say ""hi"""\n'


def test_tsv_default_sorted_union_and_sparse_cells_exact_literal():
    assert to_tsv([{'b': 1}, {'a': 2}]) == 'a\tb\n\t1\n2\t\n'
