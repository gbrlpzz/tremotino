# Tremotino MCP Setup

Tremotino exposes a local stdio MCP server. It stores durable data in:

```text
~/Documents/Tremotino/Vault
```

Agents should use `propose_note` and `propose_update` for durable memory changes. Those tools create Markdown files in the review queue; the macOS app is where proposals are approved or rejected.

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

Use the same command and environment when registering a local stdio MCP server:

```sh
python3 "/Users/gabriele/Documents/New project 3/mcp/tremotino_mcp.py"
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
