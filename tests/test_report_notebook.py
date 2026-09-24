"""Notebook generation and structural validation."""
import pytest

from sugarcode.report import new_notebook, validate_notebook, notebook_json


def test_new_notebook_nbformat_shape():
    nb = new_notebook([
        {"cell_type": "markdown", "source": "# Title"},
        {"cell_type": "code", "source": "x = 1\nprint(x)"},
    ])
    assert nb["nbformat"] == 4 and nb["nbformat_minor"] == 5
    assert nb["metadata"]["kernelspec"]["name"] == "python3"
    md, code = nb["cells"]
    assert md["source"] == ["# Title"]
    assert code["source"] == ["x = 1\n", "print(x)"]
    assert code["outputs"] == [] and code["execution_count"] is None
    assert validate_notebook(nb) == []


def test_notebook_json_roundtrip():
    import json
    nb = new_notebook([{"cell_type": "code", "source": "pass"}])
    assert json.loads(notebook_json(nb))["nbformat"] == 4


def test_validate_catches_broken_notebooks():
    assert validate_notebook("nope") == ["notebook is not a JSON object"]
    problems = validate_notebook({"nbformat": 3, "cells": [
        {"cell_type": "alien", "source": 5},
        {"cell_type": "code", "source": "x"},
    ]})
    assert any("nbformat must be 4" in p for p in problems)
    assert any("invalid cell_type" in p for p in problems)
    assert any("source must be" in p for p in problems)
    assert any("outputs list" in p for p in problems)
    assert any("execution_count" in p for p in problems)


def test_notebook_json_refuses_invalid():
    with pytest.raises(ValueError, match="invalid notebook"):
        notebook_json({"nbformat": 4, "cells": []})


def test_new_notebook_requires_cells_and_valid_types():
    with pytest.raises(ValueError):
        new_notebook([])
    with pytest.raises(ValueError):
        new_notebook([{"cell_type": "alien", "source": "x"}])
    with pytest.raises(TypeError):
        new_notebook([{"cell_type": "code", "source": 5}])
