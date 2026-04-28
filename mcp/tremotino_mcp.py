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
SKILLS = VAULT / "Skills"
PLUGINS = VAULT / "Plugins"
DESIGN = VAULT / "Design"
STILLS = VAULT / "Stills"
STILL_FILES = STILLS / "Files"
CONTEXT_PACKS = VAULT / "Context Packs"
HAY = VAULT / "Hay"
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
                "source_paths": {"type": "array", "items": {"type": "string"}},
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
    {"name": "list_skills", "description": "List local agent skills with lightweight metadata.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "get_skill",
        "description": "Fetch a skill by title or path.",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {"name": "list_plugins", "description": "List curated local plugin packs.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "get_plugin",
        "description": "Fetch a curated plugin pack by title or path.",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {"name": "list_designs", "description": "List agent-readable DESIGN.md objects.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "get_design",
        "description": "Fetch a DESIGN.md object by title or path.",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {"name": "list_stills", "description": "List still sidecars with media metadata.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "get_still",
        "description": "Fetch a still sidecar by title or path.",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {"name": "list_context_packs", "description": "List assembled-agent context pack definitions.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "assemble_context_pack",
        "description": "Assemble profile, prompts, design, still metadata, directories, and gold for a client.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "client": {"type": "string"},
                "task": {"type": "string"},
            },
            "required": [],
        },
    },
    {
        "name": "install_plugin_pack_dry_run",
        "description": "Preview importing a curated local plugin pack without copying or executing anything.",
        "inputSchema": {
            "type": "object",
            "properties": {"id": {"type": "string"}},
            "required": ["id"],
        },
    },
    {"name": "list_hay", "description": "List raw disordered material ready for signal extraction.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "get_hay",
        "description": "Fetch a raw material item by title or path.",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {
        "name": "create_hay_ingestion_job",
        "description": "Queue a Codex job to extract signal from raw material and spin it into durable Tremotino assets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "goal": {"type": "string"},
                "source_paths": {"type": "array", "items": {"type": "string"}},
                "working_directory": {"type": "string"},
            },
            "required": ["id"],
        },
    },
]


def ensure_dirs() -> None:
    for directory in (
        VAULT,
        REVIEW,
        INBOX,
        WORKFLOWS,
        PROMPTS,
        PROFILE,
        DIRECTORIES,
        SKILLS,
        PLUGINS,
        DESIGN,
        STILLS,
        STILL_FILES,
        CONTEXT_PACKS,
        HAY,
        JOBS,
        PROJECTS,
        RUNBOOKS,
        GOLD,
    ):
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


def list_still_docs() -> list[dict[str, str]]:
    items = list_docs(STILLS)
    for item in items:
        content = Path(item["path"]).read_text(encoding="utf-8", errors="ignore")
        media_path = frontmatter_value(content, "media_path") or inline_value(content, "media_path") or ""
        item["media_path"] = media_path
        item["license_privacy"] = frontmatter_value(content, "license_privacy") or inline_value(content, "license_privacy") or "private"
        item["intended_agent_use"] = inline_value(content, "intended_agent_use") or ""
    return items


