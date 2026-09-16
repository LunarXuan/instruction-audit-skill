# Source publication

Run `python -m unittest discover -s tests -v` and validate the Skill folder before packaging. Include `skills/instruction-audit` intact, README files, examples, tests, license and validation records. Exclude local trial responses, credentials and private instruction files.

Create a GitHub repository named `instruction-audit-skill` in the chosen account, then commit and push the source using the actual remote URL. Suggested description: **Audit instruction value using your agent host's models, without a separate API key.** Suggested topics: `agent-skills`, `agents-md`, `evaluation`, `codex`.

The installed unit is `skills/instruction-audit`; the repository is the distribution and development package. There is no npm package or API service to deploy. Do not promise compatibility with a host until its dispatch and context-isolation path has been exercised.

Review the validation record before a v0.3.0 source release. Publishing is a separate action; this package does not create a remote repository, attach credentials or publish automatically.
