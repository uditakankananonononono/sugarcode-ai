"""PDB and mmCIF structure toolkit.

PDB: fixed-column ATOM/HETATM records (cols per PDB 3.3 spec), HEADER/TITLE
metadata, MODEL/ENDMDL multi-model support (every atom carries its model
number; queries default to model 1).

mmCIF: a minimal but real CIF tokenizer (quoted strings, semicolon text
blocks, data_/loop_ frames) - enough to parse the ``_atom_site`` loop that
carries coordinates, which is what the docking/structure modules need. It is
NOT a general mmCIF writer; structure output is PDB via write_pdb (stated,
not silent).

Atom dict: {serial, name, altloc, resname, chain, resseq, icode, x, y, z,
occupancy, bfactor, element, record (ATOM/HETATM), model}.
"""
from __future__ import annotations

import math


# ---------------------------------------------------------------- PDB ----

def parse_pdb(text: str) -> dict:
    atoms, title_parts, header = [], [], {}
    model = 1
    for ln, line in enumerate(text.splitlines(), start=1):
        rec = line[:6].strip()
        line = line.ljust(80)
        if rec == "HEADER":
            header["classification"] = line[10:50].strip()
            header["id"] = line[62:66].strip()
        elif rec == "TITLE":
            title_parts.append(line[10:80].strip())
        elif rec == "MODEL":
            try:
                model = int(line[10:14])
            except ValueError:
                raise ValueError(f"line {ln}: malformed MODEL record")
        elif rec in ("ATOM", "HETATM"):
            try:
                atoms.append({
                    "serial": int(line[6:11]),
                    "name": line[12:16].strip(),
                    "altloc": line[16:17].strip() or None,
                    "resname": line[17:20].strip(),
                    "chain": line[21:22].strip(),
                    "resseq": int(line[22:26]),
                    "icode": line[26:27].strip() or None,
                    "x": float(line[30:38]),
                    "y": float(line[38:46]),
                    "z": float(line[46:54]),
                    "occupancy": (float(line[54:60])
                                  if line[54:60].strip() else None),
                    "bfactor": (float(line[60:66])
                                if line[60:66].strip() else None),
                    "element": line[76:78].strip() or None,
                    "record": rec, "model": model,
                })
            except ValueError as e:
                raise ValueError(f"line {ln}: malformed {rec} record ({e})")
    if title_parts:
        header["title"] = " ".join(title_parts)
    if not atoms:
        raise ValueError("no ATOM/HETATM records found")
    return {"format": "pdb", "header": header, "atoms": atoms}


def write_pdb(structure: dict) -> str:
    out = []
    for a in structure["atoms"]:
        out.append(
            f"{a['record']:<6}{a['serial']:5d} {a['name']:^4}"
            f"{a['altloc'] or ' '}{a['resname']:>3} {a['chain'] or ' '}"
            f"{a['resseq']:4d}{a['icode'] or ' '}   "
            f"{a['x']:8.3f}{a['y']:8.3f}{a['z']:8.3f}"
            f"{(a['occupancy'] if a['occupancy'] is not None else 1.0):6.2f}"
            f"{(a['bfactor'] if a['bfactor'] is not None else 0.0):6.2f}"
            f"          {(a['element'] or ''):>2}  ")
    out.append("END")
    return "\n".join(out) + "\n"


# --------------------------------------------------------------- mmCIF ----

def _tokenize_cif(text: str) -> list[str]:
    tokens, lines, i = [], text.splitlines(), 0
    while i < len(lines):
        line = lines[i]
        if line.lstrip().startswith("#"):
            i += 1
            continue  # CIF comment
        if line.startswith(";"):
            buf = [line[1:]]
            i += 1
            while i < len(lines) and not lines[i].startswith(";"):
                buf.append(lines[i])
                i += 1
            if i >= len(lines):
                raise ValueError("unterminated semicolon text block")
            tokens.append("\n".join(buf))
            i += 1
            continue
        tokens.extend(_split_cif_line(line))
        i += 1
    return tokens


