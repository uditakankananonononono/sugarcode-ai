import re
import pytest
from sugarcode.extra_doc import adr_status as ar

C = ar.check
NC = ("quality of any decision", "content of the records", "completeness of the log",
      "who approved what", "runtime behaviour")
ST = "one of proposed, accepted, rejected, deprecated, superseded required"
SUP = "None or the id of an earlier record in the list required"


class I(int):
    pass


class Li(list):
    pass


class Tu(tuple):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        C(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def test_constants():
    assert (ar.MAX_RECORDS, ar.MAX_ID) == (64, 9999)
    assert ar.STATUSES == ("proposed", "accepted", "rejected", "deprecated", "superseded") and ar.NOT_CLAIMED == NC


def test_hand_literals():
    ok = [(1, "superseded", None), (2, "accepted", 1), (3, "rejected", None), (4, "proposed", None)]
    assert C(ok)["issues"] == [] and C(ok)["links_consistent"] is True
    bad = [(1, "accepted", None), (2, "proposed", 1)]
    assert C(bad)["issues"] == [(1, "target_not_marked_superseded"), (2, "superseder_status_invalid")]
    assert C([(5, "superseded", None)])["issues"] == [(5, "superseded_without_successor")]
    twice = [(1, "superseded", None), (2, "accepted", 1), (3, "accepted", 1)]
    assert C(twice)["issues"] == [(1, "target_superseded_twice")]
    assert C([(1, "superseded", None), (2, "superseded", 1), (3, "accepted", 2)])["issues"] == []
    assert C([(9999, "accepted", None)])["issues"] == [] and C([(1, "deprecated", None)])["issues"] == []
    assert C([(3, "accepted", None), (1, "superseded", None), (2, "accepted", 1)])["issues"] == []   # list order free


def test_shape_and_untouched():
    rec = [(1, "accepted", None)]
    r = C(rec)
    assert rec == [(1, "accepted", None)]
    assert r == {"issues": [], "links_consistent": True, "adr_validated": False, "not_claimed": NC}
    r = C([(1, "accepted", None), (2, "accepted", 1)])
    assert r["links_consistent"] is False


def test_independent_oracle():
    import itertools
    sts = list(ar.STATUSES)
    for s1, s2, s3 in itertools.product(sts, repeat=3):
        for sup2, sup3 in itertools.product([None, 1], [None, 1, 2]):
            recs = [(1, s1, None), (2, s2, sup2), (3, s3, sup3)]
            want = set()
            for rid, st, sup in recs:
                if sup is not None:
                    if st not in ("accepted", "superseded"):
                        want.add((rid, "superseder_status_invalid"))
                    if dict((a, b) for a, b, _ in recs)[sup] != "superseded":
                        want.add((sup, "target_not_marked_superseded"))
            for rid, st, _ in recs:
                if st == "superseded" and not any(r[2] == rid for r in recs):
                    want.add((rid, "superseded_without_successor"))
            for rid in (1, 2):
                if sum(1 for r in recs if r[2] == rid) > 1:
                    want.add((rid, "target_superseded_twice"))
            got = C(recs)
            assert got["issues"] == sorted(want)
            assert got["links_consistent"] is (not want)


def test_caps_accepted():
    recs = [(i, "accepted", None) for i in range(1, 65)]
    assert C(recs)["links_consistent"] is True
    chain = [(1, "superseded", None)] + [(i, "superseded", i - 1) for i in range(2, 64)] + [(64, "accepted", 63)]
    assert C(chain)["issues"] == []


@pytest.mark.parametrize("bad", [True, False, 1.0, "1", None, I(1), 0, -1, 10000])
def test_id_refusals(bad):
    refuse("records[0] id: whole number 1 to 9999 required", [(bad, "accepted", None)])
    refuse("records[1] id: whole number 1 to 9999 required", [(1, "accepted", None), (bad, "accepted", None)])


@pytest.mark.parametrize("bad", [None, 1, "", "Accepted", "ACCEPTED", "accepted ", "accept", "accepted\n",
                                 "\u0430ccepted", St("accepted"), b"accepted"])
def test_status_refusals(bad):
    refuse(f"records[0] status: {ST}", [(1, bad, None)])
    refuse(f"records[1] status: {ST}", [(1, "accepted", None), (2, bad, None)])


@pytest.mark.parametrize("bad", [True, 1.0, "1", I(1), 0, 2, 3, 99, -1, [1]])
def test_supersedes_refusals(bad):
    refuse(f"records[1] supersedes: {SUP}", [(1, "accepted", None), (2, "accepted", bad)])
    refuse(f"records[0] supersedes: {SUP}", [(2, "accepted", bad), (1, "accepted", None)])


def test_supersedes_rules():
    refuse(f"records[0] supersedes: {SUP}", [(2, "accepted", 2)])             # itself
    refuse(f"records[0] supersedes: {SUP}", [(1, "accepted", 2), (2, "accepted", None)])   # later id
    assert C([(1, "superseded", None), (2, "accepted", 1)])["links_consistent"] is True


@pytest.mark.parametrize("bad", [[], (1, "accepted"), (1, "accepted", None, 0), Tu((1, "accepted", None)),
                                 [1, "accepted", None], None, "abc"])
def test_row_shape(bad):
    refuse("records[0]: (id, status, supersedes) tuple required", [bad])
    refuse("records[1]: (id, status, supersedes) tuple required", [(1, "accepted", None), bad])


@pytest.mark.parametrize("bad", [(), None, "ab", Li([(1, "accepted", None)]), [],
                                 [(i, "accepted", None) for i in range(1, 66)]])
def test_records_shape(bad):
    refuse("records: list of 1 to 64 required", bad)


def test_distinct_and_order():
    refuse("records: ids must be distinct", [(1, "accepted", None), (1, "proposed", None)])
    refuse("records: list of 1 to 64 required", None)
    refuse("records: ids must be distinct", [(1, "accepted", 5), (1, "accepted", None)])
    refuse("records[0] id: whole number 1 to 9999 required", [(0, "bad", 9)])
