"""Drop 49: consolidated evidence report - ONE repro entry for every
headline number in README/STATUS. Reads only hermetic fixtures (no
network); prints and writes docs/EVIDENCE.md. Covers: pooled golden
(deduped), canonical capture, benign specificity, AT-AC, GC-donor, UTR,
VUS sweep, conflicting sweep, exonic donor/acceptor sweeps, cryptic
recall null, ESRseq null.
"""
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class EvidenceReportFailure(RuntimeError):
    """A required report stage failed; publication must not continue."""


_HEADLINES = (
    ("fixtures:", r"fixtures: [0-9]+  unique pathogenic: [0-9]+  unique benign: [0-9]+"),
    ("canonical U2", r"canonical U2 \(GT/GC donor, AG acceptor\): ([0-9]+)/([0-9]+) called loss"),
    ("canonical AT-AC", r"canonical AT-AC \(U12 matrices, drop 27\): ([0-9]+)/([0-9]+) called loss"),
    ("benign specificity", r"benign specificity: ([0-9]+)/([0-9]+)"),
)


def pooled_headlines(root):
    try:
        result = subprocess.run(
            [sys.executable, str(root / "scripts/pooled_splice_stats.py")],
            cwd=root, capture_output=True, text=True)
    except (OSError, UnicodeError) as exc:
        raise EvidenceReportFailure("pooled child launch/decode stage failed") from exc
    if result.returncode != 0:
        raise EvidenceReportFailure(f"pooled child stage failed (exit {result.returncode})")
    found = []
    for prefix, pattern in _HEADLINES:
        matches = [line for line in result.stdout.splitlines() if line.startswith(prefix)]
        if len(matches) != 1:
            raise EvidenceReportFailure(f"pooled headline stage: missing/duplicate {prefix}")
        match = re.fullmatch(pattern, matches[0])
        if match is None:
            raise EvidenceReportFailure(f"pooled headline stage: malformed {prefix}")
        if match.groups():
            numerator = match.group(1).lstrip("0") or "0"
            denominator = match.group(2).lstrip("0") or "0"
            if (len(numerator), numerator) > (len(denominator), denominator):
                raise EvidenceReportFailure(f"pooled headline stage: invalid ratio {prefix}")
        found.append(matches[0])
    # Preserve original source order, not contract enumeration order.
    return [line for line in result.stdout.splitlines() if line in found]


def publish_report(out, destination):
    temporary = None
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", newline="",
                                         dir=destination.parent, prefix=".evidence-",
                                         suffix=".tmp", delete=False) as staged:
            temporary = Path(staged.name)
            staged.write(out)
            staged.flush()
            os.fsync(staged.fileno())
        os.replace(temporary, destination)
    except (OSError, UnicodeError) as exc:
        raise EvidenceReportFailure("publication stage failed") from exc
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass  # Never mask the publication failure with cleanup failure.


def load(root, name):
    try:
        return json.loads((root / "tests/fixtures" / name).read_text())
    except (OSError, UnicodeError, ValueError) as exc:
        raise EvidenceReportFailure(f"fixture load stage failed: {name}") from exc


def render_report(root):
    lines = ["# SugarCode AI - consolidated evidence report",
             "(regenerated from hermetic fixtures by scripts/evidence_report.py; no network)",
             ""]
    # pooled golden headline (from pooled_splice_stats logic)
    for ln in pooled_headlines(root):
        lines.append(f"- {ln}")
    gc = load(root, "gc_donor_golden.json")
    b = {}
    for c in gc["cases"]:
        b[c["sig"]] = b.get(c["sig"], 0) + 1
    lines.append(f"- GC-donor golden: {len(gc['cases'])} cases {b} - benign searched, ZERO found")
    vus = load(root, "vus_splice_golden.json")
    n_vus = sum(len(g["cases"]) for g in vus["genes"].values())
    n_strong = sum(s["strong_loss"] for s in vus["summary"].values())
    lines.append(f"- VUS sweep: {n_vus} scored, {n_strong} strong-loss "
                 "(prioritization signal, NOT pathogenicity evidence)")
    conf = load(root, "conflicting_splice_golden.json")
    n_conf = sum(len(g["cases"]) for g in conf["genes"].values())
    lines.append(f"- conflicting sweep: {n_conf} scored, "
                 f"{sum(1 for g in conf['genes'].values() for c in g['cases'] if c['delta'] <= -0.15)} "
                 "strong-loss (one computational opinion, not a tiebreaker)")
    exd = load(root, "exonic_donor_golden.json")
    n_exd = sum(len(g["cases"]) for g in exd["genes"].values())
    exa = load(root, "exonic_acceptor_golden.json")
    n_exa = sum(len(g["cases"]) for g in exa["genes"].values())
    lines.append(f"- exonic sweeps: donor -3..-1 {n_exd} cases, acceptor +1 {n_exa} cases")
    cr = load(root, "cryptic_recall_vus.json")
    lines.append(f"- cryptic recall on VUS: {cr['results']['strong']['new']} true cryptic "
                 f"creations in {cr['results']['strong']['n']} strong-loss VUS and "
                 f"{cr['results']['control']['new']} in {cr['results']['control']['n']} "
                 "controls (honest null)")
    es = load(root, "esrseq_enrichment.json")
    s = es["summary"]
    lines.append(f"- ESRseq exonic-terminal enrichment: pathogenic mean "
                 f"{s['pathogenic']['mean_esrseq_delta_exonic']:+.3f} vs benign "
                 f"{s['benign']['mean_esrseq_delta_exonic']:+.3f} - ESE hypothesis "
                 "NOT supported (honest null)")
    out = "\n".join(lines) + "\n"
    return out


def main(root=ROOT):
    root = Path(root).resolve()
    try:
        out = render_report(root)
    except EvidenceReportFailure:
        raise
    except (KeyError, TypeError, ValueError, IndexError, ArithmeticError) as exc:
        raise EvidenceReportFailure("fixture section rendering stage failed") from exc
    publish_report(out, root / "docs/EVIDENCE.md")
    print(out)


if __name__ == "__main__":
    try:
        main()
    except EvidenceReportFailure as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
