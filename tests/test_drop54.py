"""Drop 54: repo-wide stub/error audit, locked continuously + real SBML
export (the one literal stub the audit found)."""
import ast
import re
import subprocess
import xml.dom.minidom as md
from pathlib import Path

import pytest

SRC = Path("src")


def _py_files():
    return [p for p in SRC.rglob("*.py") if "__pycache__" not in str(p)]


def test_zero_compile_errors():
    r = subprocess.run(["python3", "-m", "compileall", "-q", "src", "scripts"],
                       capture_output=True)
    assert r.returncode == 0, r.stderr.decode()[:500]


def test_zero_stub_markers():
    offenders = []
    for p in _py_files():
        t = p.read_text()
        if re.search(r"NotImplementedError|TODO|FIXME|HACK", t):
            offenders.append(str(p))
        if re.search(r"_stub\b", t):
            offenders.append(f"{p} (_stub name)")
    assert offenders == []


def test_zero_empty_function_bodies():
    hits = []
    for p in _py_files():
        for node in ast.walk(ast.parse(p.read_text())):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                b = node.body
                if len(b) == 1 and isinstance(b[0], ast.Pass):
                    hits.append(f"{p}:{node.name}")
                elif len(b) == 1 and isinstance(b[0], ast.Expr) and \
                        isinstance(b[0].value, ast.Constant) and b[0].value.value is Ellipsis:
                    hits.append(f"{p}:{node.name}")
    assert hits == []


def test_sbml_export_is_a_real_model():
    from sugarcode.modules.codon_opt import optimize
    r = optimize("MKTAYIAKQRQISFVKSHFSRQ", host="ecoli_k12")
    doc = md.parseString(r["sbml_export"])  # raises unless well-formed
    sbml = doc.getElementsByTagName("sbml")[0]
    assert sbml.getAttribute("level") == "3" and sbml.getAttribute("version") == "2"
    assert sbml.getAttribute("xmlns") == "http://www.sbml.org/sbml/level3/version2/core"
    assert len(doc.getElementsByTagName("species")) == 5
    assert len(doc.getElementsByTagName("reaction")) == 4
    assert len(doc.getElementsByTagName("kineticLaw")) == 4
    params = {p.getAttribute("id"): p.getAttribute("value")
              for p in doc.getElementsByTagName("parameter")}
    assert "trna_strain_index" in params
    assert float(params["k_translate"]) == pytest.approx(
        0.1 / (1.0 + float(params["trna_strain_index"])), rel=1e-4)
    assert int(params["construct_nt"]) == len(r["optimized_dna"])