def inline_value(content: str, key: str) -> str | None:
    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{key}:"):
            return stripped.split(":", 1)[1].strip().strip('"')
    return None


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
    source_paths = args.get("source_paths", [])
    if not isinstance(source_paths, list):
        source_paths = [str(source_paths)]
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    folder = JOBS / f"{stamp}-{slugify(title)}"
    folder.mkdir(parents=True, exist_ok=True)
    job = folder / "job.md"
    safe_title = title.replace('"', '\\"')
    safe_workflow = workflow.replace('"', '\\"')
    safe_working_directory = working_directory.replace('"', '\\"')
    safe_writable_paths = "|".join(map(str, writable_paths)).replace('"', '\\"')
    safe_source_paths = "|".join(map(str, source_paths)).replace('"', '\\"')
    body = f"""---
title: "{safe_title}"
type: codex_job
status: queued
workflow: "{safe_workflow}"
client: codex
working_directory: "{safe_working_directory}"
sandbox: workspace-write
writable_paths: "{safe_writable_paths}"
source_paths: "{safe_source_paths}"
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
            "source_paths": frontmatter_value(content, "source_paths") or "",
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


def list_skills(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(list_docs(SKILLS), indent=2))


def get_skill(args: dict[str, Any]) -> dict[str, Any]:
    return text_response(fetch_from(SKILLS, str(args.get("id", ""))))


def list_plugins(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(list_docs(PLUGINS), indent=2))


def get_plugin(args: dict[str, Any]) -> dict[str, Any]:
    return text_response(fetch_from(PLUGINS, str(args.get("id", ""))))


def list_designs(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(list_docs(DESIGN), indent=2))


def get_design(args: dict[str, Any]) -> dict[str, Any]:
    return text_response(fetch_from(DESIGN, str(args.get("id", ""))))


def list_stills(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(list_still_docs(), indent=2))


def get_still(args: dict[str, Any]) -> dict[str, Any]:
    return text_response(fetch_from(STILLS, str(args.get("id", ""))))


def list_context_packs(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(list_docs(CONTEXT_PACKS), indent=2))


def assemble_context_pack(args: dict[str, Any]) -> dict[str, Any]:
    client = str(args.get("client", "codex")).lower()
    task = str(args.get("task", ""))
    pack_id = str(args.get("id", task or "default"))
    still_metadata = json.dumps(list_still_docs(), indent=2)
    sections = [
        "# Tremotino Context Pack",
        f"Client: {client}",
        f"Task: {task}",
        "## Pack Definition",
        fetch_from(CONTEXT_PACKS, pack_id),
        "## Operating Profile",
        get_operating_profile({})["content"][0]["text"],
        "## Prompt Pack",
        get_prompt_pack({"client": client})["content"][0]["text"],
        "## Skills",
        json.dumps(list_docs(SKILLS), indent=2),
        "## Design",
        "\n\n---\n\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in sorted(DESIGN.glob("*.md")) if DESIGN.exists()
        ) or "No design files found.",
        "## Still Metadata",
        still_metadata,
        "## Hay",
        json.dumps(list_docs(HAY)[:8], indent=2),
        "## Directories",
        json.dumps(list_docs(DIRECTORIES), indent=2),
        "## Gold Matches",
        build_project_context({"query": task})["content"][0]["text"] if task else json.dumps(list_docs(GOLD)[:8], indent=2),
    ]
    return text_response("\n\n".join(sections))


def install_plugin_pack_dry_run(args: dict[str, Any]) -> dict[str, Any]:
    plugin_id = str(args.get("id", ""))
    plugin = fetch_from(PLUGINS, plugin_id)
    response = {
        "plugin": plugin_id,
        "policy": "dry_run_only_no_executable_code",
        "would_import": [
            "Markdown skills into Skills/",
            "Markdown prompts into Prompts/",
            "Markdown workflows into Workflows/",
            "DESIGN.md files into Design/",
            "context fragments into Context Packs/",
        ],
        "source_preview": plugin[:1200],
    }
    return text_response(json.dumps(response, indent=2))


def list_hay(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(list_docs(HAY), indent=2))


def get_hay(args: dict[str, Any]) -> dict[str, Any]:
    return text_response(fetch_from(HAY, str(args.get("id", ""))))


def create_hay_ingestion_job(args: dict[str, Any]) -> dict[str, Any]:
    hay_id = str(args.get("id", ""))
    goal = str(args.get("goal", "Extract durable signal and spin it into Gold."))
    working_directory = str(args.get("working_directory", VAULT))
    source_paths = args.get("source_paths", [])
    if not isinstance(source_paths, list):
        source_paths = [str(source_paths)]
    expanded_sources = [str(Path(str(path)).expanduser()) for path in source_paths if str(path).strip()]
    hay = fetch_from(HAY, hay_id)
    prompt = f"""You are running from Tremotino.

Spin hay into gold: inspect the provided files or folders as disordered raw material, extract durable signal, and write refined outputs into the Tremotino vault.

Treat source paths as read-only raw material. Do not edit, delete, move, rename, or reformat source files. Write outputs only inside the Tremotino vault.

Goal:
{goal}

Source paths:
{chr(10).join(f"- {path}" for path in expanded_sources) or "- No source paths provided"}

Hay sidecar:
{hay}

Output rules:
- Create Gold items for reusable claims, arguments, summaries, or research signal.
- Create typed prompts, workflows, profile notes, directory notes, or review proposals only when clearly useful.
- Preserve source paths and uncertainty.
- Keep private data in the vault; do not add anything to the public Tremotino repo.
"""
    return create_codex_job({
        "title": f"Spin hay into gold: {hay_id}",
        "workflow": "Hay Ingestion",
        "prompt": prompt,
        "working_directory": working_directory,
        "writable_paths": [str(VAULT)],
        "source_paths": expanded_sources,
    })


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
    "list_skills": list_skills,
    "get_skill": get_skill,
    "list_plugins": list_plugins,
    "get_plugin": get_plugin,
    "list_designs": list_designs,
    "get_design": get_design,
    "list_stills": list_stills,
    "get_still": get_still,
    "list_context_packs": list_context_packs,
    "assemble_context_pack": assemble_context_pack,
    "install_plugin_pack_dry_run": install_plugin_pack_dry_run,
    "list_hay": list_hay,
    "get_hay": get_hay,
    "create_hay_ingestion_job": create_hay_ingestion_job,
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
            {"uri": "skill://all", "name": "Skills", "description": str(SKILLS), "mimeType": "application/json"},
            {"uri": "plugin://all", "name": "Plugin Packs", "description": str(PLUGINS), "mimeType": "application/json"},
            {"uri": "design://all", "name": "Design", "description": str(DESIGN), "mimeType": "application/json"},
            {"uri": "still://all", "name": "Stills", "description": str(STILLS), "mimeType": "application/json"},
            {"uri": "context-pack://all", "name": "Context Packs", "description": str(CONTEXT_PACKS), "mimeType": "application/json"},
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
