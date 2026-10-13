# Persisted support SLA deadline

The store uses the displayed `sla_hours` value, rounded to two decimal places,
to compute its persisted `response_due_at`. This makes `open_ticket`, `dumps`
and `loads` agree exactly on the stored deadline.

`core.triage` still returns a deadline computed from the unrounded SLA.
The persisted store deadline can therefore differ from the raw triage deadline
by up to 18 seconds (0.005 hours). This is an intentional store-only contract.

The urgency/tier round-trip tests cover the known rounded-SLA cases. These
bookkeeping tests do not establish real response service levels or biological
validity.
