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
import shutil
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
VENDORED_BIBTEXPARSER = REPO_ROOT / "third_party" / "python-bibtexparser"
VENDORED_PYLATEXENC = REPO_ROOT / "third_party" / "pylatexenc"
if VENDORED_PYLATEXENC.exists():
    sys.path.insert(0, str(VENDORED_PYLATEXENC))
if VENDORED_BIBTEXPARSER.exists():
    sys.path.insert(0, str(VENDORED_BIBTEXPARSER))

HOME = Path.home()
VAULT = Path(
    os.environ.get(
        "TREMOTINO_VAULT",
        os.environ.get("AGENT_WORKBENCH_VAULT", HOME / "Documents" / "Tremotino" / "Vault"),
    )
)
LIBRARY = VAULT / "Library"
WORK = VAULT / "Work"
SYSTEM = VAULT / "System"
REVIEW = WORK / "Review"
INBOX = WORK / "Inbox"
WORKFLOWS = LIBRARY / "Workflows"
PROMPTS = LIBRARY / "Prompts"
PROFILE = LIBRARY / "Profile"
DIRECTORIES = LIBRARY / "Directories"
BIBLIOGRAPHY = LIBRARY / "Bibliography"
SKILLS = LIBRARY / "Skills"
PLUGINS = LIBRARY / "Packs"
DESIGN = LIBRARY / "Design"
STILLS = LIBRARY / "Stills"
STILL_FILES = STILLS / "Files"
CONTEXT_PACKS = LIBRARY / "Context Packs"
HAY = WORK / "Hay"
JOBS = WORK / "Jobs"
PROJECTS = LIBRARY / "Projects"
RUNBOOKS = SYSTEM / "Runbooks"
GOLD = LIBRARY / "Gold"

CITABLE_SOURCE_RULE = """Citable source rule:
- When you consult a citable source for drafting, research, design direction, code provenance, or factual support, record it in Tremotino Bibliography.
- Add a use annotation explaining what the source supported and what uncertainty remains.
- Do not invent missing DOI, author, year, publisher, or publication metadata. Mark incomplete metadata for verification.
- For MCP-capable clients, prefer record_citable_source and annotate_bibliography_entry."""


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
    {"name": "list_bibliography", "description": "List BibTeX-backed bibliography entries.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "get_bibliography_entry",
        "description": "Fetch a bibliography entry by title, BibTeX key, or path.",
        "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {
        "name": "record_citable_source",
        "description": "Record or update a citable source in Tremotino bibliography and annotate how the agent used it.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "authors": {"type": ["string", "array"], "items": {"type": "string"}},
                "year": {"type": "string"},
                "entry_type": {"type": "string"},
                "source_type": {"type": "string"},
                "bibtex_key": {"type": "string"},
                "doi": {"type": "string"},
                "url": {"type": "string"},
                "journal": {"type": "string"},
                "publisher": {"type": "string"},
                "source_path": {"type": "string"},
                "bibtex": {"type": "string"},
                "used_for": {"type": "string"},
                "annotation": {"type": "string"},
                "confidence": {"type": "string"},
                "agent": {"type": "string"},
            },
            "required": ["title"],
        },
    },
    {
        "name": "annotate_bibliography_entry",
        "description": "Append a use annotation to an existing bibliography entry.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "used_for": {"type": "string"},
                "annotation": {"type": "string"},
                "confidence": {"type": "string"},
                "agent": {"type": "string"},
            },
            "required": ["id", "annotation"],
        },
    },
    {
        "name": "import_bibtex",
        "description": "Import BibTeX content into native Tremotino bibliography Markdown entries.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "content": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["content"],
        },
    },
    {"name": "validate_bibliography", "description": "Check bibliography entries for duplicate keys and missing metadata.", "inputSchema": {"type": "object", "properties": {}}},
    {
        "name": "create_bibliography_review_job",
        "description": "Queue a Codex job to review and normalize Tremotino bibliography memory.",
        "inputSchema": {
            "type": "object",
            "properties": {"goal": {"type": "string"}},
            "required": [],
        },
    },
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
        "name": "sync_cross_agent_skills",
        "description": "Copy default ~/.agents/skills and ~/.codex/skills into Tremotino's portable skill library without overwriting existing copies.",
        "inputSchema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_skill",
        "description": "Fetch a skill by title or path.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "include_references": {"type": "boolean"},
            },
            "required": ["id"],
        },
    },
    {
        "name": "upsert_skill",
        "description": "Create or update an installed Tremotino skill Markdown file.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "title": {"type": "string"},
                "content": {"type": "string"},
                "source": {"type": "string"},
            },
            "required": ["content"],
        },
    },
    {
        "name": "annotate_skill_usage",
        "description": "Append a dated usage note to an installed skill.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "used_for": {"type": "string"},
                "note": {"type": "string"},
                "agent": {"type": "string"},
            },
            "required": ["id", "note"],
        },
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
        LIBRARY,
        WORK,
        SYSTEM,
        REVIEW,
        INBOX,
        WORKFLOWS,
        PROMPTS,
        PROFILE,
        DIRECTORIES,
        BIBLIOGRAPHY,
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


