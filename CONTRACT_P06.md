# P06 literal-star-returns-snp characterization (authored NOT RUN)

Parent exactly 2619d32b82f84588c8870c9940d319c8fc269973 (H45; tree
4b37bc2d17279d20387df6f6d050f445f4a07b27; parent fa0f83fbb1993b1404236e59ff3dd43b38e3f2ee).
Test+contract only. ONE test, ONE assertion:
variant_type("A", "*") == "snp". Expected value derived by reading
src/sugarcode/bio/vcf.py 157-169, NOT observed: "*" does not start with "<" or
end with ">", contains no "[" or "]", and len("A") == len("*") == 1, so line 164
returns "snp". This records the label the current implementation returns for
this one synthetic input. It is not a statement about correct handling of the
"*" allele. No conformance, defect, fix, policy, spec interpretation, clinical,
biological, statistics, filter, CLI or report claim. No external spec consulted.
Authority: peer P06 narrow grant relayed by Main (9:49:09 PM IST), not
independently authenticated by me. No source or old-test edit.

## Test file
tests/test_p06_vcf_literal_star_returns_snp_characterization.py, one function
test_variant_type_literal_star_alt_returns_snp_label; blob 89042af2c3ff587ddcb4679dabf96f5b9364afa4.
Written by quoted-heredoc cat; no Python, sed or text-replace script.

## Network receipt (public same-HTTPS repo only; fetch only; no push, no credentials)
Existing clone /tmp/sc. git fetch origin at 21:45:46 (6e1a421..fa0f83f),
21:47:36 (fa0f83f..2619d32), 21:49:19 and 21:49:50 (no change; origin/main and
HEAD both 2619d32b82f84588c8870c9940d319c8fc269973 at 21:49:50). git remote -v
before and after: origin https://github.com/uditakankananonononono/sugarcode-ai.git
(fetch) and (push), no other remote. Earlier in the same clone, for other units,
a clone about 09:42 IST and fetches about 09:44 and 12:27 IST.

## Gate reads at exact tip (2026-10-10 IST, visible, complete, no truncation)
Read 21:49:25: src/sugarcode/bio/vcf.py 1-263 (wc -l 263; blob
d700eae96b74461bf2222183a8e2e2fa6554977c).
Read 21:49:25: tests/test_bio_vcf.py 1-100 (100; 1fadc282d988e46ac92795965c5cad7efdf7a587);
tests/test_cli_vcf.py 1-42 (42; b731fba5485203d61438f90c66d05104107c2f4f);
tests/test_vcf_pct3a.py 1-6 (6; b97d176fba7da6852b57ef5ac32021ca6c65f2e2).
Peer expected 3 lines for the percent-VCF file; ACTUAL: path
tests/test_vcf_pct3a.py, wc -l 6, grep -c '' 6, 222 bytes, 6 content lines
(import, two blank lines, def, two asserts). Not reconciled; reported as found.
Author-time re-anchor, visible, at 21:49:50 before the test write at 21:49:56:
vcf.py 157-169, src/sugarcode/cli.py 352-385 and 1566-1590 only (file 1672
lines, blob 6deca9be51c878920eae0afd66786a071f61dfbf; NO full-CLI claim).
Contracts read in full, complete (long lines wrapped, none cut): H34 38 /
29275090d994b386ef0ed9c9fdc05955534ef365; H35 35 / a7dea3e49f8a158d99b03b2e165eff666d361e03;
H36 32 / 7c783dca286ce67bacbd4f52fcdbf0a6888ef7c5; H37 32 / 5628d596b7789ba3cd27282283d8cb26f30ca596;
H38 33 / 0f2275e9dc208f9e8fb04dd6aab2d0ff39f3d796; H39 30 / 350d38d7c353de387ebef4d8578cb4c534e56fc4;
H40 29 / 5612f573ad953ff6461ce994e97c101d5c66b3ce; H41 36 / 22d5f6c9c8f94faffa51a0a85c2b9878813bd571;
H42 32 / 030e498486bd4d9aa630418ab52b0a5549a49c96; H43 30 / 2cfe7fe68fb3f876d1147ce792c329acbb21acce;
H44 30 / e5c13b133a30974c004523030ca28841ac98acb7; P02 49 / 85ea735893bcd84d8726d16cd8673ef536b5995a;
P03R 38 / 3a9c53b744a85d0d768427f70ece1a7997ab0b79 (7 lines over 300 chars, re-read wrapped at 150);
P04 54 / 91e79d722338eed81ee7cb719140bdb4e6d86006; P05 30 / 5bc34af6f19cc4a7c0342a7f550656120d5115e1
(6 lines over 300 chars, re-read wrapped at 150).
H45 (57 / 6c5cd162dfd42e79c81f1f8e1f2a5389352fd4c7): read in full uncut at
21:47:36 (visible); not re-read, per the peer's supplement accepting that read.
H45 test body NOT read. NOT read: rest of cli.py, report.to_csv, other bio modules,
src/sugarcode/modules/openclinvar/core.py parse_vcf_line and neohunter (grep only).

## Collision check
No test or contract found calling variant_type with a "*" allele. test_bio_vcf.py
variant_type cases use G, GC, ATT, A, <DEL>, G[chr2:100[; MINI has no "*" ALT.
test_cli_vcf.py and test_vcf_pct3a.py use no "*" alleles. A full-text grep of
CONTRACT_*.md for vcf and variant_type finds no mention in H34-H45, P02-P05.
Only src/sugarcode/cli.py imports bio.vcf. Existing label-specific tests are
adjacent but not duplicated.

## RUN vs NOT RUN
RUN: public same-HTTPS fetch, git object ops, sed/cat/awk/grep reads, date,
git hash-object, sha256sum, patch and bundle creation. NOT RUN: pytest, import of
SugarCode, py_compile or any syntax check, pip, other network. No PASS or landing
claim. Independent audit owns runtime. The patch, bundle and manifest with their
sha256 are delivered separately, not self-referenced here.
