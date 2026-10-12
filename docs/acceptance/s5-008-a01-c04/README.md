# S5-008.A01.C04: scheduled bottlenecks fire even after fixation/loss

Base source: fcf5dbd0 (main tip at stack start).

Tests added before behavior changes reproduced the defect: with
bottleneck_at=150, run_sandbox stopped at gen 1 (construct_fixed, seed 42,
pop 200) and at gen 92 (construct_lost, fitness [0.9, 1.0], seed 0), so the
scheduled bottleneck event never fired. See before.txt.

run_sandbox now stops early on sampled fixation/loss only when no bottleneck
is still scheduled; while bottleneck_at is pending it continues so the
bottleneck fires at its scheduled generation. Pinned no-bottleneck behavior
is unchanged: gen-1 fixation still reports generations_run == 1, and the
seed-0 loss still reports fixation_gen == 92 (tests/test_bioplayground_wf.py).

Only the loop exit condition and first-event kind tracking changed;
selection/mutation/drift math and all returned field shapes are unchanged.
The first fixation/loss event now records its kind so post-continuation
interpretation can distinguish a historical fixation from a loss. No spec
claim was broadened.

Run:

```sh
PYTHONPATH=src pytest -q tests/test_bioplayground_bottleneck_retention.py \
  tests/test_bioplayground_wf.py tests/test_final_batch.py
```

See after.txt for exact targeted results.
