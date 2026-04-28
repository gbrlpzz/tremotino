# Tremotino Vault Types

Tremotino keeps private operating context in a local Markdown vault. The public repository contains only code and generic templates.

## Types

- `workflow`: reusable agent workflow with inputs, steps, writable paths, and expected output.
- `prompt`: system prompts, tone prompts, writing style guides, and client adapters.
- `profile`: working preferences, collaboration defaults, recurring constraints, and durable self-context.
- `directory`: manual registry of local folders with purpose, privacy, and allowed scan/edit policy.
- `codex_job`: queued or completed Codex CLI job plus artifacts.
- `gold`: refined reusable context spun from raw notes, folders, or agent outputs.

The app seeds private starter prompts for shared operating behavior, Codex, Claude, system prompt storage, and writing style guidance. These are vault files, not public repository data.

## Job Artifacts

A Codex job folder contains:

- `job.md`
- `prompt.md`
- `events.jsonl`
- `final.md`
- `pre_snapshot.txt`
- `post_snapshot.txt`

Jobs are private vault data and should not be committed to this repository.
