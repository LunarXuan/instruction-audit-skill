# Changelog

## 0.3.0

- Standalone English/Chinese READMEs with localized workflow and real-evidence illustrations, installation instructions and four usage examples.

- Select AGENTS.md, SKILL.md or a Skill directory explicitly with --target.
- Record source-attributed elapsed/thinking time, token usage, quota and public execution summaries when available.
- Require the main model to write per-model retention proposals with quality, efficiency and uncertainty evidence.
- Keep hidden reasoning out of collection and distinguish text evaluation from whole-Skill compatibility.

## 0.2.0

- Construct two user-selected model groups with fresh per-trial native subagent dispatch arguments.
- Validate model capability lists and call limits before preparing a run; never silently substitute models.
- Add behavioral checks for blinded prompts, distinct fresh children and blocked preparation.

## 0.1.0

- Split instruction-value evaluation out of skill-smoke into an installable agent Skill.
- Use host-authenticated fresh sessions; no provider API client or key entry.
- Include a standard-library helper for blinded text prompts, exact-answer checks and conservative reporting.
- Preserve protected instructions; expose unavailable models, unknown identities and contaminated comparisons.
