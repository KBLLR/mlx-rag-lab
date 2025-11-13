# Task Ledger

Track every task for this project here. Keep the table sorted by priority (top = highest). Move items between sections as they progress.

## Backlog
| ID | Title | Description | Priority | Owner | Research Notes | Notes |
|----|-------|-------------|----------|-------|----------------|-------|
| P-001 | Example task | Flesh out project scope and success criteria | Medium | | | |
## In Progress
| ID | Title | Started | Owner | Notes |
|----|-------|---------|-------|-------|

## Review / QA
| ID | Title | PR / Branch | Reviewer | Notes |
|----|-------|-------------|----------|-------|

## Done
| ID | Title | Completed | Outcome |
|----|-------|-----------|---------|
| RH-002 | Model cache cleanup helper | 2025-11-11 | Added `scripts/clean_models.py` (preview + HF cache subcommands) plus documentation so manifests drive safe deletions. |
| RH-001 | Model metadata manifests | 2025-11-11 | Delivered `scripts/model_manifest.py`, registry scaffold, gitignored manifests folder, and initial Flux manifests. |
| RH-003 | Document HF Hub / macOS resource-tracker workaround | 2025-11-12 | Documented `HF_HUB_DISABLE_PROGRESS_BARS=1` inside `rag.models.model.Model.__init__`, archived the Textual TUI in `archive/tui/`, and noted that Metal still throws `NSRangeException` before the previous lock issue can occur. |

> Add or remove columns as needed, but keep the structure predictable so others can grok status fast.
