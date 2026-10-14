import re
from fractions import Fraction
import pytest
from sugarcode.extra_doc import comment_ratio as cr

C = cr.count
NC = ("usefulness of any comment", "correctness of any comment", "language syntax",
      "documentation quality", "runtime behaviour")
MSG = "string of 0 to 200 characters without line breaks required"


class Li(list):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        C(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def test_constants():
    assert (cr.MAX_LINES, cr.MAX_LINE) == (500, 200) and cr.NOT_CLAIMED == NC


def test_hand_literals():
    r = C(["# one", "x = 1", "", "   # two", "y = 2  # trailing", "\t", "z = 3"])
    assert (r["blank"], r["comment"], r["code"]) == (2, 2, 3)
    assert r["comment_share"] == (2, 5)
    r = C(["# a", "# b", "c"])
    assert r["comment_share"] == (2, 3)
    r = C(["# a", "x", "# b", "y"])
    assert r["comment_share"] == (1, 2)                     # 2/4 reduced
    assert C(["", "   "])["comment_share"] is None
    assert C(["x"])["comment_share"] == (0, 1) and C(["#"])["comment_share"] == (1, 1)
    assert C([""])["blank"] == 1 and C(["#"])["comment"] == 1


def test_unicode_pins():
    assert C(["\u00a0"])["blank"] == 1                      # no-break space is whitespace for str.strip
    assert C(["\u00a0# note"])["comment"] == 1              # lstrip removes it, then "#"
    assert C(["\u3000# note"])["comment"] == 1              # ideographic space
    assert C(["\u2003"])["blank"] == 1
    assert C(["\uff03 note"])["code"] == 1                  # fullwidth number sign is not "#"
    assert C(["\u00e9 = 1"])["code"] == 1
    assert C(["\u200b# x"])["code"] == 1                    # zero-width space is not whitespace
    assert C(["\x0b\x0c# x"])["comment"] == 1
    assert C(["#\u00e9"])["comment"] == 1


def test_shape_and_untouched():
    ln = ["#", "x"]
    r = C(ln)
    assert ln == ["#", "x"]
    assert r == {"blank": 0, "comment": 1, "code": 1, "comment_share": (1, 2),
                 "comments_validated": False, "not_claimed": NC}


def test_independent_oracle():
    import random
    rnd = random.Random(706)
    atoms = ["", " ", "\t", "#", "x", "\u00a0", "\u00e9", "\uff03", "\u200b"]
    for _ in range(300):
        lines = ["".join(rnd.choice(atoms) for _ in range(rnd.randint(0, 4))) for _ in range(rnd.randint(1, 8))]
        b = c = k = 0
        for s in lines:
            i = 0
            while i < len(s) and s[i].isspace():
                i += 1
            if i == len(s):
                b += 1
            elif s[i] == "#":
                c += 1
            else:
                k += 1
        r = C(lines)
        assert (r["blank"], r["comment"], r["code"]) == (b, c, k)
        if c + k:
            assert Fraction(*r["comment_share"]) == Fraction(c, c + k)
        else:
            assert r["comment_share"] is None


def test_caps_accepted():
    assert C(["#"] * 500)["comment"] == 500
    assert C(["x" * 200])["code"] == 1


@pytest.mark.parametrize("bad", [None, 5, b"x", ["x"], "a\nb", "a\rb", "\n", "x" * 201, St("x")])
def test_line_refusals(bad):
    refuse(f"lines[0]: {MSG}", [bad])
    refuse(f"lines[1]: {MSG}", ["x", bad])
    refuse(f"lines[2]: {MSG}", ["x", "#", bad])


@pytest.mark.parametrize("bad", [(), None, "ab", Li(["x"]), [], ["x"] * 501])
def test_lines_shape(bad):
    refuse("lines: list of 1 to 500 required", bad)


def test_check_order():
    refuse("lines: list of 1 to 500 required", None)
    refuse(f"lines[0]: {MSG}", [None, "a\nb"])
