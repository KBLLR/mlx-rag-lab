# Launcher Project Task Ledger

Track work that keeps the CLI lab coherent, batch-ready, and documented. Keep the tables sorted by priority.

## Backlog
| ID | Title | Description | Priority | Owner | Notes |
|----|-------|-------------|----------|-------|-------|
| LAU-001 | Ship lab CLI launcher | Create `apps/lab_cli.py` with `rag-batch`, `flux-batch`, `ingest`, and `bench` modes plus path defaults. | High | | |
| LAU-002 | Document path conventions | Record source/output path standards (var/source_docs, models/indexes, outputs/flux, var/prompts, etc.) | Medium | | Keeps docs/LAB_STATUS.md and COMMANDS_MANIFEST aligned. |
| LAU-003 | Add batch-friendly tests | Extend tests/cli/ and tests/flux/ to capture parsing + path handling without touching Metal. | Medium | | |

## In Progress
| ID | Title | Started | Owner | Notes |
|----|-------|---------|-------|-------|
| LAU-004 | Ingestion path flags | Improve `rag.ingestion.create_vdb` to accept `--input-dir`, `--pattern`, `--output-index`. | 2025-11-15 | Codex | CLI plan awaiting flag wiring. |

## Done
| ID | Title | Completed | Outcome |
|----|-------|-----------|---------|
| LAU-000 | Archive CLI-first docs | 2025-11-12 | Added docs/README.md updates + LAB_STATUS entry to capture buttons lab state. |
