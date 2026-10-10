# CONTRACT_H25 - shared dataset ValueError boundary (characterization)
Parent: 9a6b93805f31d3b9df77b7a031d58b726a5c4bc0 (taken from the peer-supplied bundle; tip verified by git object ops only).
Files: tests/test_h25_shared_dataset_valueerror_characterization.py, CONTRACT_H25.md. No product change.

## Chronology (test first)
- 17:32:46 branch created at 9a6b9380; 17:33:02 tests authored; contract after. Replacement candidate (supersedes a6e25c2, which stays as history): registry and catalog full re-read 17:34:54-17:35:04, tests unchanged, contract updated.

## RUN vs NOT RUN
- RUN: git object operations only (bundle verify, fetch, rev-parse, show, cat-file), sha256sum, sed/grep reads.
- NOT RUN: pytest, SugarCode import, any solver, pip, network, py_compile or any syntax check. The tests are authored NOT RUN and unverified; a typo is possible.

## Pinned behavior (read from source, not observed at runtime)
1. cli.py _cmd_shared dataset branch catches ValueError and emits {"error": str(e)}, returns 1.
2. Success emits the manifest dict, returns 0.
3. Only ValueError is caught (OSError, RuntimeError propagate).
4. build_needle_jsonl raises ValueError("no usable rows after filtering") (training/dataset.py) before mkdir/write; no out file, no .manifest.json.
5. Real CLI with --max-tools 0: llm/dataset.py slices cat[:0] to empty, so the same error. Runs the real catalog; the peer's audit runs it.
Excluded: interpreter version texts, the Python sample message, NUL-path text, success dataset content (covered by test_shared_layer).

## Read receipt (blob ids identical at 352ccdc5 and 9a6b9380)
- verbatim, full: src/sugarcode/cli.py 6deca9be51c878920eae0afd66786a071f61dfbf (lines 93-96, 281-304, 1640-1660 only; not the whole file)
- verbatim, full: src/sugarcode/llm/shared.py 72c63465d978b08db7e27d064b550af4fe342b12
- verbatim, full: src/sugarcode/llm/dataset.py 455de37ee325066d906610d6bf961de057208988
- verbatim, full: src/instinct_models/training/dataset.py 9392b180d0ff94b085d429ca94d8490a26331a40
- verbatim, full: tests/test_shared_layer.py 4464a00fda0a684b1bde92767ad537901ba50e38
- verbatim, full: src/sugarcode/llm/tools.py 1406877c06205d315eeb92cdc4db74cdfd13f09c (catalog())
- verbatim, full, untruncated, re-read in chunks at 17:34:54-17:35:04: src/omega/registry.py f0c8059760652f890b834bdb3fc021546b10f328 lines 1-40, 41-70, 71-100, 101-125, 126-150, 151-170, 171-190, 191-210, 211-222, 223-232, plus 233-248 (earlier read). Total file is 248 lines. src/sugarcode/llm/tools.py lines 1-95 and 96-188 re-read in full at 17:34:59.
- Dependency check: the tests and contract do not depend on registry content; registry feeds catalog() via module_slugs(), and test 5 depends only on cat[:0] being empty (llm/dataset.py build, sorted(catalog().values())[:max_tools]) and n_off being 0 when raw is empty (llm/shared.py 148). Whether catalog() imports modules successfully at runtime is not verified by me.

## Limits
Not independently authenticated by me: the peer's rulings, the base claim and H25 grant arrive via Main. No claim of done, tested or working. Object 588c26f9 resolves in this bundle (rev-parse); I make no other claim about it.
