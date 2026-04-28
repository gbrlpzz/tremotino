# Tremotino MCP Setup

Tremotino exposes a local stdio MCP server. It stores durable data in:

```text
~/Documents/Tremotino/Vault
```

Agents should use `propose_note` and `propose_update` for durable memory changes. Those tools create Markdown files in the review queue; the macOS app is where proposals are approved or rejected.

The MCP server at `mcp/tremotino_mcp.py` is a thin adapter over `tremotino_core`, which owns vault paths, migrations, indexing, skill discovery, bibliography operations, job creation, and context assembly.

The vault root stays simple:

```text
Vault/
  Library/   portable durable agent library
  Work/      inbox, hay, review proposals, Codex jobs
  System/    runbooks and local operating files
```

Inside `Library/`, Tremotino groups objects as `Skills/`, `Context/`, `Knowledge/`, and `Assets/`. Default cross-agent skills from `~/.agents/skills` and `~/.codex/skills` are copied into `Library/Skills/<skill-id>/`, and vendored pack skills are surfaced there too, so agents and the app see one installed skill library.

The long-term goal is a personal second brain and research moat hub: reusable claims, source provenance, project evidence, people/institutions, applications, and workflow history should all become queryable through the same cross-agent MCP layer.

## Claude Desktop

Add this server to your Claude Desktop MCP configuration:

```json
{
  "mcpServers": {
    "tremotino": {
      "command": "python3",
      "args": [
        "/Users/gabriele/Documents/New project 3/mcp/tremotino_mcp.py"
      ],
      "env": {
        "TREMOTINO_VAULT": "/Users/gabriele/Documents/Tremotino/Vault",
        "TREMOTINO_SUPPORT": "/Users/gabriele/Library/Application Support/Tremotino"
      }
    }
  }
}
```

## Codex

Print the Codex MCP configuration:

```sh
./script/install_codex_mcp.sh --print
```

Apply it to `~/.codex/config.toml` only when you explicitly want to update the local Codex configuration:

```sh
./script/install_codex_mcp.sh --apply
```

Smoke-test the same stdio MCP path used by Codex:

```sh
./script/test_codex_mcp.sh
```

## Tools

- `search`
- `fetch`
- `list_library`
- `search_library`
- `get_library_item`
- `scan_vault`
- `rebuild_index`
- `migrate_vault`
- `propose_note`
- `propose_update`
- `build_project_context`
- `list_projects`
- `list_runbooks`
- `run_runbook_dry_run`
- `list_workflows`
- `get_workflow`
- `list_prompts`
- `get_prompt_pack`
- `get_operating_profile`
- `list_directories`
- `assemble_context`
- `create_codex_job`
- `list_codex_jobs`
- `get_codex_job`
- `propose_gold`
- `list_skills`
- `sync_cross_agent_skills`
- `get_skill`
- `recommend_skills`
- `compose_workflow`
- `upsert_skill`
- `annotate_skill_usage`
- `list_plugins`
- `get_plugin`
- `list_designs`
- `get_design`
- `list_stills`
- `get_still`
- `list_context_packs`
- `assemble_context_pack`
- `install_plugin_pack_dry_run`
- `list_hay`
- `get_hay`
- `create_spin_job`
- `create_hay_ingestion_job`
- `record_citable_source`
- `annotate_bibliography_entry`
- `annotate_source`
