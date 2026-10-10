# H35 deterministic terminal-read error characterization

Exact parent 8175301420b92955f6e3c8ab29e319fcc2832350.
Test+contract only, no helper/product/old-test change. Two deterministic
synthetic error pins, not a repair, reaping proof or Linux absence guarantee.

## Source gate and sequence
Full H27 helper, deterministic tests, bounded-process test and pipe-cleanup
test read at 20:47:27 IST, 2026-10-10, before authoring. Helper blob
3b147ff0de6a0470df109a2b9289bc52f319ee39; deterministic-test blob
ce7333df4bb92cdab220b228004d14249c7e87d6; bounded-test blob
5bc850e363634525a7ace701a6e19d64d6687c2d. Tests authored before execution;
contract afterward. This chronology is documentary self-report, not independent
proof of comprehension. Parent ratified exact two-pin scope at 20:47:40.

## Observed original failure and bounded scope
H34 fresh-public wider run originally had 1863 PASS / 1 FAIL / 13 XFAIL,
38.75s: test_same_group_descendant_killed_on_timeout returned terminal False,
last_state None, error ProcessLookupError. Original XML/console preserved and
reported. Later no-edit rerun had 1864 PASS / 13 XFAIL; it does not erase FAIL.
No actual /proc snapshot or root-cause/reaping claim is supplied here.

Current helper treats FileNotFoundError as absence but all other OSError
subclasses as diagnostic errors. New pins inject ProcessLookupError(ESRCH) and
OSError(EIO), assert the complete result including nonterminal status, exact
exception-class label, one sample, unavailable observed identity, exactly one
read and no sleep. This labels current behavior only. Treating ESRCH as absence
would require a separate explicit policy decision and source grounding.

## Author execution, not inherited independent verdict
New 2 PASS 0.11s. H27 trio+new 42 PASS 1.82s. tests/self_improve only:
1840 PASS / 13 XFAIL 36.64s, not configured global suite. Four temporary helper
mutants killed: all OS errors absent, ESRCH absent, generic error-label stub,
always-terminal stub. Original helper restored byte-exact, new tests rerun.
No product changes committed, no landing/push before independent audit/EXECUTE.