def _split_cif_line(line: str) -> list[str]:
    """CIF 1.1 whitespace tokenizer. A value opening with ' or " is quoted and
    closes only at the same quote followed by whitespace or end of line, so
    embedded primes survive (atom names like O5' or "C1'"); an unquoted value
    runs to the next whitespace; '#' outside a value starts a comment. POSIX
    shlex got this wrong on every real RCSB mmCIF (e.g. unquoted O5')."""
    out, j, n = [], 0, len(line)
    while j < n:
        c = line[j]
        if c in " \t":
            j += 1
            continue
        if c == "#":
            break
        if c in "'\"":
            k = j + 1
            while k < n and not (line[k] == c and (k + 1 == n or line[k + 1] in " \t")):
                k += 1
            if k >= n:
                raise ValueError(f"unterminated quoted CIF value: {line[j:j + 40]!r}")
            out.append(line[j + 1:k])
            j = k + 1
            continue
        k = j
        while k < n and line[k] not in " \t":
            k += 1
        out.append(line[j:k])
        j = k
    return out


def _parse_cif(tokens: list[str]) -> dict:
    """Frame parser: returns {category: {column: [values]}}."""
    cats: dict[str, dict[str, list[str]]] = {}
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok == "loop_":
            i += 1
            cols = []
            while i < len(tokens) and tokens[i].startswith("_"):
                cols.append(tokens[i])
                i += 1
            if not cols:
                raise ValueError("loop_ with no columns")
            for c in cols:
                cat, col = c.split(".", 1) if "." in c else (c, "")
                cats.setdefault(cat, {}).setdefault(col, [])
            n = 0
            # A reserved-looking token ends the loop only at a row boundary:
            # RCSB files carry unquoted item names as values mid-row
            # (e.g. _pdbx_audit_revision_item.item = _database_2.pdbx_DOI).
            while (i < len(tokens) and tokens[i] != "stop_"
                   and not (n % len(cols) == 0 and tokens[i].startswith(
                       ("_", "data_", "loop_", "save_")))):
                cat, col = cols[n % len(cols)].split(".", 1)
                cats[cat][col].append(tokens[i])
                n += 1
                i += 1
            if n % len(cols) != 0:
                raise ValueError(f"loop_ row count {n} is not a multiple of "
                                 f"{len(cols)} columns")
            if i < len(tokens) and tokens[i] == "stop_":
                i += 1
        elif tok.startswith("_"):
            cat, col = tok.split(".", 1) if "." in tok else (tok, "")
            if i + 1 >= len(tokens):
                raise ValueError(f"dangling key {tok}")
            cats.setdefault(cat, {}).setdefault(col, []).append(tokens[i + 1])
            i += 2
        else:
            i += 1  # data_ blocks and stray markers
    return cats


def _cif_null(v: str):
    return None if v in (".", "?") else v


def parse_mmcif(text: str) -> dict:
    cats = _parse_cif(_tokenize_cif(text))
    site = cats.get("_atom_site")
    if site is None:
        raise ValueError("no _atom_site loop found")
    rows = len(next(iter(site.values())))

    def get(col: str, j: int, default=None):
        vals = site.get(col)
        if vals is None or j >= len(vals):
            return default
        return _cif_null(vals[j])

    atoms = []
    for j in range(rows):
        try:
            name = get("label_atom_id", j) or get("auth_atom_id", j)
            chain = get("auth_asym_id", j) or get("label_asym_id", j) or ""
            resseq = get("auth_seq_id", j) or get("label_seq_id", j)
            atoms.append({
                "serial": int(get("id", j)),
                "name": name,
                "altloc": get("label_alt_id", j),
                "resname": get("label_comp_id", j),
                "chain": chain,
                "resseq": int(resseq),
                "icode": get("pdbx_PDB_ins_code", j),
                "x": float(get("Cartn_x", j)),
                "y": float(get("Cartn_y", j)),
                "z": float(get("Cartn_z", j)),
                "occupancy": (float(v) if (v := get("occupancy", j))
                              is not None else None),
                "bfactor": (float(v) if (v := get("B_iso_or_equiv", j))
                            is not None else None),
                "element": get("type_symbol", j),
                "record": get("group_PDB", j) or "ATOM",
                "model": int(get("pdbx_PDB_model_num", j) or 1),
            })
        except (TypeError, ValueError) as e:
            raise ValueError(f"_atom_site row {j + 1}: malformed ({e})")
    if not atoms:
        raise ValueError("_atom_site loop is empty")
    return {"format": "mmcif", "header": {}, "atoms": atoms}


