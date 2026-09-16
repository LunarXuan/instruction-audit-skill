# Validation record — 2026-09-16

Documentation refresh: independent English and Chinese READMEs now include four localized PNG illustrations. All four were visually inspected for readable labels and clipping. Evidence images reference the existing two-child smoke record; no new model-performance numbers were generated. Local documentation/image links were checked before repackaging. Runtime code was unchanged in this documentation update.

0.3.0 update: 23 tests, 22 passed and one Windows symlink-permission skip. New checks cover explicit Skill/AGENTS targets, target-only original-condition injection, missing/empty targets, telemetry provenance/units/finite values, unknown metrics, mixed-unit aggregation and compatibility with old records. These checks do not claim that the host exposes thinking time or per-run subscription quota. No new live two-model Skill evaluation was performed in this update.

0.2.0 update: 16 helper tests run, 15 passed and one symlink test skipped on Windows. The new builder was checked for model selection, fresh child arguments, hidden expected answers, unavailable/duplicate models, call limits and no overwrite. These are offline orchestration checks; no new two-model live comparison was run for this update.

The package is an installable Skill plus an offline Python helper, not a provider API application. Validation is recorded separately for helper behavior and host execution.

- Skill frontmatter and resource structure checked with the Skill Creator validator.
- Local `codex login status` confirms ChatGPT authentication is available in the development environment; credential contents were not accessed.
- Host documentation checked for subscription authentication and Skill discovery locations. Host capabilities remain version/account dependent.

- Python helper: 13 tests run; 12 passed and 1 symlink test skipped because this Windows account could not create a symlink. Tests cover answer separation, missing/blocked/error/synthetic rows, unknown identity, contamination, reused sessions, local assertions, limits, no overwrite and damaged manifests.
- Real host dispatch: two fresh native children (`fork_turns: none`), one with the optional instruction and one without, each answered the arithmetic question with `10`. No API key was supplied; no solver tools were used. See [captured responses](examples/host-smoke-responses.json) and [locally generated report](examples/host-smoke-report.md).
- The dispatch tool did not expose resolved backend model identity. Both records therefore use unknown identity and the report is **INCONCLUSIVE**. This is a tiny transport/recording check, not a cross-model efficacy experiment. Actual dispatched text omitted the helper's section headings; the evidence file discloses that difference.
- Fresh children did not inherit the parent conversation. No claim of OS-level isolation is made, and global host instructions were not removed. The toy optional sentence was supplied only in its assigned condition.
- Independent forward-check with a host lacking fresh sessions and CLI: the reviewing agent followed the Skill, produced static suggestions labeled NOT EXECUTED / INCONCLUSIVE, preserved mandatory instructions and did not request a key or invent trials.
- Extracted the standalone install ZIP and checked the five-file Skill package with skill-smoke 0.2.0: PASS, including its relative references. The helper's four-trial example prepared successfully without model calls. Rechecked local documentation links before packaging.

Not verified: automatic Skill discovery after installation, other agent hosts, actual old/new-model comparison, or hosted Linux/macOS CI. No cross-model effectiveness claim follows from this validation.
