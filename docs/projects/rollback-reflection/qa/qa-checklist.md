# QA Checklist — Rollback Reflection

> Use this checklist whenever validating updates to the rollback reflection project or the consolidated open-task index.

## Metadata
- **Commit**: `<hash>`
- **Environment**: `<local>` (expect Apple Silicon + MLX toolchain)
- **Tester**: `<name>`
- **Date**: `<YYYY-MM-DD>`

## Pre-flight
- [ ] Session log added under `docs/projects/rollback-reflection/sessions/`
- [ ] `tasks.md` updated to reference any new/closed items
- [ ] `docs/open-tasks.md` regenerated (if backlog changed)

## Validation Steps
1. **Rollback notes**
   - [ ] Latest session clearly states commit hash and observations.
   - [ ] Missing components or regressions are captured under “Findings”.
2. **Consolidated backlog**
   - [ ] Each project listed in `docs/projects/` appears in `docs/open-tasks.md`.
   - [ ] Task IDs/titles match their source files.
   - [ ] Any ownership/priority info is preserved where available.
3. **Cross-references**
   - [ ] Links or file paths in `docs/open-tasks.md` resolve.
   - [ ] Follow-up tasks created in the originating project where necessary.

## Regression Notes
- Capture any discrepancies (e.g., missing project, stale priority) and log them in `tasks.md`.

## Sign-off
- ✅ / ⚠️ / ❌  — *Tester signature*