def bootstrap_layout() -> None:
    ensure_dirs()
    migrate_legacy_layout()
    sync_cross_agent_skills()


def merge_move(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    if destination.exists() and source.is_dir() and destination.is_dir():
        for child in source.iterdir():
            merge_move(child, destination / child.name)
        try:
            source.rmdir()
        except OSError:
            pass
        return
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source), str(destination))


def migrate_legacy_layout() -> None:
    moves = {
        "Inbox": INBOX,
        "Workflows": WORKFLOWS,
        "Prompts": PROMPTS,
        "Profile": PROFILE,
        "Directories": DIRECTORIES,
        "Bibliography": BIBLIOGRAPHY,
        "Skills": SKILLS,
        "Plugins": PLUGINS,
        "Design": DESIGN,
        "Stills": STILLS,
        "Context Packs": CONTEXT_PACKS,
        "Hay": HAY,
        "Jobs": JOBS,
        "Projects": PROJECTS,
        "Review Queue": REVIEW,
        "Runbooks": RUNBOOKS,
        "Gold": GOLD,
    }
    for legacy_name, destination in moves.items():
        source = VAULT / legacy_name
        if source == destination or not source.exists():
            continue
        destination.mkdir(parents=True, exist_ok=True)
        for child in list(source.iterdir()):
            merge_move(child, destination / child.name)
        try:
            source.rmdir()
        except OSError:
            pass


def sync_cross_agent_skills() -> dict[str, Any]:
    ensure_dirs()
    copied: list[str] = []
    sources = {
        "agents": HOME / ".agents" / "skills",
        "codex": HOME / ".codex" / "skills",
    }
    for source_name, source_root in sources.items():
        if not source_root.exists():
            continue
        destination_root = SKILLS / "External" / source_name
        destination_root.mkdir(parents=True, exist_ok=True)
        for child in sorted(source_root.iterdir()):
            if not child.is_dir() or not (child / "SKILL.md").exists():
                continue
            destination = destination_root / child.name
            if not destination.exists():
                shutil.copytree(child, destination)
                copied.append(str(destination))
            context = destination / "TREMOTINO.md"
            if not context.exists():
                context.write_text(f"""---
title: Tremotino Skill Context
type: skill_context
source: {source_name}
source_path: "{child}"
created_at: {dt.datetime.now(dt.timezone.utc).isoformat()}
---

# Tremotino Skill Context

This is Tremotino's portable copy of a cross-agent skill.

## Source
{child}

## Policy
Keep the default external skill wiring usable. Tremotino stores this copy so the skill library is portable, annotatable, and available through MCP even if a future agent client uses a different local convention.
""", encoding="utf-8")
    return {"copied": copied, "sources": {key: str(value) for key, value in sources.items()}}


