"""Peer SC-F02 authored canaries, now run by integration builder."""
import io
from pathlib import Path

import pytest

from sugarcode.self_improve.capped_readers import (
    InputLimitExceeded, read_capped_bytes, read_capped_utf8, read_capped_utf8_lines,
)


def test_exact_file_boundary_accepts_and_next_byte_refuses(tmp_path):
    path = tmp_path / "state.json"
    path.write_bytes(b'{"a":1}')
    assert read_capped_utf8(path, max_file_bytes=7, chunk_bytes=2) == '{"a":1}'
    with pytest.raises(InputLimitExceeded) as error:
        read_capped_utf8(path, max_file_bytes=6, chunk_bytes=2)
    assert (error.value.scope, error.value.limit) == ("file", 6)
    assert path.read_bytes() == b'{"a":1}'


def test_empty_file_zero_budget(tmp_path):
    path = tmp_path / "empty"
    path.write_bytes(b"")
    assert read_capped_bytes(path, max_file_bytes=0) == b""
    assert read_capped_utf8_lines(path, max_file_bytes=0, max_line_bytes=0) == ()
    path.write_bytes(b"\n")
    with pytest.raises(InputLimitExceeded):
        read_capped_bytes(path, max_file_bytes=0)


@pytest.mark.parametrize("chunk_size", [1, 2, 3, 65536])
def test_utf8_split_across_chunks_counts_bytes(tmp_path, chunk_size):
    path = tmp_path / "utf8"
    original = "é🙂\n".encode("utf-8")
    path.write_bytes(original)
    assert read_capped_utf8_lines(path, max_file_bytes=7, max_line_bytes=7,
                                 chunk_bytes=chunk_size) == ("é🙂",)
    with pytest.raises(InputLimitExceeded) as error:
        read_capped_utf8_lines(path, max_file_bytes=7, max_line_bytes=6,
                               chunk_bytes=chunk_size)
    assert error.value.scope == "line"
    assert error.value.line_number == 1
    assert path.read_bytes() == original


@pytest.mark.parametrize("original,expected", [
    (b"", ()), (b"\n", ("",)), (b"\n\n", ("", "")),
    (b"a\n", ("a",)), (b"a\nb", ("a", "b")),
    (b"a\r\nb\r\n", ("a", "b")), (b"a\rb\r", ("a\rb\r",)),
    ("a\u2028b\n".encode(), ("a\u2028b",)),
])
def test_explicit_lf_and_crlf_contract(tmp_path, original, expected):
    path = tmp_path / "rows"
    path.write_bytes(original)
    assert read_capped_utf8_lines(path, max_file_bytes=len(original),
                                 max_line_bytes=len(original), chunk_bytes=1) == expected


def test_crlf_physical_bytes_count_toward_cap(tmp_path):
    path = tmp_path / "rows"
    path.write_bytes(b"a\r\n")
    with pytest.raises(InputLimitExceeded) as error:
        read_capped_utf8_lines(path, max_file_bytes=3, max_line_bytes=2)
    assert error.value.scope == "line"
    assert read_capped_utf8_lines(path, max_file_bytes=3, max_line_bytes=3) == ("a",)


def test_unterminated_final_line_has_same_byte_cap(tmp_path):
    path = tmp_path / "rows"
    path.write_bytes(b"a\n123")
    assert read_capped_utf8_lines(path, max_file_bytes=5, max_line_bytes=3) == ("a", "123")
    with pytest.raises(InputLimitExceeded) as error:
        read_capped_utf8_lines(path, max_file_bytes=5, max_line_bytes=2)
    assert error.value.line_number == 2


def test_many_short_lines_exceed_file_budget(tmp_path):
    path = tmp_path / "rows"
    path.write_bytes(b"a\n" * 10)
    with pytest.raises(InputLimitExceeded) as error:
        read_capped_utf8_lines(path, max_file_bytes=9, max_line_bytes=2)
    assert error.value.scope == "file"


def test_late_oversize_returns_no_partial_rows(tmp_path):
    path = tmp_path / "rows"
    path.write_bytes(b"a\nb\n" + b"x" * 50)
    with pytest.raises(InputLimitExceeded) as error:
        read_capped_utf8_lines(path, max_file_bytes=100, max_line_bytes=4)
    assert error.value.line_number == 3


