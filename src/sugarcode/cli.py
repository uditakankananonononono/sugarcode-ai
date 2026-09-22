"""SugarCode AI command-line interface (drop 57).

`sugarcode splice assess GENE NOTATION [--transcript NM_...]` runs the
deepsplice live assessment and prints JSON. `--offline` forces the
record-cache only (no network). Exit codes: 0 assessment produced (any
status), 2 usage error.
"""
from __future__ import annotations
import argparse
import json
import sys

from . import __version__
from .modules.deepsplice import live_splice_assessment


def _cmd_splice_assess(args) -> int:
    r = live_splice_assessment(args.gene, args.notation,
                               offline=args.offline,
                               transcript=args.transcript)
    json.dump(r, sys.stdout, indent=1)
    sys.stdout.write("\n")
    return 0


def _cmd_version(_args) -> int:
    print(f"sugarcode-ai {__version__}")
    return 0


def _cmd_modules(_args) -> int:
    from importlib import import_module
    from . import modules
    names = sorted(m.name for m in __import__("pkgutil").iter_modules(modules.__path__))
    print(f"{len(names)} modules")
    for n in names:
        print(n)
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="sugarcode",
                                description="SugarCode AI - multi-omic bio-design platform")
    sub = p.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("splice", help="deepsplice splice assessment")
    ssub = sp.add_subparsers(dest="sub", required=True)
    a = ssub.add_parser("assess", help="assess one ClinVar-style notation")
    a.add_argument("gene")
    a.add_argument("notation")
    a.add_argument("--transcript", default=None,
                   help="NM_ accession for an explicit transcript map")
    a.add_argument("--offline", action="store_true",
                   help="use the record cache only (no network)")
    a.set_defaults(func=_cmd_splice_assess)
    v = sub.add_parser("version", help="print version")
    v.set_defaults(func=_cmd_version)
    m = sub.add_parser("modules", help="list the 77 modules")
    m.set_defaults(func=_cmd_modules)
    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
