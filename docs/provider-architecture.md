# Provider architecture: Composio and Sarvam are tools, not the brain

The Academic Brain (`retrieval/`, `graph/`, `algorithms/`, `assessment/`)
never imports Composio's or Sarvam's SDKs/HTTP clients directly, and must
stay runnable fully offline/local. External capability is added behind two
small interfaces instead:

- **`integrations/base.py`'s `ActionProvider`** — external side effects
  (Google Calendar today; Drive/Gmail/Sheets/Forms/Tasks are real product
  decisions, not built yet). `integrations/composio_provider.py`'s
  `ComposioProvider` is the one real implementation, used by
  `integrations/composio_calendar.py`'s `sync_to_google_calendar()`.
- **`llm/base.py`'s `LLMProvider`** — chat-completion capability.
  `llm/sarvam.py`'s `SarvamLLM` is the one real implementation, used by
  `agents/critic.py`'s `SarvamCritic`. Named generically, not
  `SarvamProvider`/`VoiceProvider`: the only real Sarvam capability wired up
  today is chat completions — there is no STT/TTS/vision call in this
  codebase to build an interface around yet. Add those methods to the ABC
  only once a real call exists to implement them.

Both providers plug into the *existing* `agents/base.py` `Tool` ABC that
`SearchTool`/`ConceptLookupTool` already implement against the Brain's own
retriever/graph — `agents/composio_tool.py`'s `ComposioActionTool` wraps any
`ActionProvider` action as one more `Tool` an orchestrator can register, with
no special-casing of Composio anywhere in `agents/orchestrator.py`.

Either provider can be swapped or removed without touching Academic Brain
code: nothing under `retrieval/`, `graph/`, `algorithms/`, or `assessment/`
references `ComposioProvider`, `SarvamLLM`, or their HTTP layers. Both are
optional — unconfigured (no API key) means the corresponding `available()`
check returns `False` and callers degrade gracefully (see
`sync_to_google_calendar`'s no-op path, `SarvamCritic`'s neutral-score
fallback), never a hard failure.