@pytest.mark.parametrize("original", [b"\xff", b"\xe2\x82", b"\xc0\xaf"])
def test_invalid_utf8_refuses_without_mutation(tmp_path, original):
    path = tmp_path / "bad"
    path.write_bytes(original)
    with pytest.raises(UnicodeDecodeError):
        read_capped_utf8(path, max_file_bytes=len(original))
    with pytest.raises(UnicodeDecodeError):
        read_capped_utf8_lines(path, max_file_bytes=len(original), max_line_bytes=len(original))
    assert path.read_bytes() == original


def test_budget_failure_precedes_utf8_decode(tmp_path):
    path = tmp_path / "bad"
    path.write_bytes(b"\xff" * 100)
    with pytest.raises(InputLimitExceeded):
        read_capped_utf8(path, max_file_bytes=8)
    with pytest.raises(InputLimitExceeded):
        read_capped_utf8_lines(path, max_file_bytes=100, max_line_bytes=8)


def test_bom_preserved_not_guessed_as_codec_policy(tmp_path):
    path = tmp_path / "bom"
    path.write_bytes(b"\xef\xbb\xbf{}")
    assert read_capped_utf8(path, max_file_bytes=5) == "\ufeff{}"


@pytest.mark.parametrize("bad", [True, False, -1, 1.0, "4", None])
def test_file_budgets_must_be_exact_nonnegative_ints(tmp_path, bad):
    with pytest.raises(ValueError):
        read_capped_bytes(tmp_path / "missing", max_file_bytes=bad)


@pytest.mark.parametrize("bad", [True, -1, 1.0, "4", None])
def test_line_budgets_must_be_exact_nonnegative_ints(tmp_path, bad):
    with pytest.raises(ValueError):
        read_capped_utf8_lines(tmp_path / "missing", max_file_bytes=10, max_line_bytes=bad)


@pytest.mark.parametrize("bad", [True, 0, -1, 1.0, "4"])
def test_chunk_size_must_be_exact_positive_int(tmp_path, bad):
    with pytest.raises(ValueError):
        read_capped_bytes(tmp_path / "missing", max_file_bytes=10, chunk_bytes=bad)


class RecordingSource(io.BytesIO):
    def __init__(self, content):
        super().__init__(content)
        self.requests = []
        self.consumed = 0

    def read(self, size=-1):
        self.requests.append(size)
        assert size > 0, "unbounded read forbidden"
        chunk = super().read(size)
        self.consumed += len(chunk)
        return chunk


def install_source(monkeypatch, content):
    source = RecordingSource(content)

    def open_readonly(self, mode, buffering):
        assert mode == "rb"
        assert buffering == 0
        return source

    monkeypatch.setattr(Path, "open", open_readonly)
    return source


def test_file_refusal_reads_only_one_probe_byte(monkeypatch):
    source = install_source(monkeypatch, b"x" * 10000)
    with pytest.raises(InputLimitExceeded):
        read_capped_bytes("unused", max_file_bytes=17, chunk_bytes=4)
    assert source.consumed == 18
    assert max(source.requests) <= 4
    assert source.closed


def test_line_refusal_does_not_read_remaining_file(monkeypatch):
    source = install_source(monkeypatch, b"x" * 10000)
    with pytest.raises(InputLimitExceeded) as error:
        read_capped_utf8_lines("unused", max_file_bytes=20000, max_line_bytes=17)
    assert source.consumed == 18
    assert error.value.line_number == 1
    assert source.closed


def test_short_reads_are_not_mistaken_for_eof(monkeypatch):
    class ShortSource(RecordingSource):
        def read(self, size=-1):
            return super().read(min(size, 1))

    source = ShortSource(b"ab\ncd")
    monkeypatch.setattr(Path, "open", lambda self, mode, buffering: source)
    assert read_capped_utf8_lines("unused", max_file_bytes=5, max_line_bytes=3) == ("ab", "cd")
    assert source.consumed == 5


def test_no_stat_trust_or_full_decode_of_oversize_input(monkeypatch):
    source = install_source(monkeypatch, b"\xff" * 10000)
    monkeypatch.setattr(Path, "stat", lambda *a, **k: pytest.fail("stat must not gate safety"))
    with pytest.raises(InputLimitExceeded):
        read_capped_utf8("unused", max_file_bytes=2)
    assert source.consumed == 3


def test_missing_file_propagates_without_creating_it(tmp_path):
    path = tmp_path / "missing"
    with pytest.raises(FileNotFoundError):
        read_capped_bytes(path, max_file_bytes=10)
    assert not path.exists()
