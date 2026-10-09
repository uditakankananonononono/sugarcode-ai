import ast

import pytest

from sugarcode.self_improve.safety import SafetyViolation, validate_source


@pytest.mark.parametrize("source", ["return 1", "break", "continue", "yield 1",
                                    "from __future__ import braces"])
def test_ast_parse_success_is_not_compile_success(source):
    ast.parse(source)
    with pytest.raises(SafetyViolation) as caught:
        validate_source(source, allowed_imports=frozenset({"__future__"}))
    assert isinstance(caught.value.__cause__, SyntaxError)
    assert "does not compile" in str(caught.value)


def test_compile_unrelated_errors_are_not_mislabeled(monkeypatch):
    from sugarcode.self_improve import safety

    original = compile

    def fail_only_ast(source, *args, **kwargs):
        if isinstance(source, ast.AST):
            raise MemoryError("compiler exhausted")  # noqa: TRY004 - injected compiler failure
        return original(source, *args, **kwargs)

    monkeypatch.setattr(safety, "compile", fail_only_ast, raising=False)
    with pytest.raises(MemoryError, match="compiler exhausted"):
        validate_source("x = 1")


def test_valid_source_and_parser_failures_keep_existing_contract():
    assert isinstance(validate_source("x = 1"), ast.Module)
    with pytest.raises(SafetyViolation, match="does not parse"):
        validate_source("if")
