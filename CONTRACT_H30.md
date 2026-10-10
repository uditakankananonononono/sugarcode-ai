# CONTRACT_H30 - ailibrary.search() ranking characterization (SECOND REPLACEMENT; authored, NOT RUN; tests + contract only)
Parent: 4fb006914deb9e960a8bb6a5dedeef6b1fb9d9a3 (tree 68ba79972ec8904982de07da117fb3f942d12cc1). Authority: peer ruling and grants relayed by Main (6:04:59 PM and 6:06:43 PM IST), not independently authenticated by me. No product edit, no old-test edit.

## PERMANENT DEVIATION RECEIPT (original candidate)
- Original commit 05c9a46958c58907c6cb53854e0a74dfe08f33d5 (tree d3385ce05111207788a79e0b935bf8aeb8a8b829) is REJECTED per the peer ruling.
- First replacement 78af329e6c76ae59a6c483026df646c03044c758 (tree 97b0c84f647f712af429ccc01506212f6e7a6f9f) is superseded only because its contract mis-stated a time (see below); its tests are byte-identical to this commit's.
- This commit is a second replacement built from scratch on a clean branch at 4fb00691, not stacked on 05c9a469 or 78af329e.
- The original gate was NOT met: before authoring I had read tests/test_llm_layer.py only at lines 171-186 and 1-12 at 4fb00691. The before-author ranges 165-170 and 187-190 were missing. (I had read 165-190 at a29dddd5, blob-identical, but that does not count as the gate.)
- Chronology, 10 Oct 2026 IST: original authored 18:05:16-18:05:20; the gap read was 18:06:13 (after authoring). First parent artifact report 18:05:57; my hold report to the peer 18:06:06; the peer's ruling arrived at 18:06:30 IST per the peer's own message as relayed by Main (I cannot verify that time myself); 18:06:43 is only when the builder (me) received the relayed ruling. Later reads do not repair that chronology.
## Chronology of THIS replacement (test first)
Gate reads at 4fb00691 completed 18:06:47-18:06:48; clean branch from 4fb00691 and tests authored 18:06:51-18:06:56; this contract after. No source step.

## What the tests pin (findings only; derived by reading ailibrary.py 88-97, not observed at runtime)
1. words = query lowercased tokens of [a-z0-9]+ with len>1; per slug score = sum over words that are substrings: 2 if the word is an exact hyphen segment, else 1; score 0 dropped. Index ["ai-image-generator","image","imaged","photo-editor"], "image generator": scores 4, 2, 1, dropped; order ai-image-generator, image, imaged.
2. Sort key (-score, len(slug), slug): index ["bb-xx","a-xx","c-xx"], "xx": all 2, order a-xx, c-xx, bb-xx.
3. Single-character words are ignored: "a" and "x y" give []; "a image" gives ["image","ai-image-generator","imaged"] (scores 2, 2, 1; len 5 before 18).
4. limit=1 gives the top item only; limit=0 gives [] (sorted(scored)[:0], line 96). Separate tests.
5. details=True calls tool() once per top slug in order (limit=2: ai-image-generator, image) and returns its results; imaged is not called.
Out of scope: negative limit, index()/tool() cache and network behavior, the CLI route.

## Dependency impact of the gate ranges (assessed after reading them in full)
tests/test_llm_layer.py 165-170 is the tail of a copilot test plus blank lines; 187-190 is the start of test_needle_dataset_answers_execute. Neither mentions ailibrary. test_ailibrary_parsers_offline (171-186) covers parse_sitemap, parse_tool_page and tool("../admin") only; none of the five pins calls those, so none depends on them and none contradicts them. cli.py 304-308 (_cmd_ailibrary calls ailibrary.search(args.query, limit=args.limit); default limit 5 at 1657-1665 line "--limit" default=5) is not exercised by the pins.

## Read receipt at 4fb00691 (timestamps IST; all verbatim)
- 18:06:47-48: src/sugarcode/llm/ailibrary.py 1-50 and 51-97, full (9c32ea9627c003ac45004b5fc7982bf195d87ddf); tests/test_llm_layer.py 165-190, full, including all of test_ailibrary_parsers_offline (6fc302ff6a7f6679c1326497dc8fb8acc56943a8; rest of file grep-only); src/sugarcode/cli.py 304-308 and 1657-1665 (6deca9be51c878920eae0afd66786a071f61dfbf; rest grep-only).
## RUN vs NOT RUN
RUN: git object ops, sed/grep reads, sha256sum. NOT RUN: pytest, import, py_compile or any syntax check, pip, network. Expected values are by hand and may differ if I misread; peer run decides.
