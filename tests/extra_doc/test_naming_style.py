import re
import pytest
from sugarcode.extra_doc import naming_style as ns

C = ns.check
NC = ("quality of any name", "project style guide", "meaning of the identifiers",
      "language rules", "runtime behaviour")
EXP = "one of lowercase, snake_case, UPPER_SNAKE, camelCase, PascalCase, other required"
STY = ("lowercase", "snake_case", "UPPER_SNAKE", "camelCase", "PascalCase", "other")


class Li(list):
    pass


class St(str):
    pass


def refuse(msg, *a):
    with pytest.raises(ValueError) as e:
        C(*a)
    assert re.fullmatch(re.escape(msg), str(e.value)), str(e.value)


def style(n):
    return C([n], "other")["styles"][0]


def oracle(n):                              # independent: character-class walk, no regex
    low, up, dig = "abcdefghijklmnopqrstuvwxyz", "ABCDEFGHIJKLMNOPQRSTUVWXYZ", "0123456789"
    if any(ch not in low + up + dig + "_" for ch in n):
        return "other"
    if "_" in n:
        parts = n.split("_")
        if any(p == "" for p in parts):
            return "other"
        if parts[0][0] in dig:
            return "other"
        if all(ch in low + dig for p in parts for ch in p):
            return "snake_case"
        if all(ch in up + dig for p in parts for ch in p):
            return "UPPER_SNAKE"
        return "other"
    if n[0] in dig:
        return "other"
    if all(ch in low + dig for ch in n):
        return "lowercase"
    if all(ch in up + dig for ch in n):
        return "UPPER_SNAKE"
    if n[0] in low:
        return "camelCase"
    return "PascalCase" if any(ch in low for ch in n) else "other"


def test_constants():
    assert (ns.MAX_NAMES, ns.MAX_LEN) == (100, 64) and ns.STYLES == STY and ns.NOT_CLAIMED == NC


@pytest.mark.parametrize("name,want", [
    ("name", "lowercase"), ("name2", "lowercase"), ("a", "lowercase"), ("user_id", "snake_case"),
    ("a_b", "snake_case"), ("a1_2b", "snake_case"), ("MAX_SIZE", "UPPER_SNAKE"), ("MAX", "UPPER_SNAKE"),
    ("A", "UPPER_SNAKE"), ("A1", "UPPER_SNAKE"), ("A_1", "UPPER_SNAKE"), ("userId", "camelCase"),
    ("aB", "camelCase"), ("httpServer2", "camelCase"), ("getHTTPServer", "camelCase"), ("UserId", "PascalCase"),
    ("Ab", "PascalCase"), ("HTTPServer", "PascalCase"), ("AbC", "PascalCase"),
    ("_x", "other"), ("x_", "other"), ("a__b", "other"), ("1a", "other"), ("1", "other"), ("_", "other"),
    ("a_B", "other"), ("A_b", "other"), ("Ab_c", "other"), ("a-b", "other"), ("a b", "other"),
    ("caf\u00e9", "other"), ("Caf\u00e9", "other"), ("\uff41bc", "other"), ("a\n", "other"), ("a\u0661", "other"),
    ("x\u00df", "other")])
def test_styles(name, want):
    assert style(name) == want and oracle(name) == want


def test_exhaustive_against_oracle():
    import itertools
    alpha = "aA1_\u00e9"
    for n in range(1, 5):
        for t in itertools.product(alpha, repeat=n):
            s = "".join(t)
            assert style(s) == oracle(s), s


def test_report_shape_and_counts():
    names = ["a", "b_c", "D_E", "fG", "Hi", "_", "x"]
    r = C(names, "lowercase")
    assert r["styles"] == ["lowercase", "snake_case", "UPPER_SNAKE", "camelCase", "PascalCase", "other", "lowercase"]
    assert r["mismatches"] == [1, 2, 3, 4, 5]
    assert r["style_counts"] == [2, 1, 1, 1, 1, 1]
    assert r == {"styles": r["styles"], "mismatches": [1, 2, 3, 4, 5], "style_counts": [2, 1, 1, 1, 1, 1],
                 "naming_validated": False, "not_claimed": NC}
    assert C(["a_b", "c_d"], "snake_case")["mismatches"] == []
    assert C(["a_b", "cD"], "snake_case")["mismatches"] == [1]
    assert C(["x"], "other")["mismatches"] == [0]
    assert names == ["a", "b_c", "D_E", "fG", "Hi", "_", "x"]


def test_caps_accepted():
    assert style("a" * 64) == "lowercase"
    assert len(C(["a"] * 100, "lowercase")["styles"]) == 100


@pytest.mark.parametrize("bad", [None, 5, b"a", ["a"], "", "a" * 65, St("a")])
def test_name_refusals(bad):
    refuse("names[0]: string of 1 to 64 characters required", [bad], "other")
    refuse("names[1]: string of 1 to 64 characters required", ["a", bad], "other")
    refuse("names[2]: string of 1 to 64 characters required", ["a", "b", bad], "other")


@pytest.mark.parametrize("bad", [(), None, "ab", Li(["a"]), [], ["a"] * 101])
def test_names_shape(bad):
    refuse("names: list of 1 to 100 required", bad, "other")


@pytest.mark.parametrize("bad", [None, 1, "", "Lowercase", "snake", "CAMELCASE", "camelcase", "lowercase ", "other\n",
                                 "l\u043ewercase", St("other"), b"other"])
def test_expected_refusals(bad):
    refuse(f"expected: {EXP}", ["a"], bad)


def test_check_order():
    refuse("names: list of 1 to 100 required", None, None)
    refuse("names[0]: string of 1 to 64 characters required", [None], None)
    refuse(f"expected: {EXP}", ["a"], None)
