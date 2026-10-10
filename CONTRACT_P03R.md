# CONTRACT_P03R (repair commit: contract-only citation/summary repair of 26de084c) - bio.genbank revcomp and transcript_exons characterization, replacement unit (authored, NOT RUN; tests + contract only)
Parent: cb0048162955dc4af5c83ac7380b73ce888ec797 (tree 369d56f2814a69e48aa16bea28dc07063b806d7d; public repo https://github.com/uditakankananonononono/sugarcode-ai). Fresh single commit on that parent; NOT stacked on the discarded fe074b18. Authority: peer P03 repair ruling and GO relayed by Main (9:18:14 and 9:18:21 PM IST), not independently authenticated by me. No source, product or old-test edit.

## Discarded candidate (deviation receipt, kept)
fe074b1840e2d59d08373d11473a51136f17db04 (parent eb32087f) was discarded as a gate-passing candidate: its gate reads were incomplete at authoring time and it carried an unapproved `is` identity assertion. Later reads did not repair that chronology. This commit replaces it.

## Network receipt (same public HTTPS repo only; clone/fetch only; no push, no pip)
clone 21:12:20-21 (/tmp/sc3); fetch 21:14:54; fetch 21:15:24; fetch 21:18:24 (origin/main moved eb32087 -> cb00481, H41; diff touches only CONTRACT_H41.md and the H41 test); re-fetch 21:19:10 immediately before authoring: origin/main still cb0048162955dc4af5c83ac7380b73ce888ec797. `git remote -v`: origin only.

## Chronology
Tip verified 21:18:24. Fresh gate reads 21:18:30-21:18:48 (below). Tip re-verified 21:19:10. Branch p03r created 21:19:10. Test file written 21:19:11 (finished by 21:19:14). This contract written after the test file. A short python3 text-replace snippet was used only to write the test file from the reviewed bytes (no SugarCode code touched).

## Reuse label
The test file reuses, as an explicit label inside the file says, the reviewed bytes of tests/test_p03_genbank_revcomp_texons_characterization.py from discarded commit fe074b18. Changes: path renamed, `is` assertion removed, +1 test renamed, docstring note. No new history is claimed.

## What the tests pin (findings only; derived by reading, NOT observed)
1. genbank.revcomp is the module-local function (RC = str.maketrans("ACGTN","TGCAN"), genbank.py line 93): revcomp("ACGT") == "ACGT" and "ACGTN" -> "NACGT" are adjacent controls (no new-coverage claim); "AACGT" -> "ACGTT".
2. IUPAC letters are not in the table: revcomp("RYKM") == "MKYR" (reverse only). No claim about any other module's IUPAC handling; no standard/defect judgment.
3. Lowercase passes through: revcomp("acgt") == "tgca"; revcomp("") == "".
4. transcript_exons strand 1: same order, value equality only (no identity or copy claim).
5. transcript_exons strand -1: [(20,28),(1,9)] for [(1,9),(20,28)]; the input spans value is still [(1,9),(20,28)] afterwards (value equality only).
6. Composition finding only: parse_location("complement(join(1..9,20..28))") -> ([(1,9),(20,28)], -1) fed to transcript_exons -> [(20,28),(1,9)]. The join(complement(5..9),complement(1..3)) pin already in test_bio_genbank_real.py is not repeated.

## Fresh read receipt (21:18:30-21:18:48 IST, verbatim sed/cat, no grep-only; line counts from wc -l)
- src/sugarcode/bio/splice.py 110-682 complete (file 682 lines; blob f5ce78851c686cbd810a6442b647d520f7b5c554); 1-109 NOT claimed.
- src/sugarcode/modules/deepsplice/core.py 417-701 complete (file 747 lines; blob 5ec1d86dc0b045741ad359e46084488fa0525221); 1-416 and 702-747 NOT claimed.
- Full files: bio/genbank.py 103 (7aa1afecca5d554b34d1c7ca4c7eb1d4834a76fc); tests/test_bio_genbank_real.py 46 (161d2150fe0bd9566adead42e328ac3c5ed7b357); tests/test_drop60.py 109 (64d45ef3806528fae63d3a6938082ab6aa3a6f94); test_drop25.py 126 (61799a73b4bd50c2796da5280c8da3ac6a9d98fb); test_drop26.py 126 (613e116da828147af401a1ac618f33288ef2b401); test_drop27.py 164 (71de3b077c0cb667e8c5fe9ad5a151df4ed97679); test_drop33.py 70 (df1bd667309261282c20583b4fca8a33a5c4863a); test_drop34.py 52 (c5c11998a8a6d68f3ea9c129f52b4d94adf3e895); test_drop38.py 41 (ff101e508daa5203f9c1f0cd759247be807d877d); test_drop40.py 84 (78dfa4d309eb168d0d34a3b684ee51c97f181e49).
- Call sites (grep, 21:16:51 and consistent with the fresh reads): splice.py import 116, _parse_gb 151/252/372/376/573/577/608, _texons 157/258/292/613, _rc 178-179/335/338/386/589/657-658; core.py local revcomp import 518 with use 523, _rc2 568/576, def 629-631, called only inside _outcome_context (callers 486, 508).

## Dependency impact
No differing test or previously unread behavior found among the files read (summary of consumers is NOT exhaustive). No read test calls genbank.revcomp or transcript_exons directly. Consumers reach them through live/cached-record tests (33/34/38/40) or monkeypatched/stubbed maps and assessments (25/26/27). test_drop27 additionally builds synthetic cDNA-map records and PATCHES the parser (sp._parse_gb) with them, as well as stubbing assessments. For REAL parse_genbank records only, the sequence is uppercased at genbank.py line 86 (`"".join(seq_lines).upper()`), so slices of real-record sequences reach revcomp uppercase; this is no guarantee for patched or synthetic records. The pins do not change any consumer.

## RUN vs NOT RUN
RUN: git clone/fetch of the public repo, git object ops, sed/cat/grep reads, one python3 text-replace to write the test file, sha256sum. NOT RUN: pytest, import of sugarcode, py_compile or any syntax check, pip. Nothing claimed done, tested or working.

## Repair note (contract-only; peer audit relayed by Main 9:23:32 PM IST, not independently authenticated by me)
New candidate identity: this is a NEW single commit on the same audited parent cb0048162955dc4af5c83ac7380b73ce888ec797 (no fetch, no network in this repair; origin parent unchanged by me). Prior candidate 26de084c1d47c3f57df92aaeb57f5b6e1ee2cf1b is superseded by it, not stacked on. Corrections: RC table is genbank.py line 93 (was cited 94); uppercase assignment is line 86 (was cited 99), re-read locally at 21:23:35 (lines 80-100); uppercase statement scoped to REAL parse_genbank records only; test_drop27 summary now names synthetic patched-parser records; consumer summary stated as not exhaustive.
The test file bytes are IDENTICAL to 26de084c: blob 534b7a981dee9ac9d6a74f59274c632fa3ecefbd (checked with git rev-parse on the new commit; see manifest). The patch, bundle, manifest and their sha256 for this commit are in the delivered manifest and transport message, not self-referenced here.
