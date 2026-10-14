from fractions import Fraction
import pytest
from sugarcode.extra_doc import podcast_production as p

P = p.produce


def S(title="t", speaker="A", seconds=60):
    return {"title": title, "speaker": speaker, "seconds": seconds}


def test_constants():
    assert p.MAX_SEGMENTS == 500 and p.STATUS_NOTE.startswith("PARTIAL")


@pytest.mark.parametrize("sec,want", [(0, "0:00:00"), (9, "0:00:09"), (59, "0:00:59"), (60, "0:01:00"),
                                      (3599, "0:59:59"), (3600, "1:00:00"), (3661, "1:01:01"),
                                      (36000, "10:00:00"), (359999, "99:59:59")])
def test_stamp_literals(sec, want):
    assert p.stamp(sec) == want


@pytest.mark.parametrize("bad", [-1, 360000, 1.5, True, "5", None, 2 * 10 ** 9])
def test_stamp_rejects(bad):
    with pytest.raises(ValueError):
        p.stamp(bad)


def test_stamp_messages():
    with pytest.raises(ValueError, match="seconds: must be within"):
        p.stamp(360000)
    with pytest.raises(ValueError, match="seconds: whole number required"):
        p.stamp(1.0)
    with pytest.raises(ValueError, match="magnitude above 1e9"):
        p.stamp(10 ** 9 + 1)
    with pytest.raises(ValueError, match="must be within"):
        p.stamp(10 ** 9)


def test_hand_episode():
    r = P([S("Intro", "A", 90), S("Main", "B", 3510), S("Outro", "A", 60)])
    assert [(c["title"], c["start"], c["stamp"], c["seconds"]) for c in r["chapters"]] == [
        ("Intro", 0, "0:00:00", 90), ("Main", 90, "0:01:30", 3510), ("Outro", 3600, "1:00:00", 60)]
    assert r["total"] == 3660 and r["total_stamp"] == "1:01:00"
    assert r["talk_share"] == {"A": Fraction(5, 122), "B": Fraction(117, 122)}
    assert list(r["talk_share"]) == ["A", "B"]
    assert r["dominant"] == "B" and r["status"] == p.STATUS_NOTE


def test_share_sums_to_one_and_sorted_keys():
    r = P([S(speaker="zed", seconds=1), S(speaker="amy", seconds=2), S(speaker="Bob", seconds=4)])
    assert list(r["talk_share"]) == ["Bob", "amy", "zed"]
    assert sum(r["talk_share"].values()) == 1
    assert r["talk_share"]["Bob"] == Fraction(4, 7)


def test_dominant_tie_alphabetical():
    assert P([S(speaker="B", seconds=5), S(speaker="A", seconds=5)])["dominant"] == "A"
    assert P([S(speaker="B", seconds=6), S(speaker="A", seconds=5)])["dominant"] == "B"


def test_single_segment_and_title_kept():
    r = P([S(" Hi ", "X", 1)])
    assert r["chapters"][0]["title"] == " Hi " and r["total"] == 1 and r["talk_share"] == {"X": 1}


@pytest.mark.parametrize("bad", [
    [], "ab", None, [5], [S()] * 501, [{"speaker": "A", "seconds": 1}], [S(title="")], [S(title="  ")], [S(title=3)],
    [S(speaker="")], [S(speaker=" ")], [S(speaker=None)], [S(seconds=0)], [S(seconds=86401)], [S(seconds=1.5)],
    [S(seconds=True)], [S(seconds="5")], [S(seconds=-5)], [{"title": "t", "speaker": "A"}], [S(seconds=2 * 10 ** 9)],
])
def test_rejects(bad):
    with pytest.raises(ValueError):
        P(bad)


def test_limits():
    assert P([S(seconds=1)] * 500)["total"] == 500
    assert P([S(seconds=86400)] * 4 + [S(seconds=14399)])["total_stamp"] == "99:59:59"
    with pytest.raises(ValueError, match="total length above 99:59:59"):
        P([S(seconds=86400)] * 4 + [S(seconds=14400)])
    assert P([S(seconds=1)])["total"] == 1
    assert P([S(seconds=86400)])["total_stamp"] == "24:00:00"
    with pytest.raises(ValueError, match="seconds: must be within"):
        P([S(seconds=86401)])
    with pytest.raises(ValueError, match="seconds: must be within"):
        P([S(seconds=0)])


def test_messages():
    with pytest.raises(ValueError, match="segments: 1 to 500 required"):
        P([])
    with pytest.raises(ValueError, match="segment: title required"):
        P([S(title=" ")])
    with pytest.raises(ValueError, match="segment: title required"):
        P([5])
    with pytest.raises(ValueError, match="segment: speaker required"):
        P([S(speaker="")])
    with pytest.raises(ValueError, match="seconds: whole number required"):
        P([S(seconds=1.5)])


def test_random_against_independent_cumulative_oracle():
    import random
    rnd = random.Random(11)
    for _ in range(100):
        segs = [S("c%d" % i, rnd.choice("PQR"), rnd.randint(1, 5000)) for i in range(rnd.randint(1, 12))]
        r = P(segs)
        run = 0
        for c, s in zip(r["chapters"], segs):
            h, rem = divmod(run, 3600)
            assert c["stamp"] == "%d:%02d:%02d" % (h, rem // 60, rem % 60) and c["start"] == run
            run += s["seconds"]
        assert r["total"] == run
        for k, share in r["talk_share"].items():
            assert share * run == sum(s["seconds"] for s in segs if s["speaker"] == k)
