# Tremotino

Tremotino is a local-first macOS workbench for Markdown memory, project context, and MCP-based agent workflows.

It is designed as a personal second-brain foundation rather than a general notes clone. The app keeps durable knowledge in plain Markdown, exposes a local MCP server for agents, and routes agent-written updates through a review queue before they become part of long-term memory.

## Current status

This repository contains an early SwiftUI prototype. It includes:

- A native macOS app with Inbox, Projects, Review Queue, Runbooks, Registry, and Settings surfaces.
- A Markdown-first vault stored outside the repository by default at `~/Documents/Tremotino/Vault`.
- A disposable generated index stored outside the repository at `~/Library/Application Support/Tremotino/`.
- A local stdio MCP server with search, fetch, proposal, project context, and runbook tools.
- A minimal black-and-white macOS icon.

## Design principles

- Markdown files are the source of truth.
- Generated indexes are disposable and rebuildable.
- Agent writes are proposals by default, not silent durable memory changes.
- Local project ingestion is read-only and creates reviewable updates.
- The public MCP interface should stay small, stable, and client-neutral.
- Private vault data should not be committed to this repository.

## Build and run

Requirements:

- macOS 14 or newer
- Swift 5.9 or newer
- Python 3 for the MCP server

Run the app:

```sh
./script/build_and_run.sh
```

Verify the app launches:

```sh
./script/build_and_run.sh --verify
```

Smoke-test the MCP server:

```sh
./script/smoke_mcp.sh
```

## MCP server

The local MCP server is at:

```text
mcp/tremotino_mcp.py
```

It exposes:

- `search`
- `fetch`
- `propose_note`
- `propose_update`
- `build_project_context`
- `list_projects`
- `list_runbooks`
- `run_runbook_dry_run`

See `docs/MCP_CLIENT_SETUP.md` for client setup notes.

## Data policy

The repository is code-only. Personal vault contents, generated indexes, local SQLite files, and workflow data should remain outside git. The default vault path is intentionally outside the checkout.

## License

MIT
