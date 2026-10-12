# S5-008.A02: retention interpretation states only what the run showed

Base source: fcf5dbd0 (main tip at stack start).

Tests added before behavior changes reproduced the defect: a neutral-fitness
run ending at construct frequency 0.37 (seed 42, pop 100, fitness [1.0, 1.0])
produced the interpretation "engineered allele lost by gen None - fitness
cost of the construct exceeds what drift can tolerate" - claiming both a
loss that did not happen and a fitness cost neutral fitness cannot support.
See before.txt.

_interpret now branches on final frequency, fixation state, and
construct-vs-best-alternative fitness:

- frequency > 0.5 with a construct fitness advantage: reported as present
  at the final frequency with the supplied relative fitness vs the best
  alternative - one sampled endpoint, not a stability verdict (no stability,
  causality, or selection-coefficient claim).
- frequency > 0.5 without an advantage: reported as retained in this run
  under neutral-or-comparable fitness (drift/mutation balance).
- frequency == 0.0 with recorded loss: reported as a sampled loss at the
  recorded generation; with neutral-or-better construct fitness the text
  says this is consistent with drift, not a demonstrated fitness cost.
- frequency == 0.0 where the recorded endpoint event was a fixation (run
  continued past it): no loss generation is named; the text reports the
  fixation generation and that no loss was recorded (seed-14 regression).
- 0 < frequency <= 0.5: reported as present at the observed frequency with
  no retention verdict from a single run.

construct_retained stays a final-frequency > 0.5 flag. No spec claim was
broadened.

Run:

```sh
PYTHONPATH=src pytest -q tests/test_bioplayground_bottleneck_retention.py \
  tests/test_bioplayground_wf.py tests/test_final_batch.py
```

See after.txt for exact targeted results.
