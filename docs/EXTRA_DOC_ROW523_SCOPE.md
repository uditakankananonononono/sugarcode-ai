Source verbatim: Backup Strategy - Protects data.
Exact supplied backup-chain reconstruction metadata arithmetic only: full root or
incremental ancestors all available, strictly increasing parent timestamps, best
recoverable timestamp <= requested by latest timestamp then lowest chain bytes
then lex chain. No stored bytes, integrity checks, live restore, retention or
actual data protection. Helper caps 64 backups, timestamps 0..1e9, bytes 0..1e12.
