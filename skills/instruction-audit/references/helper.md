# Text-task helper

The coordinator uses [audit.py](../scripts/audit.py), located under the installed Skill's scripts folder. Python 3.10+ standard library only. It never calls a model, accesses credentials or executes a solver's answer. Running this protocol alone does not constitute a model experiment.

## Prepare

Write a UTF-8 JSON case outside the solving agents' input folders:

```json
{
  "name": "My instruction audit",
  "models": ["ACTUAL-HOST-MODEL-ID"],
  "protected": "Mandatory requirements shared by all trials.",
  "original": "Optional instructions to evaluate.",
  "candidate": "Optional shorter instructions.",
  "repeats": 1,
  "maxTrials": 12,
  "tasks": [
    {"id": "case-one", "split": "holdout", "prompt": "Return the sum of 2 and 3 as an integer.", "expected": "5"}
  ]
}
```

Omit `candidate` for two conditions. Use 1–4 distinct model labels, 1–5 repeats, at most 50 tasks and a maximum of 120 trials; default limit is 12. `expected` is an exact string, including whitespace. Adapt the prompt so the intended answer format is explicit. Use `development` for candidate iteration, `holdout` for unseen evaluation. The helper cannot establish whether tasks were truly unseen or representative.

```sh
python SKILL_DIR/scripts/audit.py prepare case.json --out audit-run
```

The destination must be new. `manifest.json` contains the case and trial map. `prompts/t001.md`, etc., contain only protected instructions, that condition's optional text and the task prompt. Expected answers and other conditions remain in the coordinator's manifest. Condition order is alternated to reduce a simple ordering effect; this is not a guarantee against all temporal confounding.

## Dispatch and record

Launch one fresh host session per prompt, following [host execution](host-execution.md). The coordinator captures the final answer and the host's actual metadata in a response file:

```json
{
  "answer": "5",
  "status": "COMPLETED",
  "requestedModel": "ACTUAL-HOST-MODEL-ID",
  "observedModel": null,
  "identitySource": "unknown",
  "sessionId": "actual-host-session-id",
  "isolated": true,
  "synthetic": false,
  "note": "Fresh session, but this host did not expose resolved model identity."
}
```

Use `identitySource: "host-metadata"` and a real `observedModel` only when supported by independent host evidence. Dispatch parameters are not sufficient proof of backend identity. `isolated` describes absence of target-instruction/answer/history contamination, not an OS sandbox. `sessionId` must come from the host; do not invent one to satisfy validation. Reused or absent identities make evidence inconclusive.

All displayed fields except `note` are required, including for `BLOCKED` or `ERROR`; use `answer: ""` when no answer exists. Use `synthetic: true` for hand-written fixtures. Never submit a solver-supplied `passed` flag: the helper computes it.

```sh
python SKILL_DIR/scripts/audit.py record audit-run --trial t001 --response response-t001.json
```

Existing records are not overwritten. Preserve failed attempts instead of cherry-picking a retry. For a revised experiment, prepare a new run and explain the change.

## Report

### Optional timing, usage and public trace

Each response may include `metrics` and `executionSummary`. For example:

```json
{
  "metrics": {
    "elapsedMs": {"value": 8400, "unit": "ms", "source": "coordinator-timer", "evidence": "Measured dispatch through completion event for this trial."},
    "inputTokens": {"value": 1200, "unit": "tokens", "source": "host", "evidence": "Per-trial usage event."}
  },
  "executionSummary": "One file read, one failed assertion, then a corrected artifact passed. Based on visible tool events."
}
```

These are illustrative numbers, not measured results. Merge these fields into the required response object. Supported metrics: `elapsedMs`, `thinkingMs`, `inputTokens`, `outputTokens`, `reasoningTokens`, `quotaUsed`. Time uses `ms`; tokens use `tokens`; quota uses the host's explicit unit. Only elapsed time can use `coordinator-timer`; all other metrics require `host` telemetry. Each metric requires a nonnegative finite value and a nonempty evidence description. Omit unavailable metrics rather than filling zero.

The report shows per-trial values and sources, plus per-model/condition means with coverage counts. Different quota units cannot be pooled. These descriptive means do not establish causal savings; the main model uses matched-task comparisons and the limitations in [final review](final-review.md). No private chain-of-thought is collected; `executionSummary` is a public action summary, not hidden reasoning.

```sh
python SKILL_DIR/scripts/audit.py report audit-run --out report.md
```

Reports retain absent/failed trials. Any synthetic row, missing trial, blocked/error response, unknown/mismatched model identity, reused session or contamination keeps the matrix inconclusive. Supplied metadata is an operator attestation, not proof the helper can independently verify.

For complete observations, exact-match pass rates and task-level paired differences are shown. Repeats are averaged within tasks. A pointwise 95% Hoeffding interval on original-minus-without assumes independent representative tasks; a positive lower bound may produce `KEEP_CANDIDATE`, meaning a proposal to keep the **original instructions**, not the shortened text. Otherwise the conclusion remains `INCONCLUSIVE`. Candidate-minus-original differences are descriptive. No automatic trimming, retirement or dollar-savings claim is produced.

Use project tests or an independently justified rubric for code, artifact or open-ended quality tasks. They are outside this helper's exact-text scorer; do not convert a solver's subjective self-assessment into an objective pass.
