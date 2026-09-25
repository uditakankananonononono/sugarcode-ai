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

import hashlib
import json
import re
from collections import defaultdict, deque

STANDARDS={"sequence":["FASTA","GenBank"],"structure":["PDB","mmCIF"],"variants":["VCF","HGVS"],"models":["SBML","SED-ML"],"imaging":["DICOM","OME-TIFF"],"tabular":["CSV","JSON"]}

def validate_plugin_manifest(manifest: dict) -> dict:
    """Validate and normalize a plugin manifest into an installable contract."""
    if not isinstance(manifest,dict): raise ValueError("manifest must be a mapping")
    required={"api_version","kind","metadata","provides","requirements","lifecycle"}; missing=sorted(required-set(manifest))
    if missing: raise ValueError(f"manifest missing required fields: {', '.join(missing)}")
    if manifest["api_version"]!="omega/v7" or manifest["kind"]!="SugarCodePlugin": raise ValueError("plugin requires api_version omega/v7 and kind SugarCodePlugin")
    name=manifest.get("metadata",{}).get("name","")
    if not re.fullmatch(r"[a-z][a-z0-9_-]{2,63}",name): raise ValueError("metadata.name must be 3-64 lowercase slug characters")
    provides=manifest["provides"]
    if not isinstance(provides,list) or not provides or any(not isinstance(x,str) or not x for x in provides): raise ValueError("provides must be a non-empty string list")
    if len(provides)!=len(set(provides)): raise ValueError("provides entries must be unique")
    lifecycle=manifest["lifecycle"]; expected=["discover","validate","register","health-check","serve"]
    if lifecycle!=expected: raise ValueError(f"lifecycle must be ordered as {expected}")
    canonical=json.dumps(manifest,sort_keys=True,separators=(",",":"))
    return {"valid":True,"name":name,"provides":provides,"capability_count":len(provides),"manifest_sha256":hashlib.sha256(canonical.encode()).hexdigest(),"normalized":manifest,
            "install_checks":["entry point import","module schema","named tests","health probe","format conformance"]}


def resolve_plugin_order(manifests: list[dict]) -> dict:
    """Topologically resolve plugin dependencies, rejecting cycles and missing providers."""
    validated=[validate_plugin_manifest(x) for x in manifests]
    names=[x["name"] for x in validated]
    # BUG 67: duplicate names silently collapsed into one plugin (the dict
    # below overwrote the first manifest), losing capabilities.
    if len(names)!=len(set(names)):
        dupes=sorted({n for n in names if names.count(n)>1})
        raise ValueError(f"duplicate plugin names: {dupes}")
    names=set(names)
    deps={x["name"]:set(x["normalized"].get("depends_on",[])) for x in validated}
    missing={n:sorted(v-names) for n,v in deps.items() if v-names}
    if missing: raise ValueError(f"missing plugin dependencies: {missing}")
    reverse=defaultdict(set); indegree={n:len(d) for n,d in deps.items()}
    for n,ds in deps.items():
        for d in ds: reverse[d].add(n)
    ready=deque(sorted(n for n,v in indegree.items() if v==0)); order=[]
    while ready:
        n=ready.popleft(); order.append(n)
        for nxt in sorted(reverse[n]):
            indegree[nxt]-=1
            if indegree[nxt]==0: ready.append(nxt)
    if len(order)!=len(names): raise ValueError("plugin dependency cycle detected")
    return {"install_order":order,"plugin_count":len(order),"dependency_edges":sum(len(x) for x in deps.values()),"parallel_roots":sorted(n for n,d in deps.items() if not d)}


def generate_sdk_client(module: str, operation: str, *, language: str="python", base_url: str="https://api.sugarcode.local") -> dict:
    """Generate an executable authenticated client snippet with input/output contracts."""
    if module not in REGISTRY: raise ValueError(f"unknown module {module!r}")
    if not re.fullmatch(r"[a-z][a-z0-9_]*",operation): raise ValueError("operation must be a lowercase Python-style name")
    if not base_url.startswith("https://"): raise ValueError("base_url must use https")
    path=f"/v1/modules/{module}/{operation}"
    if language=="python":
        code=f'''import os\nimport requests\n\npayload = {{"input": "replace-with-validated-data"}}\nr = requests.post("{base_url}{path}", json=payload, headers={{"Authorization": f"Bearer {{os.environ['SUGARCODE_KEY']}}"}}, timeout=60)\nr.raise_for_status()\nresult = r.json()\n'''
    elif language=="curl": code=f'''curl --fail-with-body --max-time 60 -X POST "{base_url}{path}" \\\n  -H "Authorization: Bearer $SUGARCODE_KEY" -H "Content-Type: application/json" \\\n  --data '{{"input":"replace-with-validated-data"}}'\n'''
    else: raise ValueError("language must be python or curl")
    return {"module":module,"operation":operation,"language":language,"method":"POST","path":path,"code":code,"required_environment":["SUGARCODE_KEY"],"timeout_seconds":60,"response_format":"JSON"}


