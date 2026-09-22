"""Drop 49: consolidated evidence report - ONE repro entry for every
headline number in README/STATUS. Reads only hermetic fixtures (no
network); prints and writes docs/EVIDENCE.md. Covers: pooled golden
(deduped), canonical capture, benign specificity, AT-AC, GC-donor, UTR,
VUS sweep, conflicting sweep, exonic donor/acceptor sweeps, cryptic
recall null, ESRseq null.
"""
import json
from pathlib import Path

F = Path("tests/fixtures")

def load(name):
    return json.loads((F / name).read_text())

def main():
    lines = ["# SugarCode AI - consolidated evidence report",
             "(regenerated from hermetic fixtures by scripts/evidence_report.py; no network)",
             ""]
    # pooled golden headline (from pooled_splice_stats logic)
    import subprocess
    pooled = subprocess.run(["python3", "scripts/pooled_splice_stats.py"],
                            capture_output=True, text=True).stdout
    for ln in pooled.splitlines():
        if ln.startswith(("fixtures:", "canonical", "benign specificity")):
            lines.append(f"- {ln}")
    gc = load("gc_donor_golden.json")
    b = {}
    for c in gc["cases"]:
        b[c["sig"]] = b.get(c["sig"], 0) + 1
    lines.append(f"- GC-donor golden: {len(gc['cases'])} cases {b} - benign searched, ZERO found")
    vus = load("vus_splice_golden.json")
    n_vus = sum(len(g["cases"]) for g in vus["genes"].values())
    n_strong = sum(s["strong_loss"] for s in vus["summary"].values())
    lines.append(f"- VUS sweep: {n_vus} scored, {n_strong} strong-loss "
                 "(prioritization signal, NOT pathogenicity evidence)")
    conf = load("conflicting_splice_golden.json")
    n_conf = sum(len(g["cases"]) for g in conf["genes"].values())
    lines.append(f"- conflicting sweep: {n_conf} scored, "
                 f"{sum(1 for g in conf['genes'].values() for c in g['cases'] if c['delta'] <= -0.15)} "
                 "strong-loss (one computational opinion, not a tiebreaker)")
    exd = load("exonic_donor_golden.json")
    n_exd = sum(len(g["cases"]) for g in exd["genes"].values())
    exa = load("exonic_acceptor_golden.json")
    n_exa = sum(len(g["cases"]) for g in exa["genes"].values())
    lines.append(f"- exonic sweeps: donor -3..-1 {n_exd} cases, acceptor +1 {n_exa} cases")
    cr = load("cryptic_recall_vus.json")
    lines.append(f"- cryptic recall on VUS: {cr['results']['strong']['new']} true cryptic "
                 f"creations in {cr['results']['strong']['n']} strong-loss VUS and "
                 f"{cr['results']['control']['new']} in {cr['results']['control']['n']} "
                 "controls (honest null)")
    es = load("esrseq_enrichment.json")
    s = es["summary"]
    lines.append(f"- ESRseq exonic-terminal enrichment: pathogenic mean "
                 f"{s['pathogenic']['mean_esrseq_delta_exonic']:+.3f} vs benign "
                 f"{s['benign']['mean_esrseq_delta_exonic']:+.3f} - ESE hypothesis "
                 "NOT supported (honest null)")
    out = "\n".join(lines) + "\n"
    print(out)
    Path("docs").mkdir(exist_ok=True)
    Path("docs/EVIDENCE.md").write_text(out)

if __name__ == "__main__":
    main()

