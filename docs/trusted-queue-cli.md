# Trusted local queue CLI

Opt-in scripts from your own workspace. This is NOT an isolation boundary.
Submitting never executes a script. Explicit `run` executes the next pending
script using the existing local resource-limited queue, not a container.

```sh
printf 'print(6*7)\n' > /tmp/trusted-42.py
python -m sugarcode.cli queue --db /tmp/local-queue.sqlite submit demo --script /tmp/trusted-42.py
python -m sugarcode.cli queue --db /tmp/local-queue.sqlite run
python -m sugarcode.cli queue --db /tmp/local-queue.sqlite show demo
python -m sugarcode.cli queue --db /tmp/local-queue.sqlite receipt demo --out /tmp/demo-receipt.json
python -m sugarcode.cli queue --db /tmp/local-queue.sqlite verify --receipt /tmp/demo-receipt.json
```

`cancel JOB_ID` only cancels pending jobs. A false result means nothing was
cancelled. Receipts detect changed DB/receipt content, not authenticity or
verified effects. Crashes can leave uncertain effects, no exactly-once claim
or automatic retry. An empty queue returns a null job_id. Local paths belong
to the operator; do not point this command at other people's data.
