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
WORKFLOWS = VAULT / "Workflows"
PROMPTS = VAULT / "Prompts"
PROFILE = VAULT / "Profile"
DIRECTORIES = VAULT / "Directories"
JOBS = VAULT / "Jobs"
PROJECTS = VAULT / "Projects"
RUNBOOKS = VAULT / "Runbooks"
GOLD = VAULT / "Gold"


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
    {"name": "list_workflows", "description": "List typed Tremotino workflow objects.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "get_workflow",
        "description": "Fetch a workflow by title or path.",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {"name": "list_prompts", "description": "List system, tone, writing style, and adapter prompts.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "get_prompt_pack",
        "description": "Fetch shared operating prompt plus optional client adapter and style guide.",
        "inputSchema": {"type": "object", "properties": {"client": {"type": "string"}}, "required": []},
    },
    {"name": "get_operating_profile", "description": "Fetch private operating profile notes.", "inputSchema": {"type": "object", "properties": {}}},
    {"name": "list_directories", "description": "List manually registered directory notes.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "assemble_context",
        "description": "Assemble workflow, prompt pack, profile, directories, and gold context for an agent task.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "task": {"type": "string"},
                "client": {"type": "string"},
                "workflow": {"type": "string"},
            },
            "required": ["task"],
        },
    },
    {
        "name": "create_codex_job",
        "description": "Create a queued Codex CLI job in the private Tremotino vault.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "prompt": {"type": "string"},
                "workflow": {"type": "string"},
                "working_directory": {"type": "string"},
                "writable_paths": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["title", "prompt"],
        },
    },
    {"name": "list_codex_jobs", "description": "List queued and completed Codex jobs.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "get_codex_job",
        "description": "Fetch a Codex job by title or path.",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {
        "name": "propose_gold",
        "description": "Create a gold item from refined reusable context.",
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
]


def ensure_dirs() -> None:
    for directory in (VAULT, REVIEW, INBOX, WORKFLOWS, PROMPTS, PROFILE, DIRECTORIES, JOBS, PROJECTS, RUNBOOKS, GOLD):
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


def frontmatter_value(content: str, key: str) -> str | None:
    for line in content.splitlines():
        if line.startswith(f"{key}:"):
            return line.split(":", 1)[1].strip().strip('"')
    return None


def body_for(content: str) -> str:
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) == 3:
            return parts[2].strip()
    return content


def list_docs(directory: Path) -> list[dict[str, str]]:
    if not directory.exists():
        return []
    items = []
    for path in sorted(directory.glob("*.md")):
        content = path.read_text(encoding="utf-8", errors="ignore")
        items.append({
            "title": title_for(path, content),
            "type": frontmatter_value(content, "type") or "",
            "path": str(path),
            "excerpt": re.sub(r"\s+", " ", body_for(content))[:260],
        })
    return items


def fetch_from(directory: Path, identifier: str) -> str:
    candidate = Path(identifier).expanduser()
    if candidate.exists() and candidate.is_file():
        return candidate.read_text(encoding="utf-8", errors="ignore")
    lowered = identifier.lower()
    for path in sorted(directory.rglob("*.md")) if directory.exists() else []:
        content = path.read_text(encoding="utf-8", errors="ignore")
        if lowered in title_for(path, content).lower() or lowered in str(path).lower():
            return content
    return f"No document found for {identifier}"


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


def list_workflows(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(list_docs(WORKFLOWS), indent=2))


def get_workflow(args: dict[str, Any]) -> dict[str, Any]:
    return text_response(fetch_from(WORKFLOWS, str(args.get("id", ""))))


def list_prompts(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(list_docs(PROMPTS), indent=2))


def get_prompt_pack(args: dict[str, Any]) -> dict[str, Any]:
    client = str(args.get("client", "shared")).lower()
    pieces = []
    for name in ("shared", "style", client):
        for path in sorted(PROMPTS.glob("*.md")) if PROMPTS.exists() else []:
            if name in path.stem.lower() or (name == "style" and "writing" in path.stem.lower()):
                pieces.append(f"## {title_for(path)}\nPath: {path}\n\n{path.read_text(encoding='utf-8', errors='ignore')}")
    return text_response("\n\n---\n\n".join(pieces) or "No prompt pack found.")


def get_operating_profile(_: dict[str, Any]) -> dict[str, Any]:
    pieces = []
    for path in sorted(PROFILE.glob("*.md")) if PROFILE.exists() else []:
        pieces.append(f"## {title_for(path)}\nPath: {path}\n\n{path.read_text(encoding='utf-8', errors='ignore')}")
    return text_response("\n\n---\n\n".join(pieces) or "No operating profile found.")


