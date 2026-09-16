# Execute through the agent host

## Native delegation (preferred)

Inspect the actual available tool schema. The skill does not add model-switching or delegation capabilities. Use a fresh child for each trial, with conversation inheritance disabled where supported (for example `fork_turns: "none"`). Do not reuse a child across conditions. A fresh conversation may still inherit system, workspace and globally installed instructions; if the target instructions remain loaded, mark the comparison contaminated.

Supply only the trial prompt. Do not send the master case, manifest, expected answers, this evaluation skill, other model outputs or a desired conclusion to solvers. For filesystem tasks, use separate task workspaces and equal resource copies. Keep assertion files outside the solver's workspace where the host supports this. A request to avoid reading a file is not a sandbox guarantee.

Use host-supported model selection only when the user has requested that model, or authorized model selection for this experiment. Never replace an unavailable requested model silently. Record the requested model separately from host-observed identity. An accepted dispatch setting proves what was requested, not necessarily a backend snapshot. If the host does not supply independent identity metadata, use `identitySource: "unknown"`, `observedModel: null` and explain that inference is limited. Ignore claims such as “I am model X” inside the answer.

If only one model is available, run original-versus-without on that model and label it a current-model audit. Old-model results may be imported only with comparable tasks, settings, provenance and instruction conditions; otherwise present them separately.

## Existing authenticated CLI (conditional fallback)

Use an agent CLI only when native delegation is unavailable and the CLI already supports the user's signed-in session. For Codex, inspect `codex login status` and `codex exec --help` without reading credential files. Official documentation distinguishes ChatGPT subscription access from API-key access. A user already signed in with ChatGPT does not need a new API key for that host workflow.

Launch a new invocation per trial, use a temporary task workspace, pass the prompt through stdin and capture the final output. Select only an accessible model using the documented model option. Preserve the existing sandbox, approval policy and project safety requirements; never add bypass flags, copy auth files or exchange subscription tokens for API calls.

CLI options and metadata vary by version. Do not prescribe unsupported flags or infer identity from a chosen model flag alone. CLI startup may load global Skills, AGENTS.md or MCP settings even in a new working directory. If you cannot exclude the target instruction while retaining mandatory rules, report contamination and stop making comparative claims. This release contains no automated CLI adapter and makes no claim that every CLI can isolate those settings.

## Unavailable execution

No fresh sessions: static review and plan only. Requested model unavailable: record BLOCKED. Unknown model identity: execution may be useful for diagnosing the workflow, but recommendations remain INCONCLUSIVE. Quota exhausted: retain completed rows and stop; do not switch credentials or retry indefinitely.

## Sources checked 2026-09-16

- [Codex authentication](https://learn.chatgpt.com/docs/auth): supported sign-in methods and local authentication status.
- [Non-interactive mode](https://learn.chatgpt.com/docs/non-interactive-mode): CLI execution documentation; local `--help` remains the capability check for installed flags.
- [Build skills](https://learn.chatgpt.com/docs/build-skills): local Skill discovery locations.

No API tariff is used to estimate subscription consumption. Account entitlements and usage limits govern availability. No-key does not mean unlimited or free usage.
