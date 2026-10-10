# P05 one literal normalized_score unknown-base finding (authored NOT RUN; contract-repair commit)

Parent exactly 7c02ffbe39f2abfa04e76b38a338fe0b34d47a55 (H43 landed; tree 67daa80509b1a8fe922937bd8e3eccb2eb3b2e42; parent bd5f089b98f7690239d4b0e2a07444ab7e813fd0).
Test+contract only; ONE test with ONE assertion:
normalized_score('N', [{'A':1.0,'C':0.0,'G':0.0,'T':0.0}]) == -10.0.
Expected value derived from source, NOT observed: pwm.py line 35 gives an unknown base the score -10.0; lines 48-51 compute lo=0.0, hi=1.0, so (-10.0 - 0.0) / (1.0 - 0.0) = -10.0 exactly. This lies outside the docstring's "0..1" (line 47) for this ONE synthetic matrix only. Finding only. No calibrated binding, policy, source-fix, biological, clinical, standard, general-bound, caller or CLI claim. Authority: peer P05 narrowed GROUP6-only grant relayed by Main (9:37:57 PM IST), not independently authenticated by me. No source or old-test edit.

## Dropped by the peer ruling (not authored)
Equal-length/empty build_pwm; second edge; separate unknown-base score path; log-odds floor; degenerate-matrix branch; scan edges.

## Network receipt (public HTTPS clone/fetch only; no push, no credentials, no pip)
Existing clone /tmp/sc3 (made 21:12:20). `git fetch origin` at 21:34:20 (bd5f089), 21:38:01 (to 7c02ffbe, matches the peer short hash after H43), and 21:38:23 (origin/main = HEAD = 7c02ffbe39f2abfa04e76b38a338fe0b34d47a55). The repair commit made no network call. `git remote -v` names: origin only.

## Gate reads at exact tip (2026-10-10 IST, visible, full files; wc -l lines / blob)
Read 21:38:05-21:38:18: src/sugarcode/bio/pwm.py 1-63 (63 / fc5fb45063b2f3019cb9dd184c195e2a6e3a749a); src/sugarcode/bio/motif.py 1-198 (198 / 34b8d56bfec47d1faedf76feac897e894e252c2c; 1-75 read 21:38:10, 76-198 read 21:38:05); tests/test_bio_utils.py 60 / 4708c7d6a61495dc35f4a362cee458de4b3a5c56; tests/test_bio_motif.py 87 / 6c5981f4bacb29315a06bae3368bbd3d3a59f4aa; tests/test_cli_motif.py 34 / cdbad9d353d752e89e7b644bee4c738581551aff; tests/test_drop28.py 56 / 3a923206fb790412bae6c1447d5bbff5c71cb90f; tests/test_drop44.py 80 / ab9a623894a1cfb2f06cc2caaa8265a18e50fc1f; tests/test_drop60.py 109 / 64d45ef3806528fae63d3a6938082ab6aa3a6f94; src/sugarcode/cli.py 196-210 only (handler _cmd_pwm_score; file 1672 lines / 6deca9be51c878920eae0afd66786a071f61dfbf; NO full-CLI claim).
Contracts read in full (lines / blob): H34 38 / 29275090d994b386ef0ed9c9fdc05955534ef365; H35 35 / a7dea3e49f8a158d99b03b2e165eff666d361e03; H36 32 / 7c783dca286ce67bacbd4f52fcdbf0a6888ef7c5; H37 32 / 5628d596b7789ba3cd27282283d8cb26f30ca596; H38 33 / 0f2275e9dc208f9e8fb04dd6aab2d0ff39f3d796; H39 30 / 350d38d7c353de387ebef4d8578cb4c534e56fc4; H40 29 / 5612f573ad953ff6461ce994e97c101d5c66b3ce; H41 36 / 22d5f6c9c8f94faffa51a0a85c2b9878813bd571; H42 32 / 030e498486bd4d9aa630418ab52b0a5549a49c96; H43 30 / 2cfe7fe68fb3f876d1147ce792c329acbb21acce; P02 49 / 85ea735893bcd84d8726d16cd8673ef536b5995a; P03R 38 / 3a9c53b744a85d0d768427f70ece1a7997ab0b79; P04 54 / 91e79d722338eed81ee7cb719140bdb4e6d86006.
NOT read: dark_genome/core.py (import line only by grep, no gate), splice.py/deepsplice (no reread required; old reads not upgraded), other cli.py regions.
Author-time visible re-anchor at 21:38:23 (a separate step from the test write): pwm.py 31-52 (score 31-35, max/min_score 38-43, normalized_score 46-51), blob unchanged.

## Collision check
No existing test or contract found calling normalized_score with a non-ACGT base or pinning an out-of-0..1 value. test_drop28/44 only import normalized_score; test_drop60 CLI tests use ACGT windows and assert 0..1 for CAGGTAAGT; motif tests use score_site/scan with ACGT. The CLI handler (196-210) upper-cases input and calls normalized_score for exact-window input; no CLI claim is made.

## Chronology (corrected)
Tip verified 21:38:01 and 21:38:23. Reads 21:38:05-18. Branch p05 and tip re-anchor 21:38:23. Test file written at 21:38:30 (clock receipts 21:38:30 immediately before and after the write; quoted-heredoc cat, no Python or text-replace). Contract (original commit) written after the test, 21:38:30-21:38:51. Documentary chronology, not proof of comprehension.

## Repair note (contract-only; request relayed by Main 9:39:44 PM IST, not independently authenticated by me)
Superseded candidate f96618163e49c129b3cfeb4a93f7a825581bc24c (single commit on 7c02ffbe) stated that the test was written "21:38:23-24". That was wrong: 21:38:23 was the tip re-anchor and the test write was 21:38:30. This commit is a NEW single commit on the same parent 7c02ffbe39f2abfa04e76b38a338fe0b34d47a55, not stacked on f9661816 and with no history rewrite. The test file bytes are IDENTICAL to f9661816: blob bc565d4368f262e671b30628e394494317ca3609 (checked with git rev-parse on both commits; see manifest). The patch, bundle, manifest and their sha256 for this commit are in the delivered manifest and transport message, not self-referenced here. Repair edits were made by a quoted-heredoc rewrite of this file (no sed or Python); the test file was taken with `git checkout f9661816 -- <test file>`.

## RUN vs NOT RUN
RUN: public same-HTTPS clone/fetch (earlier steps only), git object ops, sed/cat reads, date, sha256sum/stat, patch/bundle creation. NOT RUN: pytest, SugarCode import, py_compile or any syntax check, pip, other network. No PASS or landing claim. Independent audit owns runtime.
