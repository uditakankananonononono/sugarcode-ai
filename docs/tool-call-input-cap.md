# Input tool-call-list cap

Missing or None tool_calls means no calls, following the existing answer path.
A non-list, non-None value or a list with more than24calls is refused before
that response appends assistant calls, dispatches tools or builds trace rows.
Oversized responses are refused wholesale, not truncated.24valid calls work.
A ProviderError enters existing provider failure handling. No tool action from
THAT refused response happened. Tool effects from earlier rounds survive a
later refusal; this is not rollback or an all-rounds no-partial-action claim.
Prior100call test expects response-local refusal/no dispatch.

This bounds input-list processing, not provider JSON download/decode bytes,
argument/response string size, individual execution time or cumulative steps.
Provider fallback after refusal follows existing policy. Tests use local model
protocol responses and real catalog calls, no live provider acceptance.
