#!/usr/bin/env python3
"""Minimal local stdio MCP server for Tremotino.

The vault is Markdown-first. This server never writes durable memory directly;
write tools create proposals in the review queue.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import sys
from pathlib import Path
from typing import Any


HOME = Path.home()
VAULT = Path(
    os.environ.get(
        "TREMOTINO_VAULT",
        os.environ.get("AGENT_WORKBENCH_VAULT", HOME / "Documents" / "Tremotino" / "Vault"),
    )
)
REVIEW = VAULT / "Review Queue"
INBOX = VAULT / "Inbox"
PROJECTS = VAULT / "Projects"
RUNBOOKS = VAULT / "Runbooks"


TOOLS = [
    {
        "name": "search",
        "description": "Search Markdown notes in the Tremotino vault.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "fetch",
        "description": "Fetch a Markdown note by absolute path or title substring.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    {
        "name": "propose_note",
        "description": "Create a review-queue proposal for a new durable note.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "content": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["title", "content"],
        },
    },
    {
        "name": "propose_update",
        "description": "Create a review-queue proposal to update an existing memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "target": {"type": "string"},
                "content": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["target", "content"],
        },
    },
    {
        "name": "build_project_context",
        "description": "Assemble a compact context bundle for a project query.",
        "inputSchema": {
            "type": "object",
            "properties": {"query": {"type": "string"}},
            "required": ["query"],
        },
    },
    {
        "name": "list_projects",
        "description": "List known project memory files.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "list_runbooks",
        "description": "List available Tremotino runbooks.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "run_runbook_dry_run",
        "description": "Return the command preview for a runbook without executing it.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
]


def ensure_dirs() -> None:
    for directory in (VAULT, REVIEW, INBOX, PROJECTS, RUNBOOKS):
        directory.mkdir(parents=True, exist_ok=True)


def slugify(value: str) -> str:
    value = value.lower().strip()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    return value.strip("-") or "note"


def markdown_files() -> list[Path]:
    if not VAULT.exists():
        return []
    return sorted(VAULT.rglob("*.md"))


def title_for(path: Path, content: str | None = None) -> str:
    content = content if content is not None else path.read_text(encoding="utf-8", errors="ignore")
    for line in content.splitlines():
        if line.startswith("title:"):
            return line.split(":", 1)[1].strip().strip('"')
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def text_response(text: str) -> dict[str, Any]:
    return {"content": [{"type": "text", "text": text}]}


def search(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query", "")).lower()
    matches = []
    for path in markdown_files():
        content = path.read_text(encoding="utf-8", errors="ignore")
        haystack = f"{path.name}\n{content}".lower()
        if query in haystack:
            matches.append({
                "title": title_for(path, content),
                "path": str(path),
                "excerpt": re.sub(r"\s+", " ", content)[:300],
            })
    return text_response(json.dumps(matches[:20], indent=2))


def fetch(args: dict[str, Any]) -> dict[str, Any]:
    identifier = str(args.get("id", ""))
    candidate = Path(identifier).expanduser()
    if candidate.exists() and candidate.is_file():
        return text_response(candidate.read_text(encoding="utf-8", errors="ignore"))

    lowered = identifier.lower()
    for path in markdown_files():
        content = path.read_text(encoding="utf-8", errors="ignore")
        if lowered in title_for(path, content).lower() or lowered in str(path).lower():
            return text_response(content)
    return text_response(f"No note found for {identifier}")


def write_proposal(title: str, content: str, source: str) -> Path:
    ensure_dirs()
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = REVIEW / f"{stamp}-{slugify(title)}.md"
    safe_title = title.replace('"', '\\"')
    safe_source = source.replace('"', '\\"')
    body = f"""---
title: "{safe_title}"
type: proposal
status: pending
source: "{safe_source}"
created_at: {dt.datetime.now(dt.timezone.utc).isoformat()}
---

# {title}

