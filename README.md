# Tremotino

Tremotino is a local-first macOS workbench for Markdown memory, project context, and MCP-based agent workflows.

It is designed as a personal second-brain foundation rather than a general notes clone. The app keeps durable knowledge in plain Markdown, exposes a local MCP server for agents, and routes agent-written updates through a review queue before they become part of long-term memory.

## Current status

This repository contains an early SwiftUI prototype. It includes:

- A native macOS app organized around Capture, Hay to Gold, Review, Agent Hub, and Settings.
- A Markdown-first vault stored outside the repository by default at `~/Documents/Tremotino/Vault`.
- A disposable generated index stored outside the repository at `~/Library/Application Support/Tremotino/`.
- A local stdio MCP server with search, fetch, proposal, project context, and runbook tools.
- A Codex CLI job queue for scoped `codex exec` workflows.
- Typed Markdown vault objects for workflows, prompts, profile, directories, jobs, and gold items.
- Agent assets for skills, curated plugin packs, `DESIGN.md` files, stills, context packs, and hay ingestion.
- Native bibliography management with BibTeX import, editable Markdown reference entries, validation, and MCP tools.
- A minimal black-and-white macOS icon.

## Design principles

- Markdown files are the source of truth.
- Generated indexes are disposable and rebuildable.
- Agent writes are proposals by default, not silent durable memory changes.
- Typed private vault objects can be edited by scoped Codex jobs when launched from the app.
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

Print the Codex MCP configuration:

```sh
./script/install_codex_mcp.sh --print
```

Verify the Codex-facing MCP path:

```sh
./script/test_codex_mcp.sh
```

Smoke-test bibliography MCP import and validation against a temporary vault:

```sh
./script/test_bibliography_mcp.sh
```

Back up the private vault to Git:

```sh
TREMOTINO_VAULT_REMOTE=git@github.com:gbrlpzz/tremotino-vault.git ./script/backup_vault.sh "Tremotino vault snapshot"
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
- workflow, prompt, profile, directory, bibliography, skill, plugin, design, still, hay, context-pack, job, and gold tools

See `docs/MCP_CLIENT_SETUP.md` for client setup notes.

## Codex jobs

Tremotino can queue and run scoped Codex CLI jobs. Job data is written under the private vault, not this repository. Each job stores a prompt, JSONL events, final output, and pre/post vault snapshots.

App-launched jobs use `workspace-write` with explicit writable paths and never use the dangerous no-sandbox mode.

The current runner pins `gpt-5.2` because the installed Codex CLI on this machine rejects newer configured defaults. This should become a user setting once the job launcher matures.

Hay ingestion jobs take selected files or folders as raw source material, instruct Codex to leave those sources untouched, and write extracted signal into private vault objects such as Gold, prompts, workflows, directory notes, or review proposals.

## Data policy

The repository is code-only. Personal vault contents, generated indexes, local SQLite files, and workflow data should remain outside git. The default vault path is intentionally outside the checkout.

The private vault can have its own separate Git history and private remote. Use the Settings backup controls or `script/backup_vault.sh`; do not commit vault contents into this public source repository.

## License

MIT