def standards_plan(data_assets: list[dict]) -> dict:
    """Map lab assets to interoperable standards and concrete conversion actions."""
    if not isinstance(data_assets,list) or not data_assets: raise ValueError("data_assets must be a non-empty list")
    rows=[]
    for i,a in enumerate(data_assets):
        if not isinstance(a,dict) or not a.get("name") or not a.get("type"): raise ValueError(f"asset {i} requires name and type")
        kind=str(a["type"]).lower(); formats=STANDARDS.get(kind)
        if not formats: raise ValueError(f"asset {a['name']!r} has unsupported type {kind!r}; choose {sorted(STANDARDS)}")
        current=str(a.get("format","")).upper(); compliant=current in {x.upper() for x in formats}; target=formats[0]
        rows.append({"name":a["name"],"type":kind,"current_format":current or None,"accepted_formats":formats,"target_format":current if compliant else target,
          "compliant":compliant,"action":"validate schema" if compliant else f"convert {current or 'source'} to {target}","provenance_required":True})
    return {"assets":rows,"asset_count":len(rows),"compliant_count":sum(x["compliant"] for x in rows),"conversion_count":sum(not x["compliant"] for x in rows),
            "workflow_actions":[x["action"] for x in rows],"collaboration_package":["README","checksums.sha256","provenance.json","license.txt"]}


def enhancement_features(manifests: list[dict], assets: list[dict], module: str, operation: str) -> dict:
    """Compute exactly 50 integration diagnostics from actual project inputs."""
    validated=[validate_plugin_manifest(x) for x in manifests]; order=resolve_plugin_order(manifests); standards=standards_plan(assets); sdk=generate_sdk_client(module,operation)
    deps=[len(x["normalized"].get("depends_on",[])) for x in validated]; capabilities=[len(x["provides"]) for x in validated]; names=[x["name"] for x in validated]
    out={"plugin_count":len(validated),"plugin_name_count":len(set(names)),"capability_total":sum(capabilities),"capability_minimum":min(capabilities),"capability_maximum":max(capabilities),
    "capability_range":max(capabilities)-min(capabilities),"dependency_edge_count":order["dependency_edges"],"dependency_root_count":len(order["parallel_roots"]),"dependency_leaf_count":sum(not any(x["name"] in y["normalized"].get("depends_on",[]) for y in validated) for x in validated),
    "install_order_count":len(order["install_order"]),"maximum_direct_dependencies":max(deps),"plugins_with_dependencies":sum(x>0 for x in deps),"plugins_without_dependencies":sum(x==0 for x in deps),
    "manifest_unique_digest_count":len({x["manifest_sha256"] for x in validated}),"first_plugin_name_length":len(order["install_order"][0]),"last_plugin_name_length":len(order["install_order"][-1]),
    "asset_count":standards["asset_count"],"compliant_asset_count":standards["compliant_count"],"conversion_asset_count":standards["conversion_count"],"compliance_fraction":standards["compliant_count"]/standards["asset_count"],
    "sequence_asset_count":sum(a["type"]=="sequence" for a in standards["assets"]),"structure_asset_count":sum(a["type"]=="structure" for a in standards["assets"]),"variant_asset_count":sum(a["type"]=="variants" for a in standards["assets"]),
    "model_asset_count":sum(a["type"]=="models" for a in standards["assets"]),"imaging_asset_count":sum(a["type"]=="imaging" for a in standards["assets"]),"tabular_asset_count":sum(a["type"]=="tabular" for a in standards["assets"]),
    "asset_type_count":len({a["type"] for a in standards["assets"]}),"current_format_count":len({a["current_format"] for a in standards["assets"]}),"target_format_count":len({a["target_format"] for a in standards["assets"]}),
    "provenance_required_count":sum(a["provenance_required"] for a in standards["assets"]),"workflow_action_count":len(standards["workflow_actions"]),"collaboration_file_count":len(standards["collaboration_package"]),
    "sdk_code_character_count":len(sdk["code"]),"sdk_code_line_count":len(sdk["code"].splitlines()),"sdk_path_length":len(sdk["path"]),"sdk_operation_length":len(operation),"sdk_module_length":len(module),
    "sdk_timeout_seconds":sdk["timeout_seconds"],"sdk_environment_variable_count":len(sdk["required_environment"]),"registry_module_count":len(REGISTRY),"registry_subnetwork_count":len(SUBNETWORKS),
    "selected_subnetwork":REGISTRY[module].subnetwork,"selected_module_status":REGISTRY[module].status,"selected_module_summary_length":len(REGISTRY[module].summary),
    "plugin_name_total_characters":sum(map(len,names)),"capability_name_total_characters":sum(len(p) for x in validated for p in x["provides"]),"dependency_density":order["dependency_edges"]/max(1,len(validated)*(len(validated)-1)),
    "conversion_fraction":standards["conversion_count"]/standards["asset_count"],"install_parallelism":len(order["parallel_roots"])/len(validated),"integration_readiness_score":(standards["compliant_count"]/standards["asset_count"]+len(order["parallel_roots"])/len(validated))/2}
    assert len(out)==50
    return out


def build_integration_package(manifests: list[dict], assets: list[dict], module: str, operation: str, *, language="python") -> dict:
    """Build a developer-ready plugin, SDK, standards, and collaboration package."""
    return {"plugin_validation":[validate_plugin_manifest(x) for x in manifests],"plugin_order":resolve_plugin_order(manifests),
      "sdk":generate_sdk_client(module,operation,language=language),"standards":standards_plan(assets),
      "diagnostics":enhancement_features(manifests,assets,module,operation),"diagnostic_count":50,
      "release_checklist":["run named tests","verify health endpoint","validate example payload","pin API version","publish checksums and provenance"],
      "model_status":"deterministic hermetic integration tooling"}