# ------------------------------------------------------------- queries ----

def _atoms(structure: dict) -> list[dict]:
    return structure["atoms"]


def chains(structure: dict) -> list[str]:
    return sorted({a["chain"] for a in _atoms(structure)})


def residues(structure: dict, chain: str | None = None) -> list[dict]:
    seen, out = set(), []
    for a in _atoms(structure):
        if chain is not None and a["chain"] != chain:
            continue
        key = (a["chain"], a["resseq"], a["icode"])
        if key not in seen:
            seen.add(key)
            out.append({"chain": a["chain"], "resseq": a["resseq"],
                        "icode": a["icode"], "resname": a["resname"],
                        "model": a["model"]})
    return out


def select(structure: dict, *, chain: str | None = None,
           resname: str | None = None, names: list[str] | None = None,
           record: str | None = None, model: int | None = 1,
           min_bfactor: float | None = None) -> list[dict]:
    """Atom filter. model=1 selects the first model by default (multi-model
    files); pass model=None for all models."""
    out = []
    for a in _atoms(structure):
        if model is not None and a["model"] != model:
            continue
        if chain is not None and a["chain"] != chain:
            continue
        if resname is not None and a["resname"] != resname:
            continue
        if names is not None and a["name"] not in names:
            continue
        if record is not None and a["record"] != record:
            continue
        if (min_bfactor is not None
                and (a["bfactor"] is None or a["bfactor"] < min_bfactor)):
            continue
        out.append(a)
    return out


def coordinates(atoms: list[dict]) -> list[tuple[float, float, float]]:
    return [(a["x"], a["y"], a["z"]) for a in atoms]


def centroid(atoms: list[dict]) -> tuple[float, float, float]:
    if not atoms:
        raise ValueError("no atoms")
    n = len(atoms)
    return (sum(a["x"] for a in atoms) / n,
            sum(a["y"] for a in atoms) / n,
            sum(a["z"] for a in atoms) / n)


def distance(a: dict, b: dict) -> float:
    return math.sqrt((a["x"] - b["x"]) ** 2 + (a["y"] - b["y"]) ** 2
                     + (a["z"] - b["z"]) ** 2)


def contacts(structure: dict, cutoff: float, *,
             chain_a: str | None = None, chain_b: str | None = None,
             model: int | None = 1,
             exclude_same_residue: bool = True) -> list[dict]:
    """Atom pairs within `cutoff` angstrom. With both chains given, only
    cross-chain pairs are reported (chain_a x chain_b)."""
    if cutoff <= 0:
        raise ValueError("cutoff must be positive")
    atoms = select(structure, model=model)
    out = []
    for i, a in enumerate(atoms):
        if chain_a is not None and a["chain"] != chain_a:
            continue
        for b in atoms[i + 1:]:
            if chain_b is not None and b["chain"] != chain_b:
                continue
            if chain_a is not None and chain_b is not None \
                    and a["chain"] == b["chain"]:
                continue
            if exclude_same_residue and a["chain"] == b["chain"] \
                    and a["resseq"] == b["resseq"] \
                    and a["icode"] == b["icode"]:
                continue
            d = distance(a, b)
            if d <= cutoff:
                out.append({"a": {"serial": a["serial"], "name": a["name"],
                                  "resname": a["resname"],
                                  "chain": a["chain"],
                                  "resseq": a["resseq"]},
                            "b": {"serial": b["serial"], "name": b["name"],
                                  "resname": b["resname"],
                                  "chain": b["chain"],
                                  "resseq": b["resseq"]},
                            "distance": round(d, 4)})
    return out


def stats(structure: dict) -> dict:
    atoms = _atoms(structure)
    res_keys = {(a["chain"], a["resseq"], a["icode"], a["model"])
                for a in atoms}
    return {"format": structure["format"], "models": len({a["model"]
                                                          for a in atoms}),
            "chains": chains(structure), "residues": len(res_keys),
            "atoms": len(atoms),
            "hetatms": sum(1 for a in atoms if a["record"] == "HETATM"),
            "elements": sorted({a["element"] for a in atoms
                                if a["element"]})}
