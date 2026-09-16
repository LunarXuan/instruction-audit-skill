# Main-model review after execution

The main coordinating model writes the final review from recorded observations. Solving subagents supply task answers; they do not decide whether their own instructions should be retained.

## Evidence to collect

Record elapsed time around actual dispatch-to-completion when the host exposes completion events. If only polling receipt times are available, label timing as an upper bound in evidence and do not use small differences to rank conditions. Think time must be a separate host-reported metric; never derive it by subtracting guessed network/tool durations.

Use actual per-run host input/output/reasoning token counts if available. Subscription quota is a different metric. Record quota consumption only when the host attributes it to the trial; an account-wide before/after percentage can include concurrent work and must not be assigned to one child. No conversions from tokens or wall time to quota, currency or paid credits without explicit relevant telemetry.

For “thinking process,” use only observable behavior: tool calls, retries, assertion/test failures, corrections, path choices, and a brief public rationale summary where available. Do not ask for or store hidden chain-of-thought, internal deliberation, or a reconstructed private reasoning transcript. Additional requests for summaries would change measured workload; if needed, request them after timing and keep them outside task answers and grading.

Optional response telemetry uses `metrics` with each value carrying unit, source and evidence. See [helper protocol](helper.md). Put a concise observed trace in `executionSummary`. Missing information is unknown. Coordinator attestations are not independently verified by the helper.

## Weigh the evidence

Prioritize correctness, required behavior, safety and artifact quality. Compare latency and usage on matched tasks only after checking these outcomes; a faster failed answer is not a benefit. Describe per-task paired differences and variability. Record reasoning effort, host/tool settings, workload scheduling and cold starts where observable. Different model settings or incomplete telemetry can prevent fair efficiency comparisons.

Do not use verbosity, long reasoning or a persuasive self-explanation as a quality score. Visible extra checks may either prevent a real error or add needless work; explain which based on observed outcomes. Do not impose arbitrary weighted scores or hide missing measurements in a composite number.

## Deliver a recommendation

For each requested model and target, write:

| Item | Required content |
| --- | --- |
| Target and scope | Exact AGENTS.md / Skill; text-only or independently tested package behavior |
| Quality | Pass/fail evidence, protected requirements, concrete regressions and task coverage |
| Time | Measured elapsed time; host thinking time or unknown; collection limits |
| Usage | Host tokens and separately quota with units; unknown where unavailable |
| Execution | Observable tool/retry/test behavior and short public summary |
| Proposal | Keep, simplify named sections, model-specific candidate, or insufficient evidence |
| Confidence | Missing identity/isolation/telemetry, sample uncertainty and contrary observations |

A simplification proposal may be useful even when statistical evidence is inconclusive, but label it **unverified candidate**, not proven redundant. If either model needs a rule, suggest a model-specific candidate or retain the common rule rather than deleting it globally. Package removal requires package-level evidence and preservation of required capabilities. Do not override INCONCLUSIVE because a timing/usage number looks favorable.

Write this review as a separate `recommendation.md` next to the unchanged numeric report. Link claims to trial IDs and actual observations. Never automatically edit the user's target or mark unknown telemetry as measured.
