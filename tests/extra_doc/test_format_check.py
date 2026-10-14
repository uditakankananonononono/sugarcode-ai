import re
import pytest
from sugarcode.extra_doc import format_check as fc

C = fc.check
NC = ("a style guide", "language syntax", "display width of wide characters",
      "readability", "runtime behaviour")
MSG = "string of 0 to 300 characters without line breaks required"


class I(int):
    pass


class Li(list):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        C(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def v(lines, w=20, ind=4):
    return C(lines, w, ind)["violations"]


def test_constants():
    assert (fc.MAX_LINES, fc.MAX_LINE) == (500, 300)
    assert fc.KINDS == ("too_long", "trailing_whitespace", "tab_indent", "bad_indent") and fc.NOT_CLAIMED == NC


def test_hand_literals():
    assert v(["x" * 20]) == [] and v(["x" * 21]) == [(0, "too_long")]
    assert v(["x "]) == [(0, "trailing_whitespace")] and v(["x\t"]) == [(0, "trailing_whitespace")]
    assert v([" ", "\t", "", "    "]) == []                       # whitespace-only lines are not flagged
    assert v(["\tx"]) == [(0, "tab_indent")]
    assert v([" \tx"]) == [(0, "tab_indent")] and v(["\t x"]) == [(0, "tab_indent")]
    assert v(["  x"]) == [(0, "bad_indent")] and v(["    x"]) == []
    assert v(["        x"]) == [] and v(["     x"]) == [(0, "bad_indent")]
    assert v(["  x"], ind=2) == [] and v(["  x"], ind=1) == [] and v([" x"], ind=2) == [(0, "bad_indent")]
    assert v(["  " + "y" * 19 + "  "]) == [(0, "too_long"), (0, "trailing_whitespace"), (0, "bad_indent")]
    assert v(["\t" + "y" * 19 + " "]) == [(0, "too_long"), (0, "trailing_whitespace"), (0, "tab_indent")]
    assert v(["ok", "  bad", "ok"]) == [(1, "bad_indent")]


def test_unicode_pins():
    assert v(["\u00a0x"]) == []                                  # NBSP is text, not indentation
    assert v(["x\u00a0"]) == []                                  # trailing NBSP is not an ASCII space
    assert v(["\u3000x"]) == []
    assert v(["\u00e9" * 20]) == [] and v(["\u00e9" * 21]) == [(0, "too_long")]   # characters, not bytes
    assert v(["\u4e2d" * 20]) == []                              # wide characters count as one
    assert v(["\u200b  x"]) == []                                # leading zero-width space is text, so lead is empty


def test_shape_and_untouched():
    ln = ["x "]
    r = C(ln, 20, 4)
    assert ln == ["x "]
    assert r == {"violations": [(0, "trailing_whitespace")], "clean": False, "formatting_validated": False,
                 "not_claimed": NC}
    assert C(["x"], 20, 4)["clean"] is True


def test_independent_oracle():
    import random
    rnd = random.Random(708)
    atoms = [" ", " ", "\t", "x", "y", "\u00a0", "\u00e9"]
    for _ in range(400):
        s = "".join(rnd.choice(atoms) for _ in range(rnd.randint(0, 12)))
        w, ind = rnd.randint(20, 22) if rnd.random() < .1 else 20, rnd.randint(1, 4)
        k = len(s)
        i = 0
        while i < k and s[i] in " \t":
            i += 1
        j = k
        while j > i and s[j - 1] in " \t":
            j -= 1
        want = []
        if k > w:
            want.append("too_long")
        if i < k and j < k:
            want.append("trailing_whitespace")
        if i < k and "\t" in s[:i]:
            want.append("tab_indent")
        elif i < k and s[:i].count(" ") % ind:
            want.append("bad_indent")
        assert v([s], w, ind) == [(0, kd) for kd in want], (s, w, ind)


def test_caps_accepted():
    assert len(v(["  x"] * 500)) == 500
    assert v(["x" * 300], w=200)[0] == (0, "too_long")
    assert v(["x" * 200], w=200) == []
    assert v(["x" * 30], w=200, ind=8) == []


@pytest.mark.parametrize("bad", [None, 5, b"x", ["x"], "a\nb", "a\rb", "\n", "x" * 301, St("x")])
def test_line_refusals(bad):
    refuse(f"lines[0]: {MSG}", [bad], 20, 4)
    refuse(f"lines[1]: {MSG}", ["x", bad], 20, 4)
    refuse(f"lines[2]: {MSG}", ["x", "y", bad], 20, 4)


@pytest.mark.parametrize("bad", [(), None, "ab", Li(["x"]), [], ["x"] * 501])
def test_lines_shape(bad):
    refuse("lines: list of 1 to 500 required", bad, 20, 4)


@pytest.mark.parametrize("bad", [True, 1.0, "20", None, I(20), 19, 201, 0, -1])
def test_width_refusals(bad):
    refuse("max_width: whole number 20 to 200 required", ["x"], bad, 4)


@pytest.mark.parametrize("bad", [True, 1.0, "4", None, I(4), 0, 9, -1])
def test_indent_refusals(bad):
    refuse("indent: whole number 1 to 8 required", ["x"], 20, bad)


def test_check_order():
    refuse("lines: list of 1 to 500 required", None, None, None)
    refuse(f"lines[0]: {MSG}", [None], None, None)
    refuse("max_width: whole number 20 to 200 required", ["x"], None, None)
