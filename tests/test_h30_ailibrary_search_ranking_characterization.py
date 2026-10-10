"""H30 (replacement) characterization of sugarcode.llm.ailibrary.search() ranking, current behavior.

AUTHORED BY READING ONLY, NOT RUN. Source read at 4fb00691: ailibrary.py 1-97 in full.
Findings only. index() is replaced by a fixed list; _get and tool raise so no network is possible;
CACHE points into tmp_path so ~/.cache is never touched.
"""
import pytest

from sugarcode.llm import ailibrary

INDEX = ["ai-image-generator", "image", "imaged", "photo-editor"]
BASE = "https://www.theailibrary.co/tool/"


def _item(slug):
    return {"slug": slug, "url": BASE + slug}


@pytest.fixture
def fixed(monkeypatch, tmp_path):
    def no_net(*a, **k):
        raise AssertionError("network or tool() access is not allowed here")
    monkeypatch.setattr(ailibrary, "_get", no_net)
    monkeypatch.setattr(ailibrary, "tool", no_net)
    monkeypatch.setattr(ailibrary, "CACHE", tmp_path / "ailibrary.json")

    def use(slugs):
        monkeypatch.setattr(ailibrary, "index", lambda *a, **k: list(slugs))
    use(INDEX)
    return use


def test_scores_exact_segment_2_substring_1_and_nonmatches_dropped(fixed):
    # ai-image-generator 2+2=4, image 2, imaged 1, photo-editor 0 (dropped)
    got = ailibrary.search("image generator", details=False)
    assert got == [_item("ai-image-generator"), _item("image"), _item("imaged")]


def test_tie_breaks_by_length_then_lexicographic(fixed):
    fixed(["bb-xx", "a-xx", "c-xx"])  # all score 2; lengths 5, 4, 4
    got = ailibrary.search("xx", details=False)
    assert [g["slug"] for g in got] == ["a-xx", "c-xx", "bb-xx"]


def test_single_character_words_are_ignored(fixed):
    assert ailibrary.search("a", details=False) == []
    assert ailibrary.search("x y", details=False) == []
    got = ailibrary.search("a image", details=False)
    # image 2 (len 5), ai-image-generator 2 (len 18), imaged 1
    assert [g["slug"] for g in got] == ["image", "ai-image-generator", "imaged"]


def test_limit_one_returns_only_the_top_result(fixed):
    assert ailibrary.search("image generator", limit=1, details=False) == [_item("ai-image-generator")]


def test_limit_zero_returns_empty_list(fixed):
    assert ailibrary.search("image generator", limit=0, details=False) == []


def test_details_true_calls_tool_for_top_two_in_order_only(fixed, monkeypatch):
    calls = []

    def fake_tool(slug):
        calls.append(slug)
        return {"slug": slug}
    monkeypatch.setattr(ailibrary, "tool", fake_tool)
    got = ailibrary.search("image generator", limit=2)
    assert calls == ["ai-image-generator", "image"]
    assert got == [{"slug": "ai-image-generator"}, {"slug": "image"}]
