# Input tool-call-list cap

Copilot refuses a non-list or a list with more than24calls before it appends
assistant calls, dispatches any tool or builds the trace. Oversized responses
are refused wholesale, not truncated. A ProviderError enters existing provider
failure handling; no partial tool action happened for that refused response.
24valid calls still work. Prior100call test now expects refusal/no dispatch.

This bounds input-list processing, not provider JSON download/decode bytes,
argument/response string size, individual execution time or cumulative steps.
Provider fallback after refusal follows existing policy. Tests use local model
protocol responses and real catalog calls, no live provider acceptance.