def list_directories(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(list_docs(DIRECTORIES), indent=2))


def assemble_context(args: dict[str, Any]) -> dict[str, Any]:
    task = str(args.get("task", ""))
    client = str(args.get("client", "codex"))
    workflow_query = str(args.get("workflow", task))
    sections = [
        "# Tremotino Context Bundle",
        f"Task: {task}",
        "## Operating Profile",
        get_operating_profile({})["content"][0]["text"],
        "## Prompt Pack",
        get_prompt_pack({"client": client})["content"][0]["text"],
        "## Workflow",
        fetch_from(WORKFLOWS, workflow_query),
        "## Directories",
        json.dumps(list_docs(DIRECTORIES), indent=2),
        "## Gold Matches",
        build_project_context({"query": task})["content"][0]["text"],
    ]
    return text_response("\n\n".join(sections))


def create_codex_job(args: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    title = str(args.get("title", "Untitled Codex Job"))
    prompt = str(args.get("prompt", ""))
    workflow = str(args.get("workflow", "manual"))
    working_directory = str(args.get("working_directory", VAULT))
    writable_paths = args.get("writable_paths", [str(VAULT)])
    if not isinstance(writable_paths, list):
        writable_paths = [str(writable_paths)]
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = JOBS / f"{stamp}-{slugify(title)}"
    folder.mkdir(parents=True, exist_ok=True)
    job = folder / "job.md"
    safe_title = title.replace('"', '\\"')
    safe_workflow = workflow.replace('"', '\\"')
    safe_working_directory = working_directory.replace('"', '\\"')
    safe_writable_paths = "|".join(map(str, writable_paths)).replace('"', '\\"')
    body = f"""---
title: "{safe_title}"
type: codex_job
status: queued
workflow: "{safe_workflow}"
client: codex
working_directory: "{safe_working_directory}"
sandbox: workspace-write
writable_paths: "{safe_writable_paths}"
created_at: {dt.datetime.now(dt.timezone.utc).isoformat()}
started_at:
finished_at:
exit_code:
---

# {title}

Job artifacts live next to this file.
"""
    job.write_text(body, encoding="utf-8")
    (folder / "prompt.md").write_text(prompt, encoding="utf-8")
    return text_response(f"Codex job queued: {job}")


def list_codex_jobs(_: dict[str, Any]) -> dict[str, Any]:
    items = []
    for job in sorted(JOBS.glob("*/job.md")) if JOBS.exists() else []:
        content = job.read_text(encoding="utf-8", errors="ignore")
        items.append({
            "title": title_for(job, content),
            "status": frontmatter_value(content, "status") or "unknown",
            "workflow": frontmatter_value(content, "workflow") or "",
            "path": str(job),
        })
    return text_response(json.dumps(items, indent=2))


def get_codex_job(args: dict[str, Any]) -> dict[str, Any]:
    return text_response(fetch_from(JOBS, str(args.get("id", ""))))


def propose_gold(args: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    title = str(args.get("title", "Untitled Gold"))
    content = str(args.get("content", ""))
    source = str(args.get("source", "mcp-agent"))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = GOLD / f"{stamp}-{slugify(title)}.md"
    safe_title = title.replace('"', '\\"')
    safe_source = source.replace('"', '\\"')
    body = f"""---
title: "{safe_title}"
type: gold
source: "{safe_source}"
created_at: {dt.datetime.now(dt.timezone.utc).isoformat()}
---

# {title}

{content}
"""
    path.write_text(body, encoding="utf-8")
    return text_response(f"Gold created: {path}")


CALLS = {
    "search": search,
    "fetch": fetch,
    "propose_note": propose_note,
    "propose_update": propose_update,
    "build_project_context": build_project_context,
    "list_projects": list_projects,
    "list_runbooks": list_runbooks,
    "run_runbook_dry_run": run_runbook_dry_run,
    "list_workflows": list_workflows,
    "get_workflow": get_workflow,
    "list_prompts": list_prompts,
    "get_prompt_pack": get_prompt_pack,
    "get_operating_profile": get_operating_profile,
    "list_directories": list_directories,
    "assemble_context": assemble_context,
    "create_codex_job": create_codex_job,
    "list_codex_jobs": list_codex_jobs,
    "get_codex_job": get_codex_job,
    "propose_gold": propose_gold,
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
