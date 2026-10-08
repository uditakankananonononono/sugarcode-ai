# Chat response boundary

ChatClient.chat reads at most1000001raw bytes, refuses over1MB, malformed UTF-8
or JSON/decode recursion, nonobject root, absent/nonlist/empty choices and
nonobject first choice/message via ProviderError. Existing provider fallback
can classify these as upstream failures, not uncaught type/decoder errors.
Real localhost HTTP200responses tested; no live provider acceptance implied.

Byte cap covers successful chat response only, not HTTP error-body read, health
probe, request body, network time beyond existing timeout or nested schema.
Message content/tool-call fields not fully validated by this boundary.
