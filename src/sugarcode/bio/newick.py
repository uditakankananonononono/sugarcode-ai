"""Newick phylogenetic-tree toolkit.

Trees are nested dicts: {"name": str|None, "length": float|None,
"children": [..]}. Internal-node labels stay strings (they are usually
support values - the format does not distinguish, and guessing would be
dishonest). Missing branch lengths count as 0 in distance math and are
reported separately in stats, never silently invented.
"""
from __future__ import annotations


def _tokenize(text: str) -> list[tuple[str, str]]:
    toks, i, n = [], 0, len(text)
    while i < n:
        ch = text[i]
        if ch.isspace():
            i += 1
        elif ch == "[" and i + 1 < n and text[i + 1] == "&":
            j = text.find("]", i + 2)
            if j == -1:
                raise ValueError("unterminated [&...] comment")
            i = j + 1
        elif ch in "(),:;":
            toks.append((ch, ch))
            i += 1
        elif ch == "'":
            j = i + 1
            buf = []
            while j < n:
                if text[j] == "'":
                    if j + 1 < n and text[j + 1] == "'":
                        buf.append("'")
                        j += 2
                        continue
                    break
                buf.append(text[j])
                j += 1
            if j >= n:
                raise ValueError("unterminated quoted label")
            toks.append(("label", "".join(buf)))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in "(),:;' \t\n\r[]":
                j += 1
            toks.append(("label", text[i:j]))
            i = j
    return toks


def parse_newick(text: str) -> dict:
    toks = _tokenize(text)
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else (None, None)

    def subtree() -> dict:
        nonlocal pos
        node: dict = {"name": None, "length": None, "children": []}
        if peek()[0] == "(":
            pos += 1
            node["children"].append(subtree())
            while peek()[0] == ",":
                pos += 1
                node["children"].append(subtree())
            if peek()[0] != ")":
                raise ValueError(f"expected ')' at token {pos}")
            pos += 1
        if peek()[0] == "label":
            node["name"] = peek()[1]
            pos += 1
        if peek()[0] == ":":
            pos += 1
            if peek()[0] != "label":
                raise ValueError(f"branch length missing after ':' at token {pos}")
            try:
                node["length"] = float(peek()[1])
            except ValueError:
                raise ValueError(f"invalid branch length {peek()[1]!r}")
            pos += 1
        return node

    root = subtree()
    if peek()[0] != ";":
        raise ValueError("Newick tree must end with ';'")
    if pos != len(toks) - 1:
        raise ValueError("trailing content after ';'")
    if not root["children"]:
        raise ValueError("tree has a single node - nothing to root")
    return root


def write_newick(root: dict) -> str:
    def rec(node: dict) -> str:
        s = ""
        if node["children"]:
            s += "(" + ",".join(rec(c) for c in node["children"]) + ")"
        if node["name"] is not None:
            if any(c in node["name"] for c in " (),:;'[]"):
                s += "'" + node["name"].replace("'", "''") + "'"
            else:
                s += node["name"]
        if node["length"] is not None:
            s += ":" + ("%g" % node["length"])
        return s
    return rec(root) + ";\n"


def _walk(node: dict, parent: int | None, nodes: list, parents: list) -> int:
    idx = len(nodes)
    nodes.append(node)
    parents.append(parent)
    for c in node["children"]:
        _walk(c, idx, nodes, parents)
    return idx


def _index(root: dict) -> tuple[list, list]:
    nodes: list = []
    parents: list = []
    _walk(root, None, nodes, parents)
    return nodes, parents


def leaves(root: dict) -> list[str]:
    return [n["name"] for n in preorder(root) if not n["children"] and n["name"]]


def preorder(root: dict) -> list[dict]:
    out = [root]
    for c in root["children"]:
        out.extend(preorder(c))
    return out


