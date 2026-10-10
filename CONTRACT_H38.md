# H38 BED filter threshold boundaries

Exact parentb39902c72ac51c94a74ca88364035ac7e82dd87f.
Two grouped boundary tests+contract only; not pytest-parameterized functions.
No source/old-test edit, parse/NaN/path/CLI/merge scope or biological validation.

## Source gate and sequence (2026-10-10 IST)
Full bed.py1-180 and direct tests1-95 read20:59:00; CLI bed tests1-44 read
20:59:08 before authoring. Source blobcdaf35e536e26de74b34b8312a8cff7ab23d57e8;
direct-test533b14adff0f59a38e2030409ec5e432d5d911a2;
CLI-testccc9822ba156fdaf567704b9e2fd23d0fcdaf7f0.
Tests first, execution afterward, contract last; documentary self-report only.

## Exact literal findings
Width9/10/11 at min_width10 returns exact width10/11 records, header retained.
Score9/10/11/missing at min_score10 returns exact score10/11 records, header
retained. Deep input equality after filtering pins no input-value mutation.
Current strict-less-than exclusion keeps equality. Existing tests count outputs
at60; this unit supplies below/equal/above and missing-score shapes. No external
standard oracle, desired-policy or exhaustive coverage claim.

## Author runs, original failure preserved
New2 PASS0.12s; new+bio_bed+cli_bed17 PASS0.39s. First wider
self_improve+same3files:1856 PASS/1 FAIL/13 XFAIL37.23s. Unchanged canary
same_group_descendant_killed_on_timeout returned terminal False, state None,
ProcessLookupError, elapsed5.188099748920649e-05. Original XML/console sent and
retained. No actual proc snapshot or root cause/reaping conclusion.
No-edit H27 trio recheck40 PASS1.76s; full recheck1857 PASS/13 XFAIL36.22s.
Passing recheck does not erase original FAIL or resolve the error policy.
Five temporary BED mutants killed: width equality excluded, score equality
excluded, missing score retained, all-records stub, header dropped. Source
restored byte-exact, new2 PASS0.10s. Not configured global suite.
Independent audit/EXECUTE required before landing.
