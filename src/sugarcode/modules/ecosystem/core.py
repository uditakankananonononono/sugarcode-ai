from __future__ import annotations
from omega.registry import REGISTRY, SUBNETWORKS


def sdk_snippet(module: str, language: str = "python") -> str:
    """Working code snippet for programmatic access to a module."""
    if module not in REGISTRY:
        raise KeyError(f"unknown module {module!r}")
    if language == "python":
        return (
            f"# SugarCode AI SDK - {REGISTRY[module].name}\n"
            f"from sugarcode.modules import {module}\n\n"
            f"# public callables:\n"
            f"#   " + "\n#   ".join(_public_callables(module)) + "\n"
        )
    if language == "curl":
        return (f"curl -s https://api.sugarcode.local/modules/{module} \\\n"
                f"  -H 'Authorization: Bearer $SUGARCODE_KEY'\n")
    raise ValueError(f"unsupported language {language!r}")


def _public_callables(module: str) -> list[str]:
    import importlib
    try:
        mod = importlib.import_module(f"sugarcode.modules.{module}")
        return [n for n in sorted(dir(mod)) if not n.startswith("_")] or ["(pending implementation)"]
    except ModuleNotFoundError:
        return ["(pending implementation)"]


def plugin_manifest(name: str, provides: list[str]) -> dict:
    """Plugin architecture contract: manifest for a third-party extension."""
    return {
        "api_version": "omega/v7",
        "kind": "SugarCodePlugin",
        "metadata": {"name": name},
        "provides": provides,
        "requirements": {
            "entry_point": "plugin.register(registry) -> None",
            "module_spec": "must declare slug, name, subnetwork, summary",
            "tests": "pytest suite with >=1 named test per public callable",
            "standards": ["FAIR data outputs", "SBML where applicable",
                          "FASTA/PDB/JSON export formats"],
        },
        "lifecycle": ["discover", "validate", "register", "health-check", "serve"],
    }


def api_reference() -> dict:
    """Machine-readable reference of the platform API surface."""
    return {
        "rest": [
            {"method": "GET", "path": "/modules", "desc": "list modules"},
            {"method": "GET", "path": "/modules/{slug}", "desc": "module detail"},
            {"method": "GET", "path": "/subnetworks", "desc": "nine sub-networks"},
            {"method": "GET", "path": "/health", "desc": "global compute flux"},
            {"method": "GET", "path": "/health/{slug}", "desc": "module health"},
            {"method": "GET", "path": "/search?q=", "desc": "unified biological search"},
        ],
        "python_package": {
            "framework": "omega (registry, health, search, api)",
            "modules_root": "sugarcode.modules",
            "bio_toolkit": "sugarcode.bio (sequence, fasta, codon, pwm)",
        },
        "modules": len(REGISTRY),
        "subnetworks": list(SUBNETWORKS),
    }
