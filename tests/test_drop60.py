"""Drop 60: packaging pass 3 - module-level CLI subcommands.

All new subcommands (codon cai/optimize, fasta stats, genbank features,
pwm score) run offline against shipped published data. Tests invoke
sugarcode.cli.main with argv and parse the JSON from capsys.
"""
import json

import pytest

from sugarcode.cli import main


def _run(argv, capsys):
    rc = main(argv)
    assert rc == 0
    return json.loads(capsys.readouterr().out)


def test_codon_cai_perfect_e_coli_sequence(capsys):
    # ATG GCG GCG AAA: top E. coli codons -> CAI 1.0
    out = _run(["codon", "cai", "ATGGCGGCGAAA"], capsys)
    assert out["species"] == "e_coli_316407"
    assert out["length"] == 12
    assert out["cai"] == 1.0


def test_codon_optimize_roundtrip_and_gc(capsys):
    out = _run(["codon", "optimize", "MAAKRF", "--gc-min", "0.4",
                "--gc-max", "0.6"], capsys)
    dna = out["dna"]
    assert len(dna) == 18
    assert out["cai"] > 0.9
    assert 0.3 <= out["gc"] <= 0.7
    # translate back: must encode the same protein
    from sugarcode.bio.codon import synonymous_codons
    table = {}
    for aa in "ACDEFGHIKLMNPQRSTVWY":
        for c in synonymous_codons(aa):
            table[c] = aa
    assert "".join(table[dna[i:i + 3]] for i in range(0, 18, 3)) == "MAAKRF"


def test_codon_optimize_avoid_motif(capsys):
    out = _run(["codon", "optimize", "KKKKKK", "--avoid", "AAAAAA"], capsys)
    assert "AAAAAA" not in out["dna"]


def test_fasta_stats(tmp_path, capsys):
    f = tmp_path / "t.fa"
    f.write_text(">one desc\nACGTACGT\n>two\nGGGG\n")
    out = _run(["fasta", "stats", str(f)], capsys)
    assert out["records"] == 2
    assert out["total_length"] == 12
    assert out["entries"][0]["id"] == "one"
    assert out["entries"][0]["gc"] == 0.5
    assert out["entries"][1]["gc"] == 1.0


def test_genbank_features(tmp_path, capsys):
    gb = tmp_path / "t.gb"
    gb.write_text(
        "LOCUS       T1   12 bp\n"
        "FEATURES             Location/Qualifiers\n"
        "     source          1..12\n"
        "     CDS             complement(1..9)\n"
        "                     /gene=\"x\"\n"
        "ORIGIN\n"
        "        1 acgtacgtac gt\n"
        "//\n")
    out = _run(["genbank", "features", str(gb)], capsys)
    assert out["sequence_length"] == 12
    assert out["feature_counts"] == {"CDS": 1, "source": 1}
    cds = [f for f in out["features"] if f["key"] == "CDS"][0]
    assert cds["strand"] == -1
    assert cds["spans"] == [[1, 9]]


def test_pwm_score_donor_exact_window(capsys):
    out = _run(["pwm", "score", "CAGGTAAGT", "--motif", "donor"], capsys)
    assert out["window"] == 9
    assert out["normalized_score"] is not None
    assert 0.0 <= out["normalized_score"] <= 1.0


def test_pwm_score_scan_longer_sequence(capsys):
    out = _run(["pwm", "score", "TTTTTCAGGTAAGTTTT", "--motif", "donor"],
               capsys)
    assert out["normalized_score"] is None  # not exact-window length
    assert out["hits"]
    # canonical GT donor embedded at offset 5 must be a hit
    positions = [h["position"] for h in out["hits"]]
    assert 5 in positions


def test_pwm_motif_choices_offline(capsys):
    # every shipped motif matrix scores an exact-window dummy sequence
    from sugarcode.cli import _motif_lods
    for name, fn in _motif_lods().items():
        n = len(fn())
        out = _run(["pwm", "score", "A" * n, "--motif", name], capsys)
        assert out["normalized_score"] is not None, name


def test_version_and_modules_unchanged(capsys):
    assert main(["version"]) == 0
    assert "0.2.0" in capsys.readouterr().out
    assert main(["modules"]) == 0
    assert "77 modules" in capsys.readouterr().out
