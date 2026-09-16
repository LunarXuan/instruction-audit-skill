---
name: instruction-audit
description: Compare two user-selected models by creating fresh model-specific subagents in the host to evaluate SKILL.md or AGENTS.md instruction value, without a separate API key. Use for instruction retention, trimming and migration experiments.
---

# Instruction audit

Evaluate instruction value by having fresh agent sessions solve the same representative tasks with and without the optional instructions. Use the host's authenticated model tools; this skill has no API client or credential store.

## Establish what can actually be tested

Identify the target file, the user-authorized models and the available session/delegation tools. Read [host execution](references/host-execution.md) before dispatch. Prefer native fresh subagents with no inherited conversation. Use only model identifiers accepted by the host; a prompt cannot change the running model. One available model supports a current-model comparison, not an old-versus-new migration claim.

If no fresh context is available, provide a static review and a ready-to-run test plan, labeled **NOT EXECUTED**. Do not answer the trials yourself or fabricate a model transcript. Unknown model identity or inherited instructions makes the outcome inconclusive. Do not ask for an API key as a fallback.

## Build a useful comparison

Accept either a user-selected `AGENTS.md`, `SKILL.md`, or Skill directory/name. Resolve a name to its installed entry point; if multiple matches exist, ask which one. Follow [selected Skill evaluation](references/selected-skill.md) for package resources and scope. Do not substitute the workspace AGENTS.md for the specified Skill.

When the user names two models, follow [model-specific subagent construction](references/build-agents.md). Resolve their names against the actual host model list, prepare two model groups, then execute the dispatch plan through native delegation; do not stop at merely writing the plan when execution is supported and authorized. Each trial uses a fresh child. Two model groups do not mean two persistent conversations reused across conditions. If either requested model is unavailable, explain the blocked comparison rather than silently substituting or reducing it to one model.

Read the target and separate mandatory safety/business requirements from optional scaffolding. Put the former in protected text shared by every trial. Do not weaken host protections or remove actual tools/resources. For each optional block, state the behavior it should improve and an observable check. Inventory dead links and environment-specific commands separately from claims that a model has absorbed a capability.

Choose tasks representative of the user's workload. Separate candidate-development tasks from unseen holdout tasks. Use existing project assertions where available; otherwise draft verifiable outcomes and disclose who authored them. Never call self-generated toy tasks representative real-world evidence. Do not provide expected answers, other trial outputs, variant labels or the audit instructions to the solving agent.

Use original / without-optional / optional-shorter-candidate conditions. Keep task inputs, tools, permissions and reasoning settings comparable. Start with a small disclosed call count, normally no more than 12 sessions; respect the user's quota/budget preferences and stop on quota or access errors. Broader repetitions consume the same host allowance as ordinary agent work.

For text-answer tasks, [the helper protocol](references/helper.md) provides preparation, independent exact-answer checking and report generation with Python 3, no third-party dependencies. For richer code or artifact tasks, use project tests and record their actual output; the included helper does not grade them. Never execute untrusted model-generated code merely because it appears in an answer.

## Run and interpret

Dispatch one fresh context per task × model × condition × repetition. Shared process permissions are not filesystem isolation: give a solver only its prompt and authorized inputs, and account for any globally loaded instructions or accessible evaluation files. Preserve actual session identifiers, answers, errors and host metadata. Unknown telemetry remains unknown; a model's self-description is not model identity evidence.

The coordinator, not the solver, checks outcomes. Keep failed and missing trials visible. Repeated trials of the same task do not increase independent sample size. Report changed instructions, quality regressions, per-task differences, uncertainty and coverage limitations. Do not infer “unnecessary” from a nonsignificant difference. Character-count reductions are not measured token or cost savings.

After the trials, the main model must perform [the final evidence review](references/final-review.md). Combine task quality with measured elapsed/thinking time, reported usage/quota and public execution summaries. Record only host-exposed telemetry: do not request, reconstruct or store private chain-of-thought. Do not equate elapsed time with thinking time, tokens with subscription quota, or unknown usage with zero. Missing efficiency data limits efficiency claims, not the ability to report observed quality. Provide a concrete per-model retention proposal and reasons while preserving the helper's uncertainty labels.

Produce a concise report with: host/model evidence; what was executed; per-condition observations; protected requirements; proposed edits with reasons; and remaining uncertainty. Return **INCONCLUSIVE** where isolation, identity, coverage or evidence is insufficient. Suggestions to trim or retire are review candidates, never automatic deletion. This evaluates supplied instruction content; native Skill discovery and scripts need separate functional checks such as `skill-smoke`.
