"""Glow report renderer: a visual v2 pass over the typed-block contract.

Same block schema and validation behavior as report.engine (paragraph, kv,
table, list, note, provenance), rendered as a styled standalone HTML
document. Named features:

  F1 header band      title and generated-meta inside a gradient banner
  F2 section cards    each section in a bordered, shadowed card
  F3 status pills     kv values in STATUS_VOCAB render as colored pills
  F4 dark mode+print  CSS variables, prefers-color-scheme dark, print rules
  F5 responsive tables  horizontal-scroll wrapper and zebra rows

All data text is HTML-escaped; no raw markup from data is ever embedded.
HTML only; the engine's Markdown renderer is unchanged and untouched.

Validation parity with report.engine: non-str title, non-list sections
and non-str heading raise ValueError, as the engine does. One deliberate
addition: generated_utc is a glow-only parameter and a non-str value
raises TypeError; a blank banner raises ValueError.
"""
from __future__ import annotations

import html
from datetime import datetime, timezone

_BLOCK_TYPES = {"paragraph", "kv", "table", "list", "note", "provenance"}

STATUS_VOCAB = {
    "pathogenic": "pill-bad", "fail": "pill-bad", "error": "pill-bad", "high": "pill-bad",
    "likely pathogenic": "pill-warn", "vus": "pill-warn", "warn": "pill-warn",
    "moderate": "pill-warn",
    "benign": "pill-good", "pass": "pill-good", "ok": "pill-good", "low": "pill-good",
    "likely benign": "pill-neutral",
}

