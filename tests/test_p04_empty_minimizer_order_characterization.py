"""One combined empty-stream/order precedence finding, authored NOT RUN."""
from sugarcode.bio.kmer import minimizers


def test_literal_empty_valid_stream_returns_before_order_validation():
    assert minimizers('NN', 2, 5, canonical=False, order='md5') == []
