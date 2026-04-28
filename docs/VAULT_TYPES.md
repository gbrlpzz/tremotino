# Tremotino Vault Types

Tremotino keeps private operating context in a local Markdown vault. The public repository contains only code and generic templates.

## Types

- `workflow`: reusable agent workflow with inputs, steps, writable paths, and expected output.
- `prompt`: system prompts, tone prompts, writing style guides, and client adapters.
- `profile`: working preferences, collaboration defaults, recurring constraints, and durable self-context.
- `directory`: manual registry of local folders with purpose, privacy, and allowed scan/edit policy.
- `skill`: portable agent capability with trigger conditions and bounded instructions.
- `plugin`: curated local Markdown asset pack. No executable code in the first implementation.
- `design_md`: agent-readable `DESIGN.md` file with visual rules and implementation guidance.
- `still`: Markdown sidecar for a local visual reference under `Stills/Files`.
- `context_pack`: assembled bundle definition for profile, prompts, workflows, design, stills, hay, and gold.
- `hay`: disordered raw material, source paths, transcripts, exports, folders, or files to be spun into durable signal by Codex jobs.
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

## Asset Storage

Stills use local media files plus Markdown sidecars:

```text
Vault/Stills/example.md
Vault/Stills/Files/example.png
```

Hay ingestion jobs may reference source files or folders outside the vault. Those paths are treated as read-only raw material by prompt policy; extracted outputs are written back into the private vault.

## Private Git Backup

The vault is allowed to be a separate private Git repository. This is intentionally distinct from the public Tremotino source repository.

Use the macOS Settings backup controls or:

```sh
TREMOTINO_VAULT_REMOTE=git@github.com:gbrlpzz/tremotino-vault.git ./script/backup_vault.sh "Tremotino vault snapshot"
```

Generated indexes remain outside the vault. The vault `.gitignore` only excludes local noise such as `.DS_Store`, temporary files, and `.tremotino-backup`.