{content}
"""
    path.write_text(body, encoding="utf-8")
    return path


def propose_note(args: dict[str, Any]) -> dict[str, Any]:
    path = write_proposal(
        str(args.get("title", "Untitled Proposal")),
        str(args.get("content", "")),
        str(args.get("source", "mcp-agent")),
    )
    return text_response(f"Proposal created: {path}")


def propose_update(args: dict[str, Any]) -> dict[str, Any]:
    target = str(args.get("target", "unknown target"))
    content = f"Target: {target}\n\n{args.get('content', '')}"
    path = write_proposal(f"Update proposal for {target}", content, str(args.get("source", "mcp-agent")))
    return text_response(f"Update proposal created: {path}")


def build_project_context(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query", "")).lower()
    snippets = []
    for path in markdown_files():
        content = path.read_text(encoding="utf-8", errors="ignore")
        if query in str(path).lower() or query in content.lower():
            snippets.append(f"## {title_for(path, content)}\nPath: {path}\n\n{content[:1200]}")
    return text_response("\n\n---\n\n".join(snippets[:8]) or f"No project context found for {query}")


def list_projects(_: dict[str, Any]) -> dict[str, Any]:
    items = []
    for path in PROJECTS.glob("*.md") if PROJECTS.exists() else []:
        items.append({"title": title_for(path), "path": str(path)})
    return text_response(json.dumps(items, indent=2))


def list_runbooks(_: dict[str, Any]) -> dict[str, Any]:
    static = [
        {"id": "rebuild-index", "title": "Rebuild Index", "dry_run": "tremotino rebuild-index"},
        {"id": "scan-projects", "title": "Scan Known Projects", "dry_run": "tremotino scan-projects --dry-run"},
        {"id": "registry-refresh", "title": "Refresh MCP Registry", "dry_run": "tremotino registry-refresh"},
    ]
    return text_response(json.dumps(static, indent=2))


def run_runbook_dry_run(args: dict[str, Any]) -> dict[str, Any]:
    runbook_id = str(args.get("id", ""))
    commands = {
        "rebuild-index": "tremotino rebuild-index",
        "scan-projects": "tremotino scan-projects --dry-run",
        "registry-refresh": "tremotino registry-refresh",
    }
    return text_response(commands.get(runbook_id, f"Unknown runbook: {runbook_id}"))


CALLS = {
    "search": search,
    "fetch": fetch,
    "propose_note": propose_note,
    "propose_update": propose_update,
    "build_project_context": build_project_context,
    "list_projects": list_projects,
    "list_runbooks": list_runbooks,
    "run_runbook_dry_run": run_runbook_dry_run,
}


def handle(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    message_id = message.get("id")

    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": message_id,
            "result": {
                "protocolVersion": "2025-11-25",
                "capabilities": {"tools": {}, "resources": {}, "prompts": {}},
                "serverInfo": {"name": "tremotino", "version": "0.1.0"},
            },
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": message_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params", {})
        name = params.get("name")
        args = params.get("arguments", {})
        if name in CALLS:
            return {"jsonrpc": "2.0", "id": message_id, "result": CALLS[name](args)}
        return {"jsonrpc": "2.0", "id": message_id, "error": {"code": -32601, "message": f"Unknown tool {name}"}}
    if method == "resources/list":
        resources = [
            {"uri": "memory://vault", "name": "Vault", "description": str(VAULT), "mimeType": "text/markdown"},
            {"uri": "review://queue", "name": "Review Queue", "description": str(REVIEW), "mimeType": "text/markdown"},
            {"uri": "runbook://all", "name": "Runbooks", "description": "Available dry-run runbooks", "mimeType": "application/json"},
        ]
        return {"jsonrpc": "2.0", "id": message_id, "result": {"resources": resources}}
    if method == "prompts/list":
        prompts = [
            {"name": "project_briefing", "description": "Brief an agent on a project from local memory."},
            {"name": "application_draft", "description": "Draft a grant/application answer from durable context."},
            {"name": "workflow_handoff", "description": "Create a concise handoff for a workflow run."},
        ]
        return {"jsonrpc": "2.0", "id": message_id, "result": {"prompts": prompts}}

    if message_id is None:
        return None
    return {"jsonrpc": "2.0", "id": message_id, "error": {"code": -32601, "message": f"Unknown method {method}"}}


def main() -> None:
    ensure_dirs()
    for line in sys.stdin:
        try:
            message = json.loads(line)
            response = handle(message)
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
        except Exception as exc:  # keep stdio server alive for client debugging
            error = {"jsonrpc": "2.0", "id": None, "error": {"code": -32000, "message": str(exc)}}
            sys.stdout.write(json.dumps(error) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