_CSS = (
    ":root{--bg:#f4f6f5;--card:#ffffff;--ink:#1a1a2e;--muted:#5a6b62;"
    "--accent:#2d6a4f;--accent2:#52b788;--line:#d8e0dc;--note-bg:#fff8e1;"
    "--note-edge:#d4a017;--prov-bg:#eef4f1;--zebra:#f6f9f7}"
    "*{box-sizing:border-box}"
    "body{font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;"
    "margin:0;background:var(--bg);color:var(--ink);line-height:1.55}"
    ".band{max-width:960px;margin:1.5rem auto 0;padding:1.6rem 2rem;color:#ffffff;"
    "background:linear-gradient(120deg,#1b4332,#2d6a4f 55%,#40916c);"
    "border-radius:14px;box-shadow:0 6px 18px rgba(27,67,50,.25)}"
    ".band h1{margin:0;font-size:1.7rem}"
    ".band .meta{color:#d8f3e3;font-size:.85rem;margin:.35rem 0 0}"
    "main{max-width:960px;margin:1.2rem auto 2.5rem;padding:0 1rem}"
    ".card{background:var(--card);border:1px solid var(--line);border-radius:12px;"
    "box-shadow:0 2px 8px rgba(26,26,46,.06);padding:1.1rem 1.4rem;margin:1.1rem 0}"
    ".card h2{color:var(--accent);margin:.2rem 0 .8rem;font-size:1.25rem;"
    "border-bottom:2px solid var(--accent2);padding-bottom:.3rem}"
    ".table-wrap{overflow-x:auto;margin:.6rem 0}"
    "table{border-collapse:collapse;width:100%}"
    "th,td{border:1px solid var(--line);padding:.4rem .6rem;text-align:left;"
    "font-size:.92rem;vertical-align:top}"
    "th{background:var(--prov-bg)}"
    "tbody tr:nth-child(even){background:var(--zebra)}"
    ".pill{display:inline-block;padding:.1rem .6rem;border-radius:999px;"
    "font-size:.82rem;font-weight:600;white-space:nowrap}"
    ".pill-bad{background:#fde2e1;color:#9d0208}"
    ".pill-warn{background:#fff3cd;color:#9c6d00}"
    ".pill-good{background:#d8f3dc;color:#1b5e20}"
    ".pill-neutral{background:#e2eafc;color:#31518b}"
    ".note{background:var(--note-bg);border-left:4px solid var(--note-edge);"
    "padding:.55rem .85rem;border-radius:0 8px 8px 0}"
    ".provenance{background:var(--prov-bg);border-left:4px solid var(--accent);"
    "padding:.55rem .85rem;font-size:.88rem;border-radius:0 8px 8px 0}"
    ".provenance li{margin:.15rem 0}"
    "footer.meta{max-width:960px;margin:0 auto 2rem;color:var(--muted);font-size:.85rem}"
    ".banner{max-width:960px;margin:1rem auto 0;padding:.5rem 1rem;text-align:center;"
    "font-weight:700;letter-spacing:.08em;color:#7a5b00;background:#ffe9a8;"
    "border:2px dashed #d4a017;border-radius:8px}"
    "@media (prefers-color-scheme:dark){:root{--bg:#101512;--card:#182019;"
    "--ink:#e6ece8;--muted:#93a89c;--line:#2c3a31;--note-bg:#3a3416;"
    "--prov-bg:#1d2b23;--zebra:#1e2822;--accent:#52b788;--accent2:#95d5b2}"
    ".band{background:linear-gradient(120deg,#081c15,#1b4332 55%,#2d6a4f)}}"
    "@media print{body{background:#ffffff}.band,.card{box-shadow:none;border:1px solid #999;"
    "border-radius:0}.band{color:#000;background:none}.band .meta{color:#333}}"
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


def _kv_value_html(v) -> str:
    if isinstance(v, str) and v.lower() in STATUS_VOCAB:
        return f"<span class='pill {STATUS_VOCAB[v.lower()]}'>{_esc(v)}</span>"
    return _esc(v)


def _block_html(b: dict) -> str:
    t = b["type"]
    if t == "paragraph":
        return f"<p>{_esc(b['text'])}</p>"
    if t == "note":
        return f"<div class='note'>{_esc(b['text'])}</div>"
    if t == "kv":
        rows = "".join(
            f"<tr><th>{_esc(k)}</th><td>{_kv_value_html(v)}</td></tr>"
            for k, v in b["items"].items())
        return f"<div class='table-wrap'><table><tbody>{rows}</tbody></table></div>"
    if t == "table":
        head = "".join(f"<th>{_esc(c)}</th>" for c in b["columns"])
        body = "".join(
            "<tr>" + "".join(f"<td>{_esc(c)}</td>" for c in r) + "</tr>"
            for r in b["rows"])
        return ("<div class='table-wrap'><table><thead><tr>" + head
                + "</tr></thead><tbody>" + body + "</tbody></table></div>")
    if t == "list":
        items = "".join(f"<li>{_esc(x)}</li>" for x in b["items"])
        return f"<ul>{items}</ul>"
    items = "".join(f"<li>{_esc(x)}</li>" for x in b["items"])
    return f"<div class='provenance'><strong>Provenance &amp; limitations</strong><ul>{items}</ul></div>"


def render_glow_report(title: str, sections: list[dict], *,
                       generated_utc: str | None = None,
                       footer: str | None = None,
                       banner: str | None = None) -> str:
    """Render a complete standalone styled HTML document. Escapes all data."""
    if not isinstance(title, str) or not title.strip():
        raise ValueError("title must be non-empty")
    _check_sections(sections)
    if generated_utc is not None and not isinstance(generated_utc, str):
        raise TypeError("generated_utc must be a str")
    generated = generated_utc or _utc_now()
    body = []
    if banner is not None:
        if not isinstance(banner, str) or not banner.strip():
            raise ValueError("banner must be a non-empty string when given")
        body.append(f"<div class='banner'>{_esc(banner)}</div>")
    body += ["<header class='band'>",
            f"<h1>{_esc(title)}</h1>",
            f"<p class='meta'>Generated {html.escape(generated)} by sugarcode-ai glow renderer</p>",
            "</header>", "<main>"]
    for s in sections:
        body.append("<section class='card'>")
        body.append(f"<h2>{_esc(s['heading'])}</h2>")
        body.extend(_block_html(b) for b in s["blocks"])
        body.append("</section>")
    body.append("</main>")
    if footer:
        body.append(f"<footer class='meta'>{_esc(footer)}</footer>")
    return ("<!DOCTYPE html>\n<html lang='en'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{_esc(title)}</title><style>{_CSS}</style></head><body>"
            + "\n".join(body) + "</body></html>\n")
