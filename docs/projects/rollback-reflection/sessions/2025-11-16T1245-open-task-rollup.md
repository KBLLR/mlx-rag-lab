# Cross-Project Task Rollup

## Session Summary
- **Date**: 2025-11-16
- **Start Time**: 12:45
- **End Time**: 13:25
- **Elapsed (HH:MM)**: 00:40
- **Working Title**: Build consolidated `open-tasks.md`
- **Associated Tasks / Issues**: RRB-001

## Objectives
- Enumerate every backlog item living under `docs/projects/*/tasks.md`.
- Create a single canonical `docs/open-tasks.md` so prioritization doesn’t require scanning each project folder.
- Capture any gaps (projects without task files, placeholder rows) while compiling the list.

## Execution Notes
- Entry points: `find docs/projects -name tasks.md`, plus direct reads of `mlx-data-pipeline`, `mlx-rag-setup`, `mlx-setup`, `voice-app`, and `rollback-reflection` task ledgers.
- Key steps performed:
  - Copied the project template into `docs/projects/rollback-reflection` and customized README/tasks/QA (earlier session).
  - Parsed each task table manually, preserving IDs, titles, descriptions, priorities, and owner notes.
  - Built a new `docs/open-tasks.md` grouped by project, highlighting when a project only contains placeholder tasks.
  - Left TODO markers for projects lacking `tasks.md` so future owners know to add them before the next rollup.
- Tests / commands executed: `find`, `cat` for inspection; no runtime/tooling.

## Reflection
- **Errors Encountered**:
  1. None – biggest friction was inconsistent table schemas, handled manually.
- **Decisions Taken**:
  - Present each project’s backlog in its own subsection to preserve context while keeping a single document.
  - Note when data is missing (e.g., app-starter, flux-setup) so the consolidated doc doubles as a gap report.
- **Learnings & Surprises**:
  - Only five projects actually have populated task ledgers today; the rest never moved beyond placeholder folders.
  - Several “Example task” rows still exist (voice-app, template copies), which can now be cleaned up deliberately.

## Next Actions
- Immediate follow-ups:
  - Mark RRB-001 as complete once the new doc is committed.
  - Socialize `docs/open-tasks.md` with maintainers so future changes keep it updated (RRB-002).
- Blockers / dependencies:
  - Need owners for projects lacking task files; otherwise the consolidated doc will keep calling them out.

## Session Quote
> “Plans are valuable when they change.” — Brandolini’s maxim, adapted for roadmap work.

## Post Image Prompt
```
A topo-style map being annotated with bright sticky flags, minimalist flat design, teal and amber palette.
```
