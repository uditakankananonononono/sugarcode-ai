"""Dependency-free HTML/Markdown report renderer.

Reports are built from typed blocks so every consumer renders the same
structure in both formats. All user/data text is HTML-escaped; renderers
never embed raw markup from data. Block types:

  paragraph  {"type": "paragraph", "text": str}
  kv         {"type": "kv", "items": {key: scalar}}            definition table
  table      {"type": "table", "columns": [..], "rows": [[..]]}
  list       {"type": "list", "items": [str]}
  note       {"type": "note", "text": str}                     highlighted callout
  provenance {"type": "provenance", "items": [str]}            source/limitation ledger
"""
from __future__ import annotations

import html
from datetime import datetime, timezone

_BLOCK_TYPES = {"paragraph", "kv", "table", "list", "note", "provenance"}
_CSS = (
    "body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
    "margin:2.5rem auto;max-width:860px;color:#1a1a2e;line-height:1.5}"
    "h1{border-bottom:3px solid #2d6a4f;padding-bottom:.3rem}"
    "h2{color:#2d6a4f;margin-top:1.8rem}"
    "table{border-collapse:collapse;width:100%;margin:.6rem 0}"
    "th,td{border:1px solid #c8d0cc;padding:.35rem .55rem;text-align:left;"
    "font-size:.92rem;vertical-align:top}"
    "th{background:#eef4f1}"
    ".meta{color:#5a6b62;font-size:.85rem}"
    ".note{background:#fff8e1;border-left:4px solid #d4a017;padding:.5rem .8rem}"
    ".provenance{background:#f1f5f3;border-left:4px solid #2d6a4f;padding:.5rem .8rem;"
    "font-size:.88rem}"
    ".provenance li{margin:.15rem 0}"
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _check_sections(sections: list[dict]) -> None:
    if not isinstance(sections, list) or not sections:
        raise ValueError("sections must be a non-empty list")
    for i, s in enumerate(sections):
        if not isinstance(s, dict):
            raise TypeError(f"section {i} is not a dict")
        if not isinstance(s.get("heading"), str) or not s["heading"].strip():
            raise ValueError(f"section {i} needs a non-empty heading")
        blocks = s.get("blocks")
        if not isinstance(blocks, list):
            raise ValueError(f"section {i} blocks must be a list")
        for b in blocks:
            t = b.get("type") if isinstance(b, dict) else None
            if t not in _BLOCK_TYPES:
                raise ValueError(f"unknown block type {t!r} in section {i}")


def _esc(x) -> str:
    return html.escape(str(x), quote=True)


def _block_html(b: dict) -> str:
    t = b["type"]
    if t == "paragraph":
        return f"<p>{_esc(b['text'])}</p>"
    if t == "note":
        return f"<div class='note'>{_esc(b['text'])}</div>"
    if t == "kv":
        rows = "".join(
            f"<tr><th>{_esc(k)}</th><td>{_esc(v)}</td></tr>"
            for k, v in b["items"].items())
        return f"<table>{rows}</table>"
    if t == "table":
        head = "".join(f"<th>{_esc(c)}</th>" for c in b["columns"])
        body = "".join(
            "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in r) + "</tr>"
            for r in b["rows"])
        return f"<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table>"
    if t == "list":
        items = "".join(f"<li>{_esc(x)}</li>" for x in b["items"])
        return f"<ul>{items}</ul>"
    items = "".join(f"<li>{_esc(x)}</li>" for x in b["items"])
    return f"<div class='provenance'><strong>Provenance &amp; limitations</strong><ul>{items}</ul></div>"


def render_html_report(title: str, sections: list[dict], *,
                       generated_utc: str | None = None,
                       footer: str | None = None) -> str:
    """Render a complete standalone HTML document. Escapes all data text."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be non-empty")
    _check_sections(sections)
    generated = generated_utc or _utc_now()
    body = [f"<h1>{_esc(title)}</h1>",
            f"<p class='meta'>Generated {html.escape(generated)} by sugarcode-ai report engine</p>"]
    for s in sections:
        body.append(f"<h2>{_esc(s['heading'])}</h2>")
        body.extend(_block_html(b) for b in s["blocks"])
    if footer:
        body.append(f"<p class='meta'>{_esc(footer)}</p>")
    return ("<!DOCTYPE html>\n<html lang='en'><head><meta charset='utf-8'>"
            f"<title>{_esc(title)}</title><style>{_CSS}</style></head><body>"
            + "\n".join(body) + "</body></html>\n")


def _block_md(b: dict) -> list[str]:
    t = b["type"]
    if t in ("paragraph", "note"):
        prefix = "> " if t == "note" else ""
        return [f"{prefix}{b['text']}", ""]
    if t == "kv":
        return [f"- **{k}**: {v}" for k, v in b["items"].items()] + [""]
    if t == "table":
        lines = ["| " + " | ".join(str(c) for c in b["columns"]) + " |",
                 "|" + "---|" * len(b["columns"])]
        lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in b["rows"]]
        return lines + [""]
    if t == "list":
        return [f"- {x}" for x in b["items"]] + [""]
    return ["**Provenance & limitations**"] + [f"- {x}" for x in b["items"]] + [""]


def render_markdown_report(title: str, sections: list[dict], *,
                           generated_utc: str | None = None,
                           footer: str | None = None) -> str:
    """Render the same sections as a Markdown document."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be non-empty")
    _check_sections(sections)
    generated = generated_utc or _utc_now()
    lines = [f"# {title}", "", f"_Generated {generated} by sugarcode-ai report engine_", ""]
    for s in sections:
        lines.append(f"## {s['heading']}")
        lines.append("")
        for b in s["blocks"]:
            lines.extend(_block_md(b))
    if footer:
        lines += [f"_{footer}_", ""]
    return "\n".join(lines).rstrip() + "\n"