def stats(root: dict) -> dict:
    nodes = preorder(root)
    lv = [n for n in nodes if not n["children"]]
    internal = [n for n in nodes if n["children"]]
    lengths = [n["length"] for n in nodes if n["length"] is not None]
    missing = sum(1 for n in nodes[1:] if n["length"] is None)
    def height(node: dict) -> float:
        if not node["children"]:
            return 0.0
        return max((c["length"] or 0.0) + height(c) for c in node["children"])
    return {
        "nodes": len(nodes),
        "leaves": len(lv),
        "internal_nodes": len(internal),
        "binary": all(len(n["children"]) == 2 for n in internal),
        "total_branch_length": round(sum(lengths), 6),
        "edges_missing_length": missing,
        "height": round(height(root), 6),
        "leaf_names": sorted(n["name"] for n in lv if n["name"]),
    }


def mrca(root: dict, leaf_names: list[str]) -> dict:
    """Most recent common ancestor of the named leaves."""
    nodes, parents = _index(root)
    leaf_idx = {n["name"]: i for i, n in enumerate(nodes)
                if not n["children"] and n["name"]}
    missing = [x for x in leaf_names if x not in leaf_idx]
    if missing:
        raise ValueError(f"unknown leaves {missing}; have {sorted(leaf_idx)}")
    # ordered ancestor path of the first leaf, leaf-up-to-root
    ordered: list[int] = []
    i: int | None = leaf_idx[leaf_names[0]]
    while i is not None:
        ordered.append(i)
        i = parents[i]
    ancestors = set(ordered)
    for name in leaf_names[1:]:
        path = set()
        i = leaf_idx[name]
        while i is not None:
            path.add(i)
            i = parents[i]
        ancestors &= path
    # deepest common ancestor = first node on the leaf-up path still common
    for i in ordered:
        if i in ancestors:
            return nodes[i]
    return root


def distance(root: dict, a: str, b: str) -> float:
    """Path length between two leaves through their MRCA."""
    nodes, parents = _index(root)
    leaf_idx = {n["name"]: i for i, n in enumerate(nodes)
                if not n["children"] and n["name"]}
    for x in (a, b):
        if x not in leaf_idx:
            raise ValueError(f"unknown leaf {x!r}")
    anc = mrca(root, [a, b])
    anc_i = next(i for i, n in enumerate(nodes) if n is anc)
    def up(i: int) -> float:
        d = 0.0
        while i != anc_i:
            d += nodes[i]["length"] or 0.0
            i = parents[i]
        return d
    return round(up(leaf_idx[a]) + up(leaf_idx[b]), 6)


def prune(root: dict, drop: list[str]) -> dict:
    """Remove named leaves, collapsing single-child internal nodes and
    summing merged branch lengths."""
    import copy
    tree = copy.deepcopy(root)
    drop_set = set(drop)
    names = {n["name"] for n in preorder(tree) if not n["children"]}
    unknown = drop_set - names
    if unknown:
        raise ValueError(f"cannot prune unknown leaves {sorted(unknown)}")

    def rec(node: dict) -> dict | None:
        if not node["children"]:
            return None if node["name"] in drop_set else node
        kept = [c for c in (rec(c) for c in node["children"]) if c is not None]
        if not kept:
            return None  # internal node emptied by pruning is not a leaf
        node["children"] = kept
        return node

    tree = rec(tree)
    if tree is None:
        raise ValueError("pruning removed every leaf")

    def collapse(node: dict, is_root: bool) -> dict:
        node["children"] = [collapse(c, False) for c in node["children"]]
        while len(node["children"]) == 1 and not is_root:
            child = node["children"][0]
            if child["length"] is not None or node["length"] is not None:
                merged = (child["length"] or 0.0) + (node["length"] or 0.0)
            else:
                merged = None
            node.update({
                "name": child["name"] if child["name"] is not None else node["name"],
                "length": merged,
                "children": child["children"]})
        return node

    tree = collapse(tree, True)
    while len(tree["children"]) == 1:
        tree = tree["children"][0]
    return tree
