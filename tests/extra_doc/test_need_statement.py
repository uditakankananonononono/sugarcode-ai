import re
import itertools
import pytest
from sugarcode.extra_doc import need_statement as ns

B = ns.build
NC = ("clarity of the words", "assertiveness or tone", "politeness", "language meaning",
      "whether the need is met")
L = ("situation", "need", "request")


class St(str):
    pass


class Tu(tuple):
    pass


def refuse(msg, parts):
    with pytest.raises(ValueError) as e:
        B(parts)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def ok3(i, v):
    p = ["a", "b", "c"]
    p[i] = v
    return tuple(p)


def test_constants():
    assert ns.MAX_PART == 200 and ns.LABELS == L and ns.NOT_CLAIMED == NC


def test_literals():
    assert B(("s", "n", "r")) == {"lengths": (1, 1, 1), "sentence": "s | n | r",
                                  "need_statement_validated": False, "not_claimed": NC}
    assert B(("a b", "9", "x.y"))["sentence"] == "a b | 9 | x.y"
    assert B(("!a", "a!", "?7?"))["lengths"] == (2, 2, 3)
    assert B(("\u00e9a", "b\u00e9", "\u0430c"))["lengths"] == (2, 2, 2)
    assert B(("a" * 200, "b", "c"))["lengths"] == (200, 1, 1)


def test_oracle_exhaustive():
    alpha = ["a", " ", "\n", "!", "\u00e9", "9"]
    cand = ["".join(t) for n in (1, 2) for t in itertools.product(alpha, repeat=n)]

    def okp(p):
        return (p[0] not in " \t\n" and p[-1] not in " \t\n"
                and any(c in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" for c in p))
    for p in cand:
        for i in range(3):
            t = ok3(i, p)
            if okp(p):
                assert B(t)["sentence"] == " | ".join(t)
            else:
                with pytest.raises(ValueError):
                    B(t)


@pytest.mark.parametrize("i", range(3))
def test_slot_messages(i):
    lab = L[i]
    for bad in ("", "a" * 201, None, 5, b"a", St("a")):
        refuse(f"{lab}: str of 1 to 200 characters required", ok3(i, bad))
    for bad in (" a", "a ", "\ta", "a\t", "\na", "a\n", " ", "a\n"):
        refuse(f"{lab}: no leading or trailing space, tab or newline", ok3(i, bad))
    for bad in ("!", "\u00e9", "\uff41", "\u0430", "!?", "\u00e9\u00e9", "_"):
        refuse(f"{lab}: at least one ASCII letter or digit required", ok3(i, bad))
    for good in ("0", "Z", "!a", "\u00e9a\u00e9", "a b"):
        assert B(ok3(i, good))["sentence"] == " | ".join(ok3(i, good))


@pytest.mark.parametrize("bad", [(), ("a", "b"), ("a",) * 4, ["a", "b", "c"], None, "abc", Tu(("a", "b", "c"))])
def test_shape(bad):
    refuse("parts: tuple of 3 str required", bad)


def test_order():
    refuse("situation: str of 1 to 200 characters required", ("", " ", "!"))
    refuse("need: str of 1 to 200 characters required", (" ", None, "!"))
    refuse("situation: no leading or trailing space, tab or newline", (" !", "!", "!"))
    refuse("need: no leading or trailing space, tab or newline", ("a", " !", "!"))
    refuse("situation: at least one ASCII letter or digit required", ("!", "!", "!"))
    refuse("need: at least one ASCII letter or digit required", ("a", "!", "!"))
    refuse("request: at least one ASCII letter or digit required", ("a", "a", "!"))
    refuse("request: str of 1 to 200 characters required", (" !", "!", ""))


def test_boundary_positions():
    for i in range(3):
        for g in ("a!!", "!a!", "!!a", "9" + "!" * 199, "!" * 199 + "z", "!" * 100 + "q" + "!" * 99):
            assert B(ok3(i, g))["lengths"][i] == len(g)
        refuse(f"{L[i]}: str of 1 to 200 characters required", ok3(i, "a" * 201))
        refuse(f"{L[i]}: at least one ASCII letter or digit required", ok3(i, "!" * 200))
        refuse(f"{L[i]}: no leading or trailing space, tab or newline", ok3(i, "a" * 199 + " "))
        refuse(f"{L[i]}: no leading or trailing space, tab or newline", ok3(i, " " + "a" * 199))


@pytest.mark.parametrize("i", [0, 2])           # first and last slots
def test_blank_edge_each_char(i):
    lab = L[i]
    assert B(("ax", "bx", "cx"))["sentence"] == "ax | bx | cx"          # auditor witness: trailing 'x' is fine
    assert B(ok3(i, "x"))["sentence"] == " | ".join(ok3(i, "x"))        # 'x' at both ends at once
    assert B(ok3(i, "xa"))["sentence"] == " | ".join(ok3(i, "xa"))      # leading non-blank next to the blank set
    assert B(ok3(i, "ax"))["sentence"] == " | ".join(ok3(i, "ax"))      # trailing non-blank next to the blank set
    for c in (" ", "\t", "\n"):
        refuse(f"{lab}: no leading or trailing space, tab or newline", ok3(i, c + "x"))
        refuse(f"{lab}: no leading or trailing space, tab or newline", ok3(i, "x" + c))
        refuse(f"{lab}: no leading or trailing space, tab or newline", ok3(i, c + "x" + c))


@pytest.mark.parametrize("i", [0, 2])           # first and last slots
def test_blank_edge_all_printable_ascii(i):
    for k in range(0x21, 0x7F):                 # every printable non-blank ASCII char: letters, digits, punctuation
        c = chr(k)
        assert B(ok3(i, c + "a"))["sentence"] == " | ".join(ok3(i, c + "a"))
        assert B(ok3(i, "a" + c))["sentence"] == " | ".join(ok3(i, "a" + c))
    for c in ("\r", "\x0b", "\x0c", "\x00", "\u00e9", "\uff41", "\u0430"):
        assert B(ok3(i, c + "a"))["sentence"] == " | ".join(ok3(i, c + "a"))
        assert B(ok3(i, "a" + c))["sentence"] == " | ".join(ok3(i, "a" + c))
