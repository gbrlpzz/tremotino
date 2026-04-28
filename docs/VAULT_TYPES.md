# Tremotino Vault Types

Tremotino keeps private operating context in a local Markdown vault. The public repository contains only code and generic templates.

## Layout

The vault root is intentionally simple:

```text
Vault/
  Library/   durable portable agent library
  Work/      inbox, hay, review queue, Codex jobs
  System/    runbooks and local operating files
```

Most typed objects live under `Library/`. Volatile work artifacts live under `Work/`.

The re-architected library is grouped by intent:

```text
Vault/Library/
  Skills/      first-class installed skills, one folder per skill
  Context/     prompts, profiles, workflows, directories, context packs
  Knowledge/   bibliography, gold, projects
  Assets/      curated packs, DESIGN.md files, still sidecars and media
```

Generated indexes remain outside the vault at `~/Library/Application Support/Tremotino/`, unless a test sets `TREMOTINO_SUPPORT` to a temporary path.

## Types

- `workflow`: reusable agent workflow with inputs, steps, writable paths, and expected output.
- `prompt`: system prompts, tone prompts, writing style guides, and client adapters.
- `profile`: working preferences, collaboration defaults, recurring constraints, and durable self-context.
- `directory`: manual registry of local folders with purpose, privacy, and allowed scan/edit policy.
- `skill`: portable agent capability with trigger conditions and bounded instructions. Canonical path is `Library/Skills/<skill-id>/SKILL.md`.
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
Vault/Library/Assets/Stills/example.md
Vault/Library/Assets/Stills/Files/example.png
```

Hay ingestion jobs may reference source files or folders outside the vault. Those paths are treated as read-only raw material by prompt policy; extracted outputs are written back into the private vault.

## Migration

Tremotino writes a migration report under `Work/Migration Reports/` before applying canonical layout moves. Migration preserves Markdown source files and moves old direct library folders into the grouped layout.

Vendored pack skills are copied into `Library/Skills/<skill-id>/` with a `TREMOTINO.md` origin sidecar. Supporting files stay inside the skill folder and remain available to MCP resources.

## Private Git Backup

The vault is allowed to be a separate private Git repository. This is intentionally distinct from the public Tremotino source repository.

Use the macOS Settings backup controls or:

```sh
TREMOTINO_VAULT_REMOTE=git@github.com:gbrlpzz/tremotino-vault.git ./script/backup_vault.sh "Tremotino vault snapshot"
```

Generated indexes remain outside the vault. The vault `.gitignore` only excludes local noise such as `.DS_Store`, temporary files, and `.tremotino-backup`.