def sync_cross_agent_skills_tool(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(sync_cross_agent_skills(), indent=2))


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
        if line.startswith("name:"):
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
        if path.name == "skill-template.md":
            continue
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


def list_skill_docs() -> list[dict[str, str]]:
    items: list[dict[str, str]] = []
    for root in (SKILLS, PLUGINS):
        if root.exists():
            for path in sorted(root.rglob("SKILL.md")):
                content = path.read_text(encoding="utf-8", errors="ignore")
                items.append({
                    "title": title_for(path, content),
                    "type": "skill",
                    "path": str(path),
                    "source": skill_source_label(path),
                    "excerpt": re.sub(r"\s+", " ", body_for(content))[:260],
                })
    for item in list_docs(SKILLS):
        item["source"] = "local"
        items.append(item)
    seen: set[str] = set()
    unique: list[dict[str, str]] = []
    for item in items:
        key = item["title"].strip().lower()
        if key and key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return sorted(unique, key=lambda item: (skill_source_priority(item.get("source", "")), item["title"].lower()))


def skill_source_priority(source: str) -> int:
    if source.startswith("external:agents"):
        return 0
    if source.startswith("external:codex"):
        return 1
    if source.startswith("pack:"):
        return 2
    return 3


def skill_source_label(path: Path) -> str:
    try:
        relative = path.relative_to(SKILLS)
        if relative.parts[:1] == ("External",) and len(relative.parts) > 1:
            return f"external:{relative.parts[1]}"
        return "local"
    except ValueError:
        pass
    try:
        relative = path.relative_to(PLUGINS)
        return f"pack:{relative.parts[0]}" if relative.parts else "pack"
    except ValueError:
        return "unknown"


def skill_paths() -> list[Path]:
    paths: list[Path] = []
    if SKILLS.exists():
        paths.extend(sorted(SKILLS.rglob("SKILL.md")))
        paths.extend(sorted(path for path in SKILLS.glob("*.md") if path.name != "skill-template.md"))
    if PLUGINS.exists():
        paths.extend(sorted(PLUGINS.rglob("SKILL.md")))
    seen: set[str] = set()
    unique: list[Path] = []
    for path in paths:
        content = path.read_text(encoding="utf-8", errors="ignore")
        key = title_for(path, content).strip().lower()
        if key and key in seen:
            continue
        seen.add(key)
        unique.append(path)
    return sorted(unique, key=lambda path: (skill_source_priority(skill_source_label(path)), title_for(path).lower()))


def fetch_skill_document(identifier: str, include_references: bool = False) -> str:
    candidate = Path(identifier).expanduser()
    if candidate.exists() and candidate.is_file():
        content = candidate.read_text(encoding="utf-8", errors="ignore")
        return append_skill_companions(candidate, content) if include_references else content

    lowered = identifier.lower()
    for path in skill_paths():
        content = path.read_text(encoding="utf-8", errors="ignore")
        if lowered in title_for(path, content).lower() or lowered in str(path).lower():
            return append_skill_companions(path, content) if include_references else content
    return f"No skill found for {identifier}"


def append_skill_companions(path: Path, content: str) -> str:
    base = path.parent
    companions = []
    for pattern in ("references/*.md", "assets/*.md", "templates/*.md"):
        companions.extend(sorted(base.glob(pattern)))
    if not companions:
        return content
    companion_list = "\n".join(f"- {item}" for item in companions[:40])
    return f"{content}\n\n---\n\n## Tremotino Companion Files\n{companion_list}"


def find_skill_path(identifier: str) -> Path | None:
    candidate = Path(identifier).expanduser()
    if candidate.exists() and candidate.is_file():
        return candidate
    lowered = identifier.lower()
    for path in skill_paths():
        content = path.read_text(encoding="utf-8", errors="ignore")
        if lowered in title_for(path, content).lower() or lowered in str(path).lower():
            return path
    return None


