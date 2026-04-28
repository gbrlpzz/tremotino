# Tremotino MCP Setup

Tremotino exposes a local stdio MCP server. It stores durable data in:

```text
~/Documents/Tremotino/Vault
```

Agents should use `propose_note` and `propose_update` for durable memory changes. Those tools create Markdown files in the review queue; the macOS app is where proposals are approved or rejected.

The vault root stays simple:

```text
Vault/
  Library/   portable durable context, skills, prompts, packs, bibliography, gold
  Work/      inbox, hay, review proposals, Codex jobs
  System/    runbooks and local operating files
```

Default cross-agent skills from `~/.agents/skills` and `~/.codex/skills` are copied into `Library/Skills/External/` so Tremotino can use and annotate them without breaking the original agent wiring.

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
        "TREMOTINO_VAULT": "/Users/gabriele/Documents/Tremotino/Vault"
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
- `create_hay_ingestion_job`
- `record_citable_source`
- `annotate_bibliography_entry`
