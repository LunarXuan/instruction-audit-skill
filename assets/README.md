# README illustrations

`workflow-en.png` / `workflow-zh.png` illustrate the coordination design, not a captured application UI. `evidence-en.png` / `evidence-zh.png` summarize the recorded two-child host smoke test in `examples/host-smoke-responses.json` and `examples/host-smoke-report.md`. They explicitly identify its single-task, unknown-model limitations; no cross-model efficacy, time or quota measurement is invented.

Recreate these original code-rendered diagrams with `python scripts/render_readme_assets.py` after installing Pillow in a documentation-only Python environment. The renderer requires a supported CJK font; its source lists Windows, Linux and macOS candidates. Neither Pillow nor a font is required for the installed Skill's runtime. Artwork uses the repository's MIT license.
