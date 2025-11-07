# Project Template

Use this template project to organise work streams, capture tasks, and attach session logs before every commit. Duplicate the folder, rename it to match your initiative (e.g., `docs/projects/3d-experience/`), then keep the following artifacts up to date.

## Folder Structure
- `README.md` — Project overview, scope, success criteria.
- `tasks.md` — Backlog, in-progress items, and done log.
- `sessions/` — Individual session logs (one per work block) using `docs/session-template.md`.

## Getting Started
1. Copy this directory:  
   `cp -R docs/projects/template docs/projects/<your-project-name>`
2. Update the new `README.md` with:
   - Project charter and objectives.
   - Stakeholders / reviewers.
   - Key dependencies.
3. Populate `tasks.md` with the initial backlog and prioritise.
4. For each working session, drop a completed template (see `sessions/README.md`) *before* committing changes.

## Best Practices
- Keep entries concise but descriptive; future contributors should understand context at a glance.
- Link tasks to GitHub issues, tickets, or Notion docs where applicable.
- Reference session IDs in PR descriptions so reviewers can trace decisions quickly.

> Tip: Commit session logs alongside the code they describe to maintain an auditable history.
