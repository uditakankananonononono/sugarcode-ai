"""Regenerate data/periodic_table.json from RDKit's atomic_data.cpp (pinned).

Not imported at runtime. Usage:
    curl -sL -o atomic_data.cpp https://raw.githubusercontent.com/rdkit/rdkit/Release_2024_09_6/Code/GraphMol/atomic_data.cpp
    python vendor_atomic_data.py atomic_data.cpp > data/periodic_table.json
"""
import hashlib
import json
import re
import sys

PIN = {"repository": "https://github.com/rdkit/rdkit", "tag": "Release_2024_09_6",
       "commit": "b3076c77284b9a8b9d5ef78957ee067037f373a8",
       "path": "Code/GraphMol/atomic_data.cpp", "license": "BSD-3-Clause"}


def main(path):
    raw = open(path, "rb").read()
    text = raw.decode()
    elem_block = text[text.index("const std::string periodicTableAtomData ="):text.index("atomicData::atomicData")]
    rows = "".join(re.findall(r'R"DAT\((.*?)\)DAT"', elem_block, re.S))
    elements = {}
    for line in rows.splitlines():
        f = line.split()
        if len(f) < 11 or f[1] == "*":
            continue
        z, sym = int(f[0]), f[1]
        elements[sym] = {"Z": z, "average_mass": float(f[6]), "common_isotope": int(f[8]),
                         "common_isotope_mass": float(f[9]),
                         "valences": [int(v) for v in f[10:]]}
    iso_block = text[text.index("const std::string isotopesAtomData[]"):]
    iso_rows = "".join(re.findall(r'R"DAT\((.*?)\)DAT"', iso_block, re.S)).replace("\\n \\", "\n").replace("\\n", "\n")
    isotopes = {}
    for line in iso_rows.splitlines():
        f = line.split()
        if len(f) >= 4 and f[0].isdigit():
            isotopes.setdefault(f[1], {})[f[2]] = float(f[3])
    em = float(re.search(r"electronMass\s*=\s*([0-9.eE+-]+)", text).group(1))
    out = {"source": {**PIN, "sha256": hashlib.sha256(raw).hexdigest()},
           "electron_mass": em, "elements": elements, "isotopes": isotopes}
    json.dump(out, sys.stdout, indent=1, sort_keys=True)


if __name__ == "__main__":
    main(sys.argv[1])
