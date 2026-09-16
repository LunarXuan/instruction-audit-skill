# Construct model-specific subagents

Use this workflow when the user says “compare model A and model B.” This is authorization to select those models for the experiment, not to alter the current parent model or global configuration.

1. Read the host's actual delegation schema and supported model IDs. Resolve an unambiguous display name to its listed ID; ask only if the mapping is ambiguous. Check that fresh contexts and explicit model selection are supported. A model listed by the host may still fail account-access checks on dispatch.
2. Prepare representative tasks and protected/original instructions with the user-requested scope. Read [helper protocol](helper.md) for the text-task case format. State the total planned calls: two models × conditions × tasks × repeats. Keep within the agreed limit, normally 12 calls for a first pass.
3. Use [build_agents.py](../scripts/build_agents.py) to construct two groups and fresh per-trial launch arguments:

```sh
python SKILL_DIR/scripts/build_agents.py case.json --models MODEL_A MODEL_B --available-models MODEL_A MODEL_B --max-trials 12 --out comparison-run
```

`--available-models` must come from observed host capabilities, not from copying arbitrary user requests. This argument validates configuration only; it does not grant model access. The script overrides the case's model labels without modifying the source case, prepares the prompts, and writes `dispatch.json`. It has no network client and does not launch agents itself.

Add `--target /path/to/SKILL.md`, a Skill directory, or `AGENTS.md` to evaluate the user-selected entry point instead of the inline original. Follow [selected Skill evaluation](selected-skill.md). Collect telemetry during dispatch and finish with the main model's [evidence review](final-review.md).

4. The coordinating agent reads `dispatch.json` and calls the host's native `spawn_agent` (or its supported equivalent) for each row. For the supported schema, `spawnArguments` contains `task_name`, `model`, `fork_turns: "none"` and `message`. Use a unique run prefix for task names if needed. Do not add a role with a fixed different model. Apply identical supported reasoning settings to both groups, or document why differing settings change the interpretation.
5. Respect concurrency slots: schedule paired model trials as capacity allows, wait for their results, and create new children for subsequent trials. Do not send successive conditions to the same child. A solver sees only its row's message, not the manifest or dispatch plan. Coordinate resources under the existing permissions; never invent a sandbox guarantee.
6. Record actual host session references and outputs using `audit.py record`. Requested `model` is not observed backend identity. If the host does not expose resolved identity, record it as unknown. Access/quota errors remain BLOCKED/ERROR; stop additional dispatches on quota or access errors and keep the planned missing rows visible. Do not silently retry with another model or ask for an API key.
7. Generate `audit.py report` and explain differences separately for each model. Distinguish content benefit within a model from descriptive differences between models; neither proves broad model superiority. Unknown identity, contamination or incomplete execution keeps the recommendation inconclusive.

The result is two **model-specific groups of subagents**, not two agents guessing what the other models would answer. A host without model-selectable fresh subagents can receive a NOT EXECUTED plan; this Skill cannot create an unavailable host capability.
