# Session Logs

Store every working-session log for this project in this directory. Name each file with the start timestamp for easy sorting, e.g.:

- `2025-02-14T09-30-session.md`
- `2025-02-14T14-15-session.md`

## How to Log a Session
1. Copy `docs/session-template.md` into this folder:
   ```bash
   cp docs/session-template.md sessions/2025-02-14T09-30-session.md
   ```
2. Fill in every field:
   - Date, start/end time, elapsed time.
   - Objectives, execution notes, errors, decisions, learnings.
   - Session quote and image prompt.
3. Save before committing any code from that session.

## Linking Sessions to Tasks
- Reference relevant task IDs (from `../tasks.md`) in the “Associated Tasks / Issues” field.
- When closing a task, link the supporting session logs in the task notes.

> Consistent logging keeps reviews tight and gives future contributors a play-by-play of significant changes.