def skill_markdown(title: str, content: str, source: str) -> str:
    if content.lstrip().startswith("---"):
        return content
    safe_title = title.replace('"', '\\"')
    safe_source = source.replace('"', '\\"')
    return f"""---
title: "{safe_title}"
type: skill
source: "{safe_source}"
created_at: {dt.datetime.now(dt.timezone.utc).isoformat()}
---

{content}
"""


def upsert_skill(args: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    identifier = str(args.get("id", "")).strip()
    content = str(args.get("content", "")).strip()
    if not content:
        return text_response(json.dumps({"error": "content is required"}, indent=2))
    title = str(args.get("title", "")).strip()
    path = find_skill_path(identifier) if identifier else None
    created = path is None
    if path is None:
        if not title:
            title = title_for(Path("skill.md"), content)
        path = SKILLS / "Custom" / slugify(title) / "SKILL.md"
    if not title:
        title = title_for(path, content)
    source = str(args.get("source", "mcp-agent")).strip() or "mcp-agent"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(skill_markdown(title, content, source), encoding="utf-8")
    return text_response(json.dumps({
        "path": str(path),
        "created": created,
        "title": title,
    }, indent=2))


def annotate_skill_usage(args: dict[str, Any]) -> dict[str, Any]:
    identifier = str(args.get("id", ""))
    path = find_skill_path(identifier)
    if path is None:
        return text_response(json.dumps({"error": f"No skill found for {identifier}"}, indent=2))
    content = path.read_text(encoding="utf-8", errors="ignore")
    used_for = str(args.get("used_for", "")).strip()
    note = str(args.get("note", "")).strip()
    agent = str(args.get("agent", "mcp-agent")).strip() or "mcp-agent"
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    block = f"- {timestamp}\n  - agent: {agent}"
    if used_for:
        block += f"\n  - used_for: {used_for}"
    block += f"\n  - note: {note}"
    if "## Tremotino Usage Notes" in content:
        content = content.replace("## Tremotino Usage Notes", f"## Tremotino Usage Notes\n{block}\n", 1)
    else:
        content = f"{content.rstrip()}\n\n## Tremotino Usage Notes\n{block}\n"
    path.write_text(content, encoding="utf-8")
    return text_response(json.dumps({"path": str(path), "annotated": True}, indent=2))


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
        {"id": "backup-vault", "title": "Backup Private Vault", "dry_run": './script/backup_vault.sh "Tremotino vault snapshot"'},
    ]
    return text_response(json.dumps(static, indent=2))


