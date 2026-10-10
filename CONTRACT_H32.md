# CONTRACT_H32 - report/exporters.py validation and edge rendering (characterization; authored, NOT RUN; tests + contract only)
Parent: fb9e276a74860098bdcc78001d63bde8bddd2757 (tree 64358fa1499c32e334553b9425ddf82d9d57b7cf). Authority: peer grant (narrowed) relayed by Main (6:22:27 PM IST), not independently authenticated by me. No product edit, no old-test edit.

## Chronology (10 Oct 2026 IST, self-reported, test first)
- Gate reads at fb9e276a finished 18:22:31-18:22:32, before anything was authored: exporters.py 1-104, tests/test_report_exporters.py 1-58, tests/test_report_bundle_manifest_reservation.py 1-50 (entire file). An earlier hunt report (about 18:20) had read the reservation file with a head -60, which also covered all 50 lines; I worded it as "first 50", which the peer found insufficient as a gate, so the gate reads were repeated here.
- Tests authored 18:22:38-18:22:42; this contract after. No source step.

## What the tests pin (findings only; derived by reading, not observed)
1. to_csv("x") and to_csv([1]) raise TypeError (exporters.py 31-32).
2. Explicit columns [], ["a", ""], ["a", 1] raise ValueError "columns must be a non-empty list of names" (18-20).
3. Explicit column order is kept: to_csv([{"b":1,"a":2}], ["b","a"]) gives "b,a\n1,2\n" (lineterminator "\n", line 36).
4. 0, False and "" render literally: to_csv([{"a":0,"b":False,"c":""}], ["a","b","c"]) gives "a,b,c\n0,False,\n". UNGROUNDED stdlib prediction (False as text, empty field); the None conversion at line 40 is not asserted here (covered by test_csv_quoting_and_none).
5. A row missing a listed column renders an empty field: to_csv([{"a":1}], ["a","b"]) gives "a,b\n1,\n". UNGROUNDED stdlib prediction (DictWriter default restval), not code in this module.
6. make_bundle rejects name "", "  " and 5 (ValueError, line 56); filenames "a\\b", "dir/x", "", ".", ".." and 5 (ValueError, line 62).
7. make_bundle("n", {"a.txt": "\u00e9"}): bytes == 2, sha256 == hashlib.sha256("\u00e9".encode()).hexdigest(), metadata == {}, generator == "sugarcode-ai report engine". The created_utc fixture is "t" and is NOT asserted (already in test_bundle_checksums_real).
Not pinned: None rendering, MANIFEST.json reservation, write_bundle, tsv. If the peer's run shows a different stdlib rendering for 4 or 5, the actual must be pinned by an explicit later correction; nothing here is claimed as verified.

## Read receipt at fb9e276a (verbatim, in full, timestamps IST)
18:22:31-32: src/sugarcode/report/exporters.py 1-104 (541e2ddf3f196692f689b2fa4bbeb1895a8946f7); tests/test_report_exporters.py 1-58 (f8c3cb2746c955f00f5412a8d4576c666ddac92d); tests/test_report_bundle_manifest_reservation.py 1-50 (a3090230e6b07228394a5794ef58d3963135549a). Earlier, partial: report_studio/core.py 150-182 (delegation only); other report tests grep-only.
## RUN vs NOT RUN
RUN: git object ops, sed/cat reads, sha256sum. NOT RUN: pytest, import, py_compile or any syntax check, pip, network.
