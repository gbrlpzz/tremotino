#!/usr/bin/env python3
"""Tremotino stdio MCP adapter.

The implementation lives in tremotino_core. This file only translates JSON-RPC
MCP messages to core commands and returns tool/resource/prompt results.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from tremotino_core import core  # noqa: E402


def schema(properties: Optional[dict[str, Any]] = None, required: Optional[list[str]] = None) -> dict[str, Any]:
    return {"type": "object", "properties": properties or {}, "required": required or []}


TOOLS: list[dict[str, Any]] = [
    {"name": "search", "description": "Search Tremotino Markdown memory.", "inputSchema": schema({"query": {"type": "string"}}, ["query"])},
    {"name": "fetch", "description": "Fetch a Tremotino item by path, title, or identifier.", "inputSchema": schema({"id": {"type": "string"}}, ["id"])},
    {"name": "list_library", "description": "List unified Agent Library items across skills, prompts, workflows, profile, bibliography, design, stills, and gold.", "inputSchema": schema({"type": {"type": "string"}, "query": {"type": "string"}})},
    {"name": "search_library", "description": "Search the disposable SQLite/FTS library index.", "inputSchema": schema({"query": {"type": "string"}, "type": {"type": "string"}}, ["query"])},
    {"name": "get_library_item", "description": "Fetch one unified Agent Library item.", "inputSchema": schema({"id": {"type": "string"}, "type": {"type": "string"}}, ["id"])},
    {"name": "scan_vault", "description": "List vault objects using the current Markdown vault.", "inputSchema": schema({"type": {"type": "string"}})},
    {"name": "rebuild_index", "description": "Rebuild disposable SQLite and JSON indexes from Markdown.", "inputSchema": schema()},
    {"name": "migrate_vault", "description": "Create or apply a migration report for the canonical vault layout.", "inputSchema": schema({"dry_run": {"type": "boolean"}})},
    {"name": "propose_note", "description": "Create a review-queue proposal for a new durable note.", "inputSchema": schema({"title": {"type": "string"}, "content": {"type": "string"}, "source": {"type": "string"}}, ["title", "content"])},
    {"name": "propose_update", "description": "Create a review-queue proposal for an update.", "inputSchema": schema({"target": {"type": "string"}, "content": {"type": "string"}, "source": {"type": "string"}}, ["target", "content"])},
    {"name": "build_project_context", "description": "Assemble compact project context for a query.", "inputSchema": schema({"query": {"type": "string"}}, ["query"])},
    {"name": "list_projects", "description": "List known project memory objects.", "inputSchema": schema()},
    {"name": "list_runbooks", "description": "List runbooks and command previews.", "inputSchema": schema()},
    {"name": "run_runbook_dry_run", "description": "Return a runbook command preview without executing it.", "inputSchema": schema({"id": {"type": "string"}}, ["id"])},
    {"name": "list_workflows", "description": "List workflow objects.", "inputSchema": schema()},
    {"name": "get_workflow", "description": "Fetch a workflow object.", "inputSchema": schema({"id": {"type": "string"}}, ["id"])},
    {"name": "list_prompts", "description": "List prompts and style guides.", "inputSchema": schema()},
    {"name": "get_prompt_pack", "description": "Return prompt-pack metadata for a client.", "inputSchema": schema({"client": {"type": "string"}})},
    {"name": "get_operating_profile", "description": "List operating profile objects.", "inputSchema": schema()},
    {"name": "list_directories", "description": "List registered directories.", "inputSchema": schema()},
    {"name": "list_bibliography", "description": "List native Markdown/BibTeX bibliography entries.", "inputSchema": schema()},
    {"name": "get_bibliography_entry", "description": "Fetch a bibliography entry.", "inputSchema": schema({"id": {"type": "string"}}, ["id"])},
    {"name": "record_citable_source", "description": "Record or update a citable source and optional use annotation.", "inputSchema": schema({"title": {"type": "string"}, "authors": {}, "year": {"type": "string"}, "entry_type": {"type": "string"}, "source_type": {"type": "string"}, "bibtex_key": {"type": "string"}, "doi": {"type": "string"}, "url": {"type": "string"}, "journal": {"type": "string"}, "publisher": {"type": "string"}, "source_path": {"type": "string"}, "bibtex": {"type": "string"}, "used_for": {"type": "string"}, "annotation": {"type": "string"}, "confidence": {"type": "string"}, "agent": {"type": "string"}}, ["title"])},
    {"name": "annotate_bibliography_entry", "description": "Append a use annotation to a bibliography entry.", "inputSchema": schema({"id": {"type": "string"}, "used_for": {"type": "string"}, "annotation": {"type": "string"}, "confidence": {"type": "string"}, "agent": {"type": "string"}}, ["id", "annotation"])},
    {"name": "annotate_source", "description": "Alias for annotating a citable bibliography source.", "inputSchema": schema({"id": {"type": "string"}, "used_for": {"type": "string"}, "annotation": {"type": "string"}, "confidence": {"type": "string"}, "agent": {"type": "string"}}, ["id", "annotation"])},
    {"name": "import_bibtex", "description": "Import BibTeX into native Tremotino bibliography Markdown.", "inputSchema": schema({"content": {"type": "string"}, "source": {"type": "string"}}, ["content"])},
    {"name": "validate_bibliography", "description": "Validate duplicate keys and missing metadata.", "inputSchema": schema()},
    {"name": "create_bibliography_review_job", "description": "Queue a Codex job to review bibliography memory.", "inputSchema": schema({"goal": {"type": "string"}})},
    {"name": "assemble_context", "description": "Assemble context for an agent task.", "inputSchema": schema({"task": {"type": "string"}, "client": {"type": "string"}, "workflow": {"type": "string"}}, ["task"])},
    {"name": "assemble_context_pack", "description": "Assemble a named context pack for Codex, Claude, or another client.", "inputSchema": schema({"id": {"type": "string"}, "client": {"type": "string"}, "task": {"type": "string"}})},
    {"name": "create_codex_job", "description": "Create a queued Codex CLI job.", "inputSchema": schema({"title": {"type": "string"}, "prompt": {"type": "string"}, "workflow": {"type": "string"}, "working_directory": {"type": "string"}, "writable_paths": {"type": "array", "items": {"type": "string"}}, "source_paths": {"type": "array", "items": {"type": "string"}}}, ["title", "prompt"])},
    {"name": "create_spin_job", "description": "Queue a Spin hay-to-gold Codex job from files or folders.", "inputSchema": schema({"title": {"type": "string"}, "goal": {"type": "string"}, "source_paths": {"type": "array", "items": {"type": "string"}}})},
    {"name": "create_hay_ingestion_job", "description": "Queue a Codex job from an existing Hay item.", "inputSchema": schema({"id": {"type": "string"}, "goal": {"type": "string"}, "source_paths": {"type": "array", "items": {"type": "string"}}}, ["id"])},
    {"name": "list_codex_jobs", "description": "List Codex jobs.", "inputSchema": schema()},
    {"name": "get_codex_job", "description": "Fetch a Codex job.", "inputSchema": schema({"id": {"type": "string"}}, ["id"])},
    {"name": "propose_gold", "description": "Create a Gold item from refined reusable context.", "inputSchema": schema({"title": {"type": "string"}, "content": {"type": "string"}, "source": {"type": "string"}}, ["title", "content"])},
    {"name": "list_skills", "description": "List all installed skills in the unified skill library.", "inputSchema": schema()},
    {"name": "get_skill", "description": "Fetch a skill and optionally supporting files.", "inputSchema": schema({"id": {"type": "string"}, "include_references": {"type": "boolean"}}, ["id"])},
    {"name": "recommend_skills", "description": "Recommend skills for a task using lightweight ranking.", "inputSchema": schema({"task": {"type": "string"}, "limit": {"type": "integer"}}, ["task"])},
    {"name": "compose_workflow", "description": "Compose an ordered multi-skill workflow for a task.", "inputSchema": schema({"task": {"type": "string"}, "limit": {"type": "integer"}}, ["task"])},
    {"name": "sync_cross_agent_skills", "description": "Copy ~/.agents/skills and ~/.codex/skills into Tremotino's portable skill library.", "inputSchema": schema()},
    {"name": "upsert_skill", "description": "Create or update a Tremotino skill.", "inputSchema": schema({"id": {"type": "string"}, "title": {"type": "string"}, "content": {"type": "string"}, "source": {"type": "string"}}, ["content"])},
    {"name": "annotate_skill_usage", "description": "Append a usage note to a skill.", "inputSchema": schema({"id": {"type": "string"}, "used_for": {"type": "string"}, "note": {"type": "string"}, "agent": {"type": "string"}}, ["id", "note"])},
    {"name": "list_plugins", "description": "List curated local asset packs.", "inputSchema": schema()},
    {"name": "get_plugin", "description": "Fetch a curated pack.", "inputSchema": schema({"id": {"type": "string"}}, ["id"])},
    {"name": "install_plugin_pack_dry_run", "description": "Preview pack import without executing or copying code.", "inputSchema": schema({"id": {"type": "string"}}, ["id"])},
    {"name": "list_designs", "description": "List DESIGN.md objects.", "inputSchema": schema()},
    {"name": "get_design", "description": "Fetch a DESIGN.md object.", "inputSchema": schema({"id": {"type": "string"}}, ["id"])},
    {"name": "list_stills", "description": "List still sidecars.", "inputSchema": schema()},
    {"name": "get_still", "description": "Fetch a still sidecar.", "inputSchema": schema({"id": {"type": "string"}}, ["id"])},
    {"name": "list_context_packs", "description": "List context pack definitions.", "inputSchema": schema()},
    {"name": "list_hay", "description": "List raw Hay items.", "inputSchema": schema()},
    {"name": "get_hay", "description": "Fetch a Hay item.", "inputSchema": schema({"id": {"type": "string"}}, ["id"])},
]


def text_result(value: Any) -> dict[str, Any]:
    if isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, indent=2, sort_keys=True)
    return {"content": [{"type": "text", "text": text}]}


def response(message_id: Any, result: Any) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "result": result}


def error_response(message_id: Any, code: int, message: str) -> dict[str, Any]:
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": code, "message": message}}


def list_resources() -> dict[str, Any]:
    resources = []
    for skill in core.list_skills({})["skills"]:
        resources.append(
            {
                "uri": f"skill://{skill['id']}/SKILL.md",
                "name": skill["title"],
                "description": skill.get("description") or "Tremotino skill",
                "mimeType": "text/markdown",
            }
        )
    for item in core.list_library({})["items"][:200]:
        resources.append(
            {
                "uri": f"library://{item['id']}",
                "name": item["title"],
                "description": item["type"],
                "mimeType": "text/markdown",
            }
        )
    return {"resources": resources}


def read_resource(uri: str) -> dict[str, Any]:
    if uri.startswith("skill://"):
        rest = uri.removeprefix("skill://")
        parts = rest.split("/", 1)
        skill_id = parts[0]
        file_name = parts[1] if len(parts) > 1 else "SKILL.md"
        skill = core.get_skill({"id": skill_id, "include_references": True})
        if skill.get("error"):
            return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": skill["error"]}]}
        if file_name == "SKILL.md":
            text = skill.get("content", "")
        else:
            text = skill.get("files", {}).get(file_name, "")
        return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": text}]}
    if uri.startswith("library://"):
        item_id = uri.removeprefix("library://")
        item = core.get_object(item_id)
        return {"contents": [{"uri": uri, "mimeType": "text/markdown", "text": item.get("content", json.dumps(item))}]}
    return {"contents": [{"uri": uri, "mimeType": "text/plain", "text": "Unknown resource"}]}


def list_prompts() -> dict[str, Any]:
    prompts = [{"name": f"tremotino:{item['id']}", "description": item["title"]} for item in core.list_objects("prompt")]
    prompts += [{"name": f"skill:{item['id']}", "description": item["title"]} for item in core.list_skills({})["skills"]]
    return {"prompts": prompts}


def get_prompt(name: str, arguments: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    arguments = arguments or {}
    if name.startswith("skill:"):
        skill = core.get_skill({"id": name.removeprefix("skill:"), "include_references": bool(arguments.get("include_references"))})
        text = skill.get("content", json.dumps(skill))
    elif name.startswith("tremotino:"):
        item = core.get_object(name.removeprefix("tremotino:"), "prompt")
        text = item.get("content", json.dumps(item))
    else:
        text = core.assemble_context({"task": arguments.get("task", name), "client": arguments.get("client", "agent")})["content"]
    return {"messages": [{"role": "user", "content": {"type": "text", "text": text}}]}


def handle(message: dict[str, Any]) -> Optional[dict[str, Any]]:
    method = message.get("method")
    message_id = message.get("id")
    params = message.get("params") or {}

    if method == "initialize":
        core.bootstrap({})
        return response(
            message_id,
            {
                "protocolVersion": "2025-11-25",
                "serverInfo": {"name": "tremotino", "version": "0.2.0"},
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
            },
        )
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return response(message_id, {"tools": TOOLS})
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        result = core.dispatch(str(name), arguments)
        return response(message_id, text_result(result))
    if method == "resources/list":
        return response(message_id, list_resources())
    if method == "resources/read":
        return response(message_id, read_resource(str(params.get("uri") or "")))
    if method == "prompts/list":
        return response(message_id, list_prompts())
    if method == "prompts/get":
        return response(message_id, get_prompt(str(params.get("name") or ""), params.get("arguments") or {}))
    return error_response(message_id, -32601, f"Unknown method: {method}")


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            message = json.loads(line)
            reply = handle(message)
        except Exception as exc:
            reply = error_response(None, -32000, str(exc))
        if reply is not None:
            print(json.dumps(reply), flush=True)


if __name__ == "__main__":
    main()