def run_runbook_dry_run(args: dict[str, Any]) -> dict[str, Any]:
    runbook_id = str(args.get("id", ""))
    commands = {
        "rebuild-index": "tremotino rebuild-index",
        "scan-projects": "tremotino scan-projects --dry-run",
        "registry-refresh": "tremotino registry-refresh",
        "backup-vault": './script/backup_vault.sh "Tremotino vault snapshot"',
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


def parse_bibtex_entries(content: str) -> list[dict[str, Any]]:
    try:
        import bibtexparser  # type: ignore

        library = bibtexparser.parse_string(content)
        entries = []
        for entry in getattr(library, "entries", []):
            fields = {field.key.lower(): str(field.value) for field in getattr(entry, "fields", [])}
            entries.append({
                "type": str(getattr(entry, "entry_type", "")),
                "key": str(getattr(entry, "key", "")),
                "fields": fields,
                "raw": str(getattr(entry, "raw", "")) or render_bibtex_entry(str(getattr(entry, "entry_type", "")), str(getattr(entry, "key", "")), fields),
            })
        if entries:
            return entries
    except Exception:
        pass

    return fallback_parse_bibtex_entries(content)


def fallback_parse_bibtex_entries(content: str) -> list[dict[str, Any]]:
    entries = []
    pattern = re.compile(r"@(?P<type>[A-Za-z]+)\s*[{(](?P<body>.*?)[})]\s*(?=@|\Z)", re.DOTALL)
    for match in pattern.finditer(content):
        raw = match.group(0).strip()
        body = match.group("body")
        key, _, fields_text = body.partition(",")
        fields: dict[str, str] = {}
        for field_match in re.finditer(r"([A-Za-z0-9_:-]+)\s*=\s*[{\"']?([^,\n{}\"']+)", fields_text):
            fields[field_match.group(1).lower()] = field_match.group(2).strip()
        entries.append({"type": match.group("type").lower(), "key": key.strip(), "fields": fields, "raw": raw})
    return entries


def render_bibtex_entry(entry_type: str, key: str, fields: dict[str, str]) -> str:
    lines = [f"@{entry_type or 'misc'}{{{key},"]
    for field_key, value in fields.items():
        lines.append(f"  {field_key} = {{{value}}},")
    lines.append("}")
    return "\n".join(lines)


def bibliography_title(entry: dict[str, Any]) -> str:
    fields = entry.get("fields", {})
    title = str(fields.get("title") or entry.get("key") or "Untitled Reference")
    year = str(fields.get("year") or fields.get("date") or "")
    return f"{title} ({year})" if year else title


def write_bibliography_entry(entry: dict[str, Any], source: str) -> Path:
    ensure_dirs()
    fields = entry.get("fields", {})
    title = bibliography_title(entry)
    key = str(entry.get("key", "reference"))
    entry_type = str(entry.get("type", "misc"))
    authors = str(fields.get("author") or fields.get("editor") or "")
    year = str(fields.get("year") or fields.get("date") or "")
    doi = str(fields.get("doi") or "")
    url = str(fields.get("url") or "")
    source_path = str(fields.get("source_path") or "")
    raw = str(entry.get("raw") or render_bibtex_entry(entry_type, key, fields))
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = BIBLIOGRAPHY / f"{stamp}-{slugify(key or title)}.md"
    safe = {name: value.replace('"', '\\"') for name, value in {
        "title": title,
        "key": key,
        "entry_type": entry_type,
        "authors": authors,
        "year": year,
        "doi": doi,
        "url": url,
        "source_path": source_path,
        "source": source,
    }.items()}
    body = f"""---
title: "{safe['title']}"
type: bibliography
bibtex_key: "{safe['key']}"
entry_type: "{safe['entry_type']}"
authors: "{safe['authors']}"
year: "{safe['year']}"
doi: "{safe['doi']}"
url: "{safe['url']}"
source_path: "{safe['source_path']}"
source: "{safe['source']}"
created_at: {dt.datetime.now(dt.timezone.utc).isoformat()}
---

# {title}

## Citation Metadata
- bibtex_key: {key}
- entry_type: {entry_type}
- authors: {authors}
- year: {year}
- doi: {doi}
- url: {url}
- source_path: {source_path}
- source: {source}

## Agent Notes
- Verify citation metadata before using in a paper, report, or grant.
- Preserve uncertainty if source metadata is incomplete.

## Use Annotations

## Raw BibTeX
```bibtex
{raw}
```
"""
    path.write_text(body, encoding="utf-8")
    return path


def list_bibliography(_: dict[str, Any]) -> dict[str, Any]:
    return text_response(json.dumps(list_docs(BIBLIOGRAPHY), indent=2))


def get_bibliography_entry(args: dict[str, Any]) -> dict[str, Any]:
    return text_response(fetch_from(BIBLIOGRAPHY, str(args.get("id", ""))))


def normalize_identifier(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"^https?://(dx\.)?doi\.org/", "", text)
    text = re.sub(r"^doi:\s*", "", text)
    text = re.sub(r"https?://", "", text)
    return text.rstrip("/")


def bibliography_field(content: str, key: str) -> str:
    return frontmatter_value(content, key) or inline_value(content, key) or ""


def bibliography_paths() -> list[Path]:
    return sorted(BIBLIOGRAPHY.glob("*.md")) if BIBLIOGRAPHY.exists() else []


def find_bibliography_match(fields: dict[str, Any]) -> tuple[Path | None, str]:
    identifiers = {
        "doi": normalize_identifier(fields.get("doi")),
        "url": normalize_identifier(fields.get("url")),
        "bibtex_key": normalize_identifier(fields.get("bibtex_key") or fields.get("key")),
        "title": normalize_identifier(fields.get("title")),
    }
    for path in bibliography_paths():
        content = path.read_text(encoding="utf-8", errors="ignore")
        existing = {
            "doi": normalize_identifier(bibliography_field(content, "doi")),
            "url": normalize_identifier(bibliography_field(content, "url")),
            "bibtex_key": normalize_identifier(bibliography_field(content, "bibtex_key")),
            "title": normalize_identifier(title_for(path, content)),
        }
        for key in ("doi", "url", "bibtex_key"):
            if identifiers[key] and existing[key] and identifiers[key] == existing[key]:
                return path, key
        if identifiers["title"] and existing["title"] and identifiers["title"] == existing["title"]:
            return path, "title"
    return None, ""


def find_bibliography_path(identifier: str) -> Path | None:
    candidate = Path(identifier).expanduser()
    if candidate.exists() and candidate.is_file():
        return candidate
    lowered = identifier.lower()
    for path in bibliography_paths():
        content = path.read_text(encoding="utf-8", errors="ignore")
        values = [
            title_for(path, content),
            str(path),
            bibliography_field(content, "bibtex_key"),
            bibliography_field(content, "doi"),
            bibliography_field(content, "url"),
        ]
        if any(lowered in value.lower() for value in values if value):
            return path
    return None


def authors_value(value: Any) -> str:
    if isinstance(value, list):
        return " and ".join(str(item).strip() for item in value if str(item).strip())
    return str(value or "").strip()


def source_entry_from_args(args: dict[str, Any]) -> dict[str, Any]:
    bibtex = str(args.get("bibtex", "")).strip()
    if bibtex:
        parsed = parse_bibtex_entries(bibtex)
        if parsed:
            return parsed[0]

    title = str(args.get("title", "Untitled Reference")).strip()
    year = str(args.get("year", "")).strip()
    author_parts = authors_value(args.get("authors")).split()
    title_parts = title.split()
    key_parts = [
        author_parts[-1] if author_parts else "",
        year,
        title_parts[0] if title_parts else "source",
    ]
    key = str(args.get("bibtex_key", "")).strip() or slugify("-".join(part for part in key_parts if part))
    entry_type = str(args.get("entry_type") or args.get("source_type") or "misc").strip().lower()
    entry_type = re.sub(r"[^a-z0-9_-]+", "", entry_type) or "misc"
    fields = {
        "title": title,
        "author": authors_value(args.get("authors")),
        "year": year,
        "doi": str(args.get("doi", "")).strip(),
        "url": str(args.get("url", "")).strip(),
        "journal": str(args.get("journal", "")).strip(),
        "publisher": str(args.get("publisher", "")).strip(),
        "source_path": str(args.get("source_path", "")).strip(),
    }
    fields = {key_: value for key_, value in fields.items() if value}
    return {
        "type": entry_type,
        "key": key,
        "fields": fields,
        "raw": render_bibtex_entry(entry_type, key, fields),
    }


def append_bibliography_annotation(path: Path, args: dict[str, Any]) -> None:
    content = path.read_text(encoding="utf-8", errors="ignore")
    used_for = str(args.get("used_for", "")).strip()
    annotation = str(args.get("annotation", "")).strip()
    confidence = str(args.get("confidence", "")).strip()
    agent = str(args.get("agent", "mcp-agent")).strip()
    timestamp = dt.datetime.now(dt.timezone.utc).isoformat()
    lines = [
        f"- {timestamp}",
        f"  - agent: {agent}",
    ]
    if used_for:
        lines.append(f"  - used_for: {used_for}")
    if annotation:
        lines.append(f"  - annotation: {annotation}")
    if confidence:
        lines.append(f"  - confidence: {confidence}")
    block = "\n".join(lines)
    if "## Use Annotations" in content:
        content = content.replace("## Use Annotations", f"## Use Annotations\n{block}\n", 1)
    else:
        insertion = f"\n\n## Use Annotations\n{block}\n"
        if "## Raw BibTeX" in content:
            content = content.replace("## Raw BibTeX", f"{insertion}\n## Raw BibTeX", 1)
        else:
            content += insertion
    path.write_text(content, encoding="utf-8")


def record_citable_source(args: dict[str, Any]) -> dict[str, Any]:
    entry = source_entry_from_args(args)
    fields = dict(entry.get("fields", {}))
    fields["bibtex_key"] = entry.get("key", "")
    match, matched_by = find_bibliography_match(fields)
    created = match is None
    path = match
    if path is None:
        source = str(args.get("source_path") or args.get("url") or args.get("agent") or "mcp-citable-source")
        path = write_bibliography_entry(entry, source)
    append_bibliography_annotation(path, args)
    return text_response(json.dumps({
        "path": str(path),
        "created": created,
        "matched_by": matched_by or None,
    }, indent=2))


def annotate_bibliography_entry(args: dict[str, Any]) -> dict[str, Any]:
    identifier = str(args.get("id", ""))
    path = find_bibliography_path(identifier)
    if path is None:
        return text_response(json.dumps({"error": f"No bibliography entry found for {identifier}"}, indent=2))
    append_bibliography_annotation(path, args)
    return text_response(json.dumps({"path": str(path), "annotated": True}, indent=2))


def import_bibtex(args: dict[str, Any]) -> dict[str, Any]:
    content = str(args.get("content", ""))
    source = str(args.get("source", "mcp-bibtex-import"))
    paths = [str(write_bibliography_entry(entry, source)) for entry in parse_bibtex_entries(content)]
    return text_response(json.dumps({"imported": len(paths), "paths": paths}, indent=2))


def validate_bibliography(_: dict[str, Any]) -> dict[str, Any]:
    items = list_docs(BIBLIOGRAPHY)
    keys: dict[str, int] = {}
    missing = []
    for item in items:
        content = Path(item["path"]).read_text(encoding="utf-8", errors="ignore")
        key = frontmatter_value(content, "bibtex_key") or item["title"]
        keys[key] = keys.get(key, 0) + 1
        lower = content.lower()
        problems = []
        if "year:" not in lower and "year =" not in lower:
            problems.append("year")
        if "doi:" not in lower and "doi =" not in lower and "url:" not in lower and "url =" not in lower and "http" not in lower:
            problems.append("doi/url")
        if problems:
            missing.append({"title": item["title"], "missing": problems, "path": item["path"]})
    duplicates = [{"key": key, "count": count} for key, count in sorted(keys.items()) if count > 1]
    return text_response(json.dumps({"entries": len(items), "duplicates": duplicates, "missing": missing}, indent=2))


def create_bibliography_review_job(args: dict[str, Any]) -> dict[str, Any]:
    goal = str(args.get("goal", "Review, normalize, and connect bibliography memory to research context."))
    entries = "\n\n---\n\n".join(
        path.read_text(encoding="utf-8", errors="ignore")[:1800]
        for path in sorted(BIBLIOGRAPHY.glob("*.md")) if BIBLIOGRAPHY.exists()
    )
    prompt = f"""You are running from Tremotino.

Treat the bibliography library as first-class research memory. Do not invent metadata. Check duplicate keys, missing DOI/URL/year/author fields, citation integrity, and links to Gold or project context.

{CITABLE_SOURCE_RULE}

Goal:
{goal}

Bibliography:
{entries or "No bibliography entries found."}

Write outputs only inside the Tremotino vault. Use Review proposals for uncertain durable claims.
"""
    return create_codex_job({
        "title": "Review bibliography library",
        "workflow": "Bibliography Management",
        "prompt": prompt,
        "working_directory": str(VAULT),
        "writable_paths": [str(VAULT)],
    })


def assemble_context(args: dict[str, Any]) -> dict[str, Any]:
    task = str(args.get("task", ""))
    client = str(args.get("client", "codex"))
    workflow_query = str(args.get("workflow", task))
    sections = [
        "# Tremotino Context Bundle",
        f"Task: {task}",
        "## Source Use Contract",
        CITABLE_SOURCE_RULE,
        "## Operating Profile",
        get_operating_profile({})["content"][0]["text"],
        "## Prompt Pack",
        get_prompt_pack({"client": client})["content"][0]["text"],
        "## Workflow",
        fetch_from(WORKFLOWS, workflow_query),
        "## Directories",
        json.dumps(list_docs(DIRECTORIES), indent=2),
        "## Bibliography",
        json.dumps(list_docs(BIBLIOGRAPHY)[:12], indent=2),
        "## Gold Matches",
        build_project_context({"query": task})["content"][0]["text"],
    ]
    return text_response("\n\n".join(sections))


def create_codex_job(args: dict[str, Any]) -> dict[str, Any]:
    ensure_dirs()
    title = str(args.get("title", "Untitled Codex Job"))
    prompt = str(args.get("prompt", ""))
    if CITABLE_SOURCE_RULE not in prompt:
        prompt = f"{CITABLE_SOURCE_RULE}\n\n{prompt}"
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
    return text_response(json.dumps(list_skill_docs(), indent=2))


def get_skill(args: dict[str, Any]) -> dict[str, Any]:
    identifier = str(args.get("id", ""))
    include_references = bool(args.get("include_references", False))
    return text_response(fetch_skill_document(identifier, include_references=include_references))


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
        "## Source Use Contract",
        CITABLE_SOURCE_RULE,
        "## Pack Definition",
        fetch_from(CONTEXT_PACKS, pack_id),
        "## Operating Profile",
        get_operating_profile({})["content"][0]["text"],
        "## Prompt Pack",
        get_prompt_pack({"client": client})["content"][0]["text"],
        "## Skills",
        json.dumps(list_skill_docs(), indent=2),
        "## Design",
        "\n\n---\n\n".join(
            path.read_text(encoding="utf-8", errors="ignore")
            for path in sorted(DESIGN.glob("*.md")) if DESIGN.exists()
        ) or "No design files found.",
        "## Still Metadata",
        still_metadata,
        "## Bibliography",
        json.dumps(list_docs(BIBLIOGRAPHY)[:12], indent=2),
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
    "list_bibliography": list_bibliography,
    "get_bibliography_entry": get_bibliography_entry,
    "record_citable_source": record_citable_source,
    "annotate_bibliography_entry": annotate_bibliography_entry,
    "import_bibtex": import_bibtex,
    "validate_bibliography": validate_bibliography,
    "create_bibliography_review_job": create_bibliography_review_job,
    "assemble_context": assemble_context,
    "create_codex_job": create_codex_job,
    "list_codex_jobs": list_codex_jobs,
    "get_codex_job": get_codex_job,
    "propose_gold": propose_gold,
    "list_skills": list_skills,
    "sync_cross_agent_skills": sync_cross_agent_skills_tool,
    "get_skill": get_skill,
    "upsert_skill": upsert_skill,
    "annotate_skill_usage": annotate_skill_usage,
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
        bootstrap_layout()
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
            {"uri": "bibliography://all", "name": "Bibliography", "description": str(BIBLIOGRAPHY), "mimeType": "application/json"},
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
