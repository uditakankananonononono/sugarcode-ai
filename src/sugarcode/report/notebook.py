"""Executable Jupyter notebook generation (nbformat 4.x, dependency-free).

Notebooks are emitted as real nbformat JSON: every code cell is runnable
as-is in an environment with sugarcode-ai installed. validate_notebook is
a structural checker so generated and hand-supplied notebooks are verified
before being handed to a user.
"""
from __future__ import annotations

import json

_VALID_CELL_TYPES = {"code", "markdown", "raw"}


def _lines(source: str) -> list[str]:
    if not isinstance(source, str):
        raise TypeError("cell source must be a string")
    return source.splitlines(keepends=True)


def new_notebook(cells: list[dict], *, language_version: str = "3.10",
                 kernel_display: str = "Python 3") -> dict:
    """Build an nbformat 4.5 notebook dict from
    [{"cell_type": "code"|"markdown", "source": str}]."""
    if not cells:
        raise ValueError("cells must be non-empty")
    out_cells = []
    for i, c in enumerate(cells):
        ct = c.get("cell_type")
        if ct not in _VALID_CELL_TYPES:
            raise ValueError(f"cell {i} has invalid cell_type {ct!r}")
        cell = {"cell_type": ct, "metadata": {}, "source": _lines(c["source"])}
        if ct == "code":
            cell["execution_count"] = None
            cell["outputs"] = []
        out_cells.append(cell)
    return {
        "nbformat": 4,
        "nbformat_minor": 5,
        "metadata": {
            "kernelspec": {"display_name": kernel_display,
                           "language": "python", "name": "python3"},
            "language_info": {"name": "python", "version": language_version},
        },
        "cells": out_cells,
    }


def validate_notebook(nb: dict) -> list[str]:
    """Structural validation. Returns a list of problems ([] = valid)."""
    problems: list[str] = []
    if not isinstance(nb, dict):
        return ["notebook is not a JSON object"]
    if nb.get("nbformat") != 4:
        problems.append("nbformat must be 4")
    if not isinstance(nb.get("nbformat_minor"), int):
        problems.append("nbformat_minor missing or not an int")
    cells = nb.get("cells")
    if not isinstance(cells, list) or not cells:
        problems.append("cells must be a non-empty list")
        return problems
    for i, c in enumerate(cells):
        if not isinstance(c, dict):
            problems.append(f"cell {i} is not an object")
            continue
        ct = c.get("cell_type")
        if ct not in _VALID_CELL_TYPES:
            problems.append(f"cell {i}: invalid cell_type {ct!r}")
        src = c.get("source")
        if not (isinstance(src, str) or
                (isinstance(src, list) and all(isinstance(x, str) for x in src))):
            problems.append(f"cell {i}: source must be a string or list of strings")
        if ct == "code":
            if "outputs" not in c or not isinstance(c["outputs"], list):
                problems.append(f"cell {i}: code cell needs an outputs list")
            if "execution_count" not in c:
                problems.append(f"cell {i}: code cell needs execution_count")
    return problems


def notebook_json(nb: dict) -> str:
    """Serialize a notebook dict to .ipynb text."""
    problems = validate_notebook(nb)
    if problems:
        raise ValueError(f"invalid notebook: {problems}")
    return json.dumps(nb, indent=1) + "\n"
