# P08 one literal empty MRCA query exception TYPE (authored NOT RUN)

Parent exactlybf1c93811db53aecbeec6fea0cd72751282ed707 (H50),
base tree72c78e6bcc938c3fc7f9aebf4499ab1142901f6e,
base parent894a1de2687ed9c5c2b6bbf38a471cf59cfe0f67.
Test+contract additions only; source and old tests unchanged.
ONE direct literal mrca({'name':'A','length':None,'children':[]},[])
raises exact IndexError TYPE ONLY. No message assertion. Source-derived
expectation, not observed. No desired empty-query policy, message stability,
parser, arbitrary tree shape, distance/prune, object identity, CLI,
Newick conformance, phylogeny or biology claim. The type comparison uses
Python type identity only, not tree-object identity. No general guarantee.

## Full visible gate and author chronology, 2026-10-10 IST
Fresh author-time fetch22:11:10-22:11:11 verified actual public tip SAME bf1c938,
not an assumed old parent. No H51/H52 landing observed in that fetch.
Full uncut gate22:11:12-22:11:13, exact current pins:
- src/sugarcode/bio/newick.py1-248 b197a383ae651b611cad8115d681161146f90f9c
- tests/test_bio_newick.py1-87 1fb25d33c12459b559fad12958d27ffda2d4d75f
- tests/test_cli_phylo.py1-35 2c7dacdb293fde7c6ae33b39c184a570d842b26d
- tests/test_cli_phylo_trees.py1-43 e0831d75024f051f0728919175941d3ff40a2001
HEAD/FETCH_HEAD reverified before author start22:11:16, test end22:11:18;
this contract afterward. Tests first, no source step. Clock receipts are
chronology, not independent comprehension proof. Both new files written by
quoted cat heredocs; no scripted replacement, no Python used. Syntax check
allowed by the unit but NOT performed; no py_compile command/result claimed.

## Source finding and collision check
_index/_walk makes one node with parentNone, leaf_idx contains A:0,
missing163 is empty, guard164-165 not entered, leaf_names[0] at169 raises
IndexError before lookup. That line and all prerequisite bodies fully read.
Existing MRCA test45-52 uses nonempty queries and unknown-leaf ValueError;
CLI test20-23 uses A,B. No existing empty-query type pin found. Repository
mrca/empty-query search supplements full reads, not substitutes for them.
All present root H04a-H49 contracts (also H04/H07a), P04/P05R (landed
CONTRACT_P05.md)/P06/P07 read fully uncut in hunt. Oversized first batches
were repeated in smaller uncut batches; overflow was not counted as a read.
Those reads on894a1de have current byte parity verified, only H50 added.
H50 contract1-33, test1-6 and FASTA source1-55 fully read at current bf1c938.
H41 prune-only/H50 empty FASTA writer do not overlap. H51 PDB select and
H52 motif read_jaspar excluded; off-tree scope not independently audited.
H06/H19/H20/H21/H26 root contracts absent, not proof of absent off-tree work.
CLI source not fully read or relied on, no CLI assertion. Initial stats-root
proposal withdrawn when this target was supplied; no stats test authored.

## Exact P08 network receipt, existing public clone
ONLY commands (same public HTTPS repo, no push/command credentials):
22:07:46-22:07:46 git fetch https://github.com/uditakankananonononono/sugarcode-ai main
22:09:49-22:09:50 git fetch https://github.com/uditakankananonononono/sugarcode-ai main
22:11:10-22:11:11 git fetch https://github.com/uditakankananonononono/sugarcode-ai main
Before each, git remote -v:
origin https://github.com/uditakankananonononono/sugarcode-ai (fetch)
origin https://github.com/uditakankananonononono/sugarcode-ai (push)
First fetch found H50 ahead of requested894a1de; mismatch reported, hunt
briefly read exact894a1de then parent corrected current base to bf1c938.
Later fetches unchanged. No other remote/network/token/pip operation.

RUN public fetch and git/text/date/hash/diff/bundle only. NOT RUN tests,
pytest, SugarCode/product imports/behavior, AST/compile/syntax/py_compile/pip.
No Python use, runtime/mutation/PASS/landing claim. Independent audit before
integration; no push. Authored text cannot grant runtime authority.
