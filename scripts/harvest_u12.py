"""Harvest human U12 (minor spliceosome) splice-site PWMs from the published
Larue & Roy (2023, NAR gkad797) intronIC training index on FigShare
(DOI 10.6084/m9.figshare.20483655, GPL-3.0+; splice-site sequences are the
facts vendored - provenance in data/splice_sites/PROVENANCE.md).

Writes data/splice_sites/u12_atac_donor_pwm.json, u12_atac_acceptor_pwm.json,
u12_gtag_donor_pwm.json, u12_gtag_acceptor_pwm.json.
Acceptor matrices: 14 INTRONIC positions learned from data + one uniform
column at index 14 (first exonic base not in the export - labeled, not
guessed).
"""
from __future__ import annotations
import gzip, io, json, sys, urllib.request
from collections import Counter
from pathlib import Path

sys.path.insert(0, "src")
from sugarcode.bio.pwm import build_pwm

URL = ("https://raw.githubusercontent.com/glarue/intronIC/main/"
       "training_index/training_data_index.tsv.gz")
OUT = Path("src/sugarcode/bio/data/splice_sites")


def pwm_payload(sites: list[str], ncols: int) -> dict:
    pwm = build_pwm(sites)
    if len(pwm) == ncols - 1:   # acceptor: append uniform exonic column
        pwm = pwm + [{b: 0.25 for b in "ACGT"}]
    assert len(pwm) == ncols
    return {"pwm": pwm, "n_sites": len(sites)}


def main():
    data = urllib.request.urlopen(URL, timeout=60).read()
    txt = gzip.open(io.BytesIO(data), "rt")
    hdr = txt.readline().rstrip("\n").split("\t")
    donors = {"ATAC": [], "GTAG": []}
    acceptors = {"ATAC": [], "GTAG": []}
    for line in txt:
        r = dict(zip(hdr, line.rstrip("\n").split("\t")))
        if r["species_full"] != "homo_sapiens" or r["label"] != "u12":
            continue
        up, seq = r["up_flank"], r["intron_seq_trunc"].replace("...", "")
        five = up[-3:] + seq[:6]
        three = seq[-14:]
        if len(five) != 9 or len(three) != 14 or "N" in five + three:
            continue
        key = ("ATAC" if (seq[:2], seq[-2:]) == ("AT", "AC")
               else "GTAG" if (seq[:2], seq[-2:]) == ("GT", "AG") else None)
        if not key:
            continue
        donors[key].append(five)
        acceptors[key].append(three)
    for key, stem in (("ATAC", "u12_atac"), ("GTAG", "u12_gtag")):
        json.dump(pwm_payload(donors[key], 9),
                  open(OUT / f"{stem}_donor_pwm.json", "w"), indent=1)
        json.dump(pwm_payload(acceptors[key], 15),
                  open(OUT / f"{stem}_acceptor_pwm.json", "w"), indent=1)
        print(key, "donors:", len(donors[key]), "acceptors:", len(acceptors[key]))
    return donors, acceptors


if __name__ == "__main__":
    main()
