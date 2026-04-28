#!/usr/bin/env python3
"""Tremotino local core.

The core is deliberately small and file-first:
- Markdown files are the source of truth.
- SQLite FTS is a rebuildable index.
- Agents can write review proposals, jobs, skills, and bibliography entries
  through explicit tools.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import sqlite3
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional


REPO_ROOT = Path(__file__).resolve().parents[1]
VENDORED_BIBTEXPARSER = REPO_ROOT / "third_party" / "python-bibtexparser"
VENDORED_PYLATEXENC = REPO_ROOT / "third_party" / "pylatexenc"
if VENDORED_PYLATEXENC.exists():
    sys.path.insert(0, str(VENDORED_PYLATEXENC))
if VENDORED_BIBTEXPARSER.exists():
    sys.path.insert(0, str(VENDORED_BIBTEXPARSER))


CITABLE_SOURCE_RULE = """Citable source rule:
- When you consult a citable source for drafting, research, design direction, code provenance, or factual support, record it in Tremotino Bibliography.
- Add a use annotation explaining what the source supported and what uncertainty remains.
- Do not invent missing DOI, author, year, publisher, or publication metadata. Mark incomplete metadata for verification.
- For MCP-capable clients, prefer record_citable_source and annotate_bibliography_entry."""


TYPE_TITLES = {
    "workflow": "Workflow",
    "prompt": "Prompt",
    "profile": "Profile",
    "directory": "Directory",
    "bibliography": "Bibliography",
    "codex_job": "Codex Job",
    "gold": "Gold",
    "skill": "Skill",
    "plugin": "Plugin",
    "design_md": "Design",
    "still": "Still",
    "context_pack": "Context Pack",
    "hay": "Hay",
    "proposal": "Proposal",
    "project": "Project",
    "runbook": "Runbook",
    "inbox": "Inbox",
}


@dataclass(frozen=True)
class TremotinoPaths:
    vault: Path
    support: Path
    library: Path
    work: Path
    system: Path
    context: Path
    knowledge: Path
    assets: Path
    skills: Path
    workflows: Path
    prompts: Path
    profile: Path
    directories: Path
    context_packs: Path
    bibliography: Path
    gold: Path
    projects: Path
    packs: Path
    design: Path
    stills: Path
    still_files: Path
    inbox: Path
    hay: Path
    jobs: Path
    review: Path
    migration_reports: Path
    runbooks: Path
    index_db: Path
    index_json: Path

    @staticmethod
    def defaults() -> "TremotinoPaths":
        home = Path.home()
        vault = Path(
            os.environ.get(
                "TREMOTINO_VAULT",
                os.environ.get("AGENT_WORKBENCH_VAULT", home / "Documents" / "Tremotino" / "Vault"),
            )
        ).expanduser()
        support = Path(
            os.environ.get(
                "TREMOTINO_SUPPORT",
                home / "Library" / "Application Support" / "Tremotino",
            )
        ).expanduser()
        library = vault / "Library"
        work = vault / "Work"
        system = vault / "System"
        context = library / "Context"
        knowledge = library / "Knowledge"
        assets = library / "Assets"
        stills = assets / "Stills"
        return TremotinoPaths(
            vault=vault,
            support=support,
            library=library,
            work=work,
            system=system,
            context=context,
            knowledge=knowledge,
            assets=assets,
            skills=library / "Skills",
            workflows=context / "Workflows",
            prompts=context / "Prompts",
            profile=context / "Profile",
            directories=context / "Directories",
            context_packs=context / "Context Packs",
            bibliography=knowledge / "Bibliography",
            gold=knowledge / "Gold",
            projects=knowledge / "Projects",
            packs=assets / "Packs",
            design=assets / "Design",
            stills=stills,
            still_files=stills / "Files",
            inbox=work / "Inbox",
            hay=work / "Hay",
            jobs=work / "Jobs",
            review=work / "Review",
            migration_reports=work / "Migration Reports",
            runbooks=system / "Runbooks",
            index_db=support / "index.sqlite",
            index_json=support / "index.json",
        )


def paths() -> TremotinoPaths:
    return TremotinoPaths.defaults()


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def timestamp_slug() -> str:
    return dt.datetime.now().strftime("%Y%m%d-%H%M%S")


def slugify(value: str) -> str:
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9_-]+", "-", value)
    value = re.sub(r"-{2,}", "-", value)
    return value.strip("-") or "item"


def escape_yaml(value: Any) -> str:
    text = "" if value is None else str(value)
    return '"' + text.replace("\\", "\\\\").replace('"', '\\"') + '"'


def ensure_dirs(p: Optional[TremotinoPaths] = None) -> None:
    p = p or paths()
    for directory in (
        p.vault,
        p.library,
        p.work,
        p.system,
        p.context,
        p.knowledge,
        p.assets,
        p.skills,
        p.workflows,
        p.prompts,
        p.profile,
        p.directories,
        p.context_packs,
        p.bibliography,
        p.gold,
        p.projects,
        p.packs,
        p.design,
        p.stills,
        p.still_files,
        p.inbox,
        p.hay,
        p.jobs,
        p.review,
        p.migration_reports,
        p.runbooks,
        p.support,
    ):
        directory.mkdir(parents=True, exist_ok=True)


def object_primary_dirs(p: Optional[TremotinoPaths] = None) -> dict[str, Path]:
    p = p or paths()
    return {
        "workflow": p.workflows,
        "prompt": p.prompts,
        "profile": p.profile,
        "directory": p.directories,
        "bibliography": p.bibliography,
        "codex_job": p.jobs,
        "gold": p.gold,
        "skill": p.skills,
        "plugin": p.packs,
        "design_md": p.design,
        "still": p.stills,
        "context_pack": p.context_packs,
        "hay": p.hay,
        "proposal": p.review,
        "project": p.projects,
        "runbook": p.runbooks,
        "inbox": p.inbox,
    }


def object_compat_dirs(kind: str, p: Optional[TremotinoPaths] = None) -> list[Path]:
    p = p or paths()
    legacy_library = {
        "workflow": p.library / "Workflows",
        "prompt": p.library / "Prompts",
        "profile": p.library / "Profile",
        "directory": p.library / "Directories",
        "bibliography": p.library / "Bibliography",
        "gold": p.library / "Gold",
        "plugin": p.library / "Packs",
        "design_md": p.library / "Design",
        "still": p.library / "Stills",
        "context_pack": p.library / "Context Packs",
        "project": p.library / "Projects",
    }
    legacy_root = {
        "workflow": p.vault / "Workflows",
        "prompt": p.vault / "Prompts",
        "profile": p.vault / "Profile",
        "directory": p.vault / "Directories",
        "bibliography": p.vault / "Bibliography",
        "skill": p.vault / "Skills",
        "plugin": p.vault / "Plugins",
        "design_md": p.vault / "Design",
        "still": p.vault / "Stills",
        "context_pack": p.vault / "Context Packs",
        "hay": p.vault / "Hay",
        "codex_job": p.vault / "Jobs",
        "project": p.vault / "Projects",
        "proposal": p.vault / "Review Queue",
        "runbook": p.vault / "Runbooks",
        "gold": p.vault / "Gold",
        "inbox": p.vault / "Inbox",
    }
    dirs = [object_primary_dirs(p)[kind]]
    for candidate in (legacy_library.get(kind), legacy_root.get(kind)):
        if candidate is not None and candidate not in dirs:
            dirs.append(candidate)
    return dirs


def markdown(title: str, kind: str, body: str, extra: Optional[dict[str, Any]] = None) -> str:
    fields = {
        "title": escape_yaml(title),
        "type": kind,
        "created_at": now_iso(),
    }
    if extra:
        for key, value in extra.items():
            fields[key] = escape_yaml(value)
    frontmatter = "\n".join(f"{key}: {value}" for key, value in fields.items())
    return f"---\n{frontmatter}\n---\n\n{body.rstrip()}\n"


def parse_frontmatter(content: str) -> dict[str, str]:
    if not content.startswith("---"):
        return {}
    lines = content.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}
    values: dict[str, str] = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" not in line:
            continue
        key, raw = line.split(":", 1)
        value = raw.strip()
        if len(value) >= 2 and value[0] in ("'", '"') and value[-1] == value[0]:
            value = value[1:-1]
        values[key.strip()] = value
    return values


def body_for(content: str) -> str:
    if not content.startswith("---"):
        return content.strip()
    lines = content.splitlines()
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            return "\n".join(lines[index + 1 :]).strip()
    return content.strip()


def title_for(path: Path, content: Optional[str] = None) -> str:
    content = content if content is not None else safe_read(path)
    frontmatter = parse_frontmatter(content)
    if frontmatter.get("title"):
        return frontmatter["title"]
    if frontmatter.get("name"):
        return frontmatter["name"]
    for line in content.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.stem


def safe_read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def excerpt(content: str, limit: int = 280) -> str:
    text = re.sub(r"\s+", " ", body_for(content)).strip()
    return text[:limit]


def markdown_files(root: Optional[Path] = None) -> list[Path]:
    p = paths()
    root = root or p.vault
    if not root.exists():
        return []
    ignored = {".git", ".tremotino-backup"}
    files: list[Path] = []
    for item in root.rglob("*.md"):
        if any(part in ignored for part in item.parts):
            continue
        files.append(item)
    return sorted(files)


def is_migrated_duplicate(path: Path) -> bool:
    match = re.search(r"-migrated-\d{8}-\d{6}(?=\.md$)", path.name)
    if not match:
        return False
    canonical_name = path.name[: match.start()] + path.suffix
    canonical = path.with_name(canonical_name)
    if not canonical.exists() or not canonical.is_file():
        return False
    return body_for(safe_read(path)).strip() == body_for(safe_read(canonical)).strip()


def detect_type(path: Path, content: Optional[str] = None, p: Optional[TremotinoPaths] = None) -> str:
    p = p or paths()
    content = content if content is not None else safe_read(path)
    frontmatter = parse_frontmatter(content)
    if frontmatter.get("type"):
        return frontmatter["type"]
    if path.name == "SKILL.md":
        return "skill"
    parts = set(path.parts)
    if "Bibliography" in parts:
        return "bibliography"
    if "Gold" in parts:
        return "gold"
    if "Prompts" in parts:
        return "prompt"
    if "Profile" in parts:
        return "profile"
    if "Workflows" in parts:
        return "workflow"
    if "Context Packs" in str(path):
        return "context_pack"
    if "Design" in parts:
        return "design_md"
    if "Stills" in parts:
        return "still"
    if "Hay" in parts:
        return "hay"
    if "Review" in parts or "Review Queue" in str(path):
        return "proposal"
    if "Jobs" in parts:
        return "codex_job"
    if "Projects" in parts:
        return "project"
    if "Runbooks" in parts:
        return "runbook"
    if "Inbox" in parts:
        return "inbox"
    if "Packs" in parts or "Plugins" in parts:
        return "plugin"
    return "note"


def item_record(path: Path, kind: Optional[str] = None) -> dict[str, Any]:
    content = safe_read(path)
    frontmatter = parse_frontmatter(content)
    detected = kind or detect_type(path, content)
    return {
        "id": item_id(path),
        "title": title_for(path, content),
        "type": detected,
        "path": str(path),
        "relative_path": relative_to_vault(path),
        "status": frontmatter.get("status", ""),
        "source": frontmatter.get("source", ""),
        "description": frontmatter.get("description", ""),
        "excerpt": excerpt(content),
        "updated_at": mtime_iso(path),
    }


def item_id(path: Path) -> str:
    if path.name == "SKILL.md":
        return path.parent.name
    return path.stem


def relative_to_vault(path: Path) -> str:
    p = paths()
    try:
        return str(path.relative_to(p.vault))
    except ValueError:
        return str(path)


def mtime_iso(path: Path) -> str:
    try:
        return dt.datetime.fromtimestamp(path.stat().st_mtime, dt.timezone.utc).replace(microsecond=0).isoformat()
    except OSError:
        return ""


def list_objects(kind: Optional[str] = None) -> list[dict[str, Any]]:
    if kind == "skill":
        return list_skills()["skills"]
    if kind:
        files: list[Path] = []
        for directory in object_compat_dirs(kind):
            if not directory.exists():
                continue
            if kind == "codex_job":
                files.extend(sorted(directory.glob("*/job.md")))
            else:
                files.extend(
                    [
                        file
                        for file in sorted(directory.glob("*.md"))
                        if not file.name.startswith(".") and not is_migrated_duplicate(file)
                    ]
                )
        seen: set[Path] = set()
        records: list[dict[str, Any]] = []
        for file in files:
            if file in seen:
                continue
            seen.add(file)
            if file.name in {"skill-template.md", "still-template.md"}:
                continue
            records.append(item_record(file, kind))
        return sorted(records, key=lambda item: (item.get("title") or "").lower())

    files = markdown_files()
    records = []
    for file in files:
        if file.name.startswith("TREMOTINO") or is_migrated_duplicate(file):
            continue
        records.append(item_record(file))
    return sorted(records, key=lambda item: (item["type"], item["title"].lower()))


def list_library(args: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    args = args or {}
    kind = args.get("type")
    query = str(args.get("query", "")).strip().lower()
    records = list_objects(kind)
    if query:
        records = [
            record
            for record in records
            if query in record["title"].lower()
            or query in record["path"].lower()
            or query in record.get("excerpt", "").lower()
        ]
    return {"items": records, "count": len(records)}


def find_item(identifier: str, kind: Optional[str] = None) -> Optional[Path]:
    raw = str(identifier or "").strip()
    if not raw:
        return None
    candidate = Path(raw).expanduser()
    if candidate.exists():
        return candidate
    lowered = raw.lower()
    for record in list_objects(kind):
        fields = [
            record.get("id", ""),
            record.get("title", ""),
            record.get("path", ""),
            record.get("relative_path", ""),
        ]
        if any(lowered == str(field).lower() for field in fields):
            return Path(record["path"])
    for record in list_objects(kind):
        if lowered in record.get("title", "").lower() or lowered in record.get("path", "").lower():
            return Path(record["path"])
    return None


def get_object(identifier: str, kind: Optional[str] = None, include_content: bool = True) -> dict[str, Any]:
    path = find_item(identifier, kind)
    if path is None:
        return {"error": f"Not found: {identifier}"}
    content = safe_read(path)
    record = item_record(path, kind)
    if include_content:
        record["content"] = content
        record["body"] = body_for(content)
    return record


def save_object(args: dict[str, Any]) -> dict[str, Any]:
    kind = str(args.get("type") or args.get("kind") or "note")
    title = str(args.get("title") or f"Untitled {TYPE_TITLES.get(kind, kind)}")
    body = str(args.get("body") or args.get("content") or f"# {title}\n")
    identifier = str(args.get("id") or "")
    if identifier:
        existing = find_item(identifier, kind)
    else:
        existing = None
    target = existing or object_primary_dirs()[kind] / f"{timestamp_slug()}-{slugify(title)}.md"
    target.parent.mkdir(parents=True, exist_ok=True)
    if body.startswith("---"):
        content = body.rstrip() + "\n"
    else:
        content = markdown(title, kind, body)
    target.write_text(content, encoding="utf-8")
    return {"path": str(target), "item": item_record(target, kind)}


def skill_source(path: Path) -> str:
    text = str(path)
    context = path.parent / "TREMOTINO.md"
    if context.exists():
        context_text = safe_read(context).lower()
        if "source: agents" in context_text or "source: \"agents\"" in context_text:
            return "agents"
        if "source: codex" in context_text or "source: \"codex\"" in context_text:
            return "codex"
        if "source: pack" in context_text or "source: \"pack\"" in context_text:
            return "pack"
    if "/.agents/skills/" in text or "External/agents" in text:
        return "agents"
    if "/.codex/skills/" in text or "External/codex" in text:
        return "codex"
    if "/Packs/" in text or "/Assets/Packs/" in text:
        return "pack"
    return "local"


def skill_files() -> list[Path]:
    p = paths()
    roots = [p.skills, p.packs, p.library / "Packs", p.vault / "Skills", p.vault / "Plugins"]
    files: list[Path] = []
    for root in roots:
        if root.exists():
            files.extend(sorted(root.rglob("SKILL.md")))
    seen: set[Path] = set()
    unique: list[Path] = []
    for file in files:
        resolved = file.resolve()
        if resolved in seen:
            continue
        seen.add(resolved)
        unique.append(file)
    return unique


def list_skills(_: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    records = []
    for file in skill_files():
        record = item_record(file, "skill")
        record["source_kind"] = skill_source(file)
        record["skill_id"] = file.parent.name
        record["supporting_files"] = [
            str(path.relative_to(file.parent))
            for path in sorted(file.parent.rglob("*"))
            if path.is_file() and path.name != "SKILL.md" and not path.name.startswith("TREMOTINO-migrated-")
        ][:40]
        records.append(record)
    records = deduplicate_skill_records(records)
    return {"skills": sorted(records, key=lambda item: item["title"].lower()), "count": len(records)}


def deduplicate_skill_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    priority = {"local": 0, "agents": 1, "codex": 2, "pack": 3}
    selected: dict[str, dict[str, Any]] = {}
    for record in records:
        key = str(record.get("title") or record.get("skill_id") or record["path"]).lower()
        existing = selected.get(key)
        record_is_canonical = "/Library/Skills/" in str(record.get("path", ""))
        existing_is_canonical = existing is not None and "/Library/Skills/" in str(existing.get("path", ""))
        if existing is None:
            selected[key] = record
        elif record_is_canonical and not existing_is_canonical:
            selected[key] = record
        elif record_is_canonical == existing_is_canonical and priority.get(str(record.get("source_kind")), 9) < priority.get(str(existing.get("source_kind")), 9):
            selected[key] = record
    return list(selected.values())


def get_skill(args: dict[str, Any]) -> dict[str, Any]:
    identifier = str(args.get("id") or args.get("name") or "")
    path = find_item(identifier, "skill")
    if path is None:
        return {"error": f"Skill not found: {identifier}"}
    content = safe_read(path)
    result = item_record(path, "skill")
    result["content"] = content
    result["body"] = body_for(content)
    if args.get("include_references"):
        result["files"] = {}
        for file in sorted(path.parent.rglob("*")):
            if file.is_file() and file != path and not file.name.startswith("TREMOTINO-migrated-"):
                try:
                    result["files"][str(file.relative_to(path.parent))] = safe_read(file)
                except OSError:
                    continue
    return result


def upsert_skill(args: dict[str, Any]) -> dict[str, Any]:
    title = str(args.get("title") or args.get("id") or "untitled-skill")
    skill_id = slugify(str(args.get("id") or title))
    destination = paths().skills / skill_id
    destination.mkdir(parents=True, exist_ok=True)
    content = str(args.get("content") or "")
    if not content.startswith("---"):
        content = f"---\nname: {skill_id}\ndescription: {escape_yaml(title)}\n---\n\n{content.strip()}\n"
    (destination / "SKILL.md").write_text(content.rstrip() + "\n", encoding="utf-8")
    write_origin_context(destination, str(args.get("source") or "tremotino"), "", "local")
    return get_skill({"id": skill_id})


def annotate_skill_usage(args: dict[str, Any]) -> dict[str, Any]:
    path = find_item(str(args.get("id") or ""), "skill")
    if path is None:
        return {"error": "Skill not found"}
    note = str(args.get("note") or "")
    used_for = str(args.get("used_for") or "unspecified")
    agent = str(args.get("agent") or "agent")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n\n## Tremotino Usage - {now_iso()}\n"
            f"- agent: {agent}\n"
            f"- used_for: {used_for}\n\n{note.strip()}\n"
        )
    return {"path": str(path), "status": "annotated"}


def unique_skill_destination(skill_id: str, source_kind: str) -> Path:
    p = paths()
    base = slugify(skill_id)
    candidate = p.skills / base
    if not candidate.exists():
        return candidate
    context = candidate / "TREMOTINO.md"
    if context.exists() and source_kind in safe_read(context):
        return candidate
    prefixed = p.skills / slugify(f"{source_kind}-{base}")
    return prefixed


def write_origin_context(destination: Path, source: str, upstream_path: str, license_name: str) -> None:
    context = destination / "TREMOTINO.md"
    if context.exists():
        return
    context.write_text(
        markdown(
            "Tremotino Skill Context",
            "skill_context",
            f"""# Tremotino Skill Context

## Origin
- source: {source}
- upstream_path: {upstream_path}
- license: {license_name}
- installed_at: {now_iso()}
- update_policy: manual
- local_edits: allowed

## Policy
This skill is part of the unified Tremotino Agent Library. Supporting files in this folder are available to MCP clients on demand.
""",
            {"source": source, "upstream_path": upstream_path, "license": license_name},
        ),
        encoding="utf-8",
    )


def sync_cross_agent_skills(_: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    ensure_dirs()
    home = Path.home()
    sources = {
        "agents": home / ".agents" / "skills",
        "codex": home / ".codex" / "skills",
    }
    copied: list[str] = []
    for source_kind, source_root in sources.items():
        if not source_root.exists():
            continue
        for child in sorted(source_root.iterdir()):
            if not child.is_dir() or not (child / "SKILL.md").exists():
                continue
            destination = unique_skill_destination(child.name, source_kind)
            if not destination.exists():
                shutil.copytree(child, destination)
                copied.append(str(destination))
            write_origin_context(destination, source_kind, str(child), "local-user-skill")
    return {"copied": copied, "sources": {key: str(value) for key, value in sources.items()}}


def build_migration_plan(p: Optional[TremotinoPaths] = None) -> list[dict[str, str]]:
    p = p or paths()
    plan: list[dict[str, str]] = []

    direct_moves = {
        p.library / "Workflows": p.workflows,
        p.library / "Prompts": p.prompts,
        p.library / "Profile": p.profile,
        p.library / "Directories": p.directories,
        p.library / "Context Packs": p.context_packs,
        p.library / "Bibliography": p.bibliography,
        p.library / "Gold": p.gold,
        p.library / "Projects": p.projects,
        p.library / "Packs": p.packs,
        p.library / "Design": p.design,
        p.library / "Stills": p.stills,
        p.vault / "Inbox": p.inbox,
        p.vault / "Workflows": p.workflows,
        p.vault / "Prompts": p.prompts,
        p.vault / "Profile": p.profile,
        p.vault / "Directories": p.directories,
        p.vault / "Bibliography": p.bibliography,
        p.vault / "Skills": p.skills,
        p.vault / "Plugins": p.packs,
        p.vault / "Design": p.design,
        p.vault / "Stills": p.stills,
        p.vault / "Context Packs": p.context_packs,
        p.vault / "Hay": p.hay,
        p.vault / "Jobs": p.jobs,
        p.vault / "Projects": p.projects,
        p.vault / "Review Queue": p.review,
        p.vault / "Runbooks": p.runbooks,
        p.vault / "Gold": p.gold,
    }

    for source, destination in direct_moves.items():
        if source.exists() and source != destination:
            plan.append(
                {
                    "action": "move_children",
                    "source": str(source),
                    "destination": str(destination),
                    "reason": "canonical vault layout",
                }
            )

    external = p.skills / "External"
    if external.exists():
        for skill in sorted(external.glob("*/*")):
            if skill.is_dir() and (skill / "SKILL.md").exists():
                source_kind = skill.parent.name
                destination = unique_skill_destination(skill.name, source_kind)
                if skill != destination:
                    plan.append(
                        {
                            "action": "move_dir",
                            "source": str(skill),
                            "destination": str(destination),
                            "reason": "flatten external skills into unified Library/Skills",
                        }
                    )

    pack_roots = [p.packs, p.library / "Packs"]
    for root in pack_roots:
        if not root.exists():
            continue
        for skill_file in sorted(root.rglob("SKILL.md")):
            source_dir = skill_file.parent
            if p.skills in source_dir.parents:
                continue
            source_kind = source_dir.name
            destination = unique_skill_destination(source_kind, "pack")
            if not destination.exists():
                plan.append(
                    {
                        "action": "copy_dir",
                        "source": str(source_dir),
                        "destination": str(destination),
                        "reason": "surface vendored pack skill as first-class skill",
                    }
                )

    return plan


def migration_report(plan: list[dict[str, str]], applied: bool) -> str:
    status = "applied" if applied else "dry-run"
    lines = [
        "---",
        f"title: Tremotino Migration Report {timestamp_slug()}",
        "type: migration_report",
        f"status: {status}",
        f"created_at: {now_iso()}",
        "---",
        "",
        f"# Tremotino Migration Report ({status})",
        "",
        f"Planned actions: {len(plan)}",
        "",
    ]
    for item in plan:
        lines.append(f"- {item['action']}: `{item['source']}` -> `{item['destination']}`")
        lines.append(f"  reason: {item['reason']}")
    return "\n".join(lines).rstrip() + "\n"


def merge_move(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and source.is_dir() and destination.is_dir():
        for child in sorted(source.iterdir()):
            merge_move(child, destination / child.name)
        try:
            source.rmdir()
        except OSError:
            pass
        return
    if destination.exists():
        if source.is_file() and destination.is_file():
            try:
                if source.read_bytes() == destination.read_bytes():
                    source.unlink()
                    return
            except OSError:
                pass
        suffix = destination.suffix
        stem = destination.name[: -len(suffix)] if suffix else destination.name
        candidate = destination.with_name(f"{stem}-migrated-{timestamp_slug()}{suffix}")
        counter = 2
        while candidate.exists():
            candidate = destination.with_name(f"{stem}-migrated-{timestamp_slug()}-{counter}{suffix}")
            counter += 1
        shutil.move(str(source), str(candidate))
        return
    shutil.move(str(source), str(destination))


def prune_empty_directories(roots: Iterable[Path]) -> list[str]:
    removed: list[str] = []
    for root in roots:
        if not root.exists() or not root.is_dir():
            continue
        for directory in sorted([path for path in root.rglob("*") if path.is_dir()], key=lambda path: len(path.parts), reverse=True):
            try:
                directory.rmdir()
                removed.append(str(directory))
            except OSError:
                pass
        try:
            root.rmdir()
            removed.append(str(root))
        except OSError:
            pass
    return removed


def copy_dir_without_overwrite(source: Path, destination: Path) -> None:
    if not source.exists():
        return
    if destination.exists():
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)


def surface_pack_skills() -> list[str]:
    p = paths()
    surfaced: list[str] = []
    if not p.packs.exists():
        return surfaced
    for skill_file in sorted(p.packs.rglob("SKILL.md")):
        source_dir = skill_file.parent
        if p.skills in source_dir.parents:
            continue
        destination = unique_skill_destination(source_dir.name, "pack")
        if not destination.exists():
            copy_dir_without_overwrite(source_dir, destination)
            surfaced.append(str(destination))
        write_origin_context(destination, "pack", str(source_dir), "see-upstream")
    return surfaced


def migrate_vault(args: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    args = args or {}
    p = paths()
    ensure_dirs(p)
    plan = build_migration_plan(p)
    dry_run = bool(args.get("dry_run", True))
    report = migration_report(plan, applied=not dry_run)
    report_path = p.migration_reports / f"{timestamp_slug()}-migration-{'dry-run' if dry_run else 'applied'}.md"
    report_path.write_text(report, encoding="utf-8")
    if dry_run:
        return {"dry_run": True, "actions": plan, "report_path": str(report_path)}

    for item in plan:
        source = Path(item["source"])
        destination = Path(item["destination"])
        if item["action"] == "move_children":
            destination.mkdir(parents=True, exist_ok=True)
            if source.exists():
                for child in sorted(source.iterdir()):
                    merge_move(child, destination / child.name)
                try:
                    source.rmdir()
                except OSError:
                    pass
        elif item["action"] == "move_dir":
            merge_move(source, destination)
            write_origin_context(destination, "migrated", item["source"], "unknown")
        elif item["action"] == "copy_dir":
            copy_dir_without_overwrite(source, destination)
            if destination.exists():
                write_origin_context(destination, "pack", item["source"], "see-upstream")
    surfaced = surface_pack_skills()
    legacy_roots = [
        p.library / "Workflows",
        p.library / "Prompts",
        p.library / "Profile",
        p.library / "Directories",
        p.library / "Context Packs",
        p.library / "Bibliography",
        p.library / "Gold",
        p.library / "Projects",
        p.library / "Packs",
        p.library / "Design",
        p.library / "Stills",
        p.skills / "External",
        p.vault / "Inbox",
        p.vault / "Workflows",
        p.vault / "Prompts",
        p.vault / "Profile",
        p.vault / "Directories",
        p.vault / "Bibliography",
        p.vault / "Skills",
        p.vault / "Plugins",
        p.vault / "Design",
        p.vault / "Stills",
        p.vault / "Context Packs",
        p.vault / "Hay",
        p.vault / "Jobs",
        p.vault / "Projects",
        p.vault / "Review Queue",
        p.vault / "Runbooks",
        p.vault / "Gold",
    ]
    removed_empty_dirs = prune_empty_directories(legacy_roots)
    return {
        "dry_run": False,
        "actions": plan,
        "report_path": str(report_path),
        "surfaced_pack_skills": surfaced,
        "removed_empty_dirs": removed_empty_dirs,
    }


def write_seed(path: Path, title: str, kind: str, body: str) -> None:
    if path.exists():
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown(title, kind, body), encoding="utf-8")


def seed_vault() -> None:
    p = paths()
    write_seed(
        p.vault / "README.md",
        "Tremotino Vault",
        "system",
        "# Tremotino Vault\n\nThis folder is the Markdown-first source of truth for Tremotino.\n",
    )
    write_seed(
        p.profile / "how-i-work.md",
        "How I Work",
        "profile",
        "# How I Work\n\n## Collaboration Defaults\n- Prefer direct implementation once the goal is clear.\n- Keep uncertainty visible.\n- Use local authoritative artifacts first.\n",
    )
    write_seed(
        p.prompts / "writing-style-guide.md",
        "Writing Style Guide",
        "prompt",
        "# Writing Style Guide\n\nUse direct, concrete language. Preserve uncertainty and source grounding.\n",
    )
    write_seed(
        p.workflows / "spin-into-gold.md",
        "Spin Into Gold",
        "workflow",
        "# Spin Into Gold\n\nConvert raw notes, folders, transcripts, or agent outputs into durable reusable context with provenance.\n",
    )
    write_seed(
        p.context_packs / "codex-default.md",
        "Codex Default Context Pack",
        "context_pack",
        "# Codex Default Context Pack\n\nIncludes operating profile, style guide, skills, bibliography, and gold context.\n",
    )
    write_seed(
        p.hay / "raw-material-template.md",
        "Raw Material Template",
        "hay",
        "# Raw Material Template\n\n## Raw Material\n\n## Extraction Goal\n\n## Output Preference\nPrefer Gold or review proposals depending on risk.\n",
    )
    skill_template = p.skills / "skill-template" / "SKILL.md"
    if not skill_template.exists():
        skill_template.parent.mkdir(parents=True, exist_ok=True)
        skill_template.write_text(
            "---\nname: skill-template\ndescription: Template for a portable Tremotino skill.\n---\n\n# Skill Template\n\n## When To Use\n\n## Instructions\n",
            encoding="utf-8",
        )
    write_seed(
        p.gold / "README.md",
        "Gold",
        "gold",
        "# Gold\n\nRefined reusable context belongs here.\n",
    )


def bootstrap(args: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    ensure_dirs()
    migration = migrate_vault({"dry_run": False})
    surfaced = surface_pack_skills()
    sync = sync_cross_agent_skills({})
    seed_vault()
    return {"vault": str(paths().vault), "migration": migration, "surfaced_pack_skills": surfaced, "skill_sync": sync}


def rebuild_index(_: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    p = paths()
    ensure_dirs(p)
    files = [
        file
        for file in markdown_files(p.vault)
        if not file.name.startswith("TREMOTINO") and not is_migrated_duplicate(file)
    ]
    records = [item_record(file) for file in files]
    p.index_json.write_text(json.dumps(records, indent=2, sort_keys=True), encoding="utf-8")

    connection = sqlite3.connect(p.index_db)
    try:
        connection.execute("DROP TABLE IF EXISTS docs")
        connection.execute("CREATE TABLE docs (path TEXT PRIMARY KEY, title TEXT, type TEXT, body TEXT, updated_at TEXT)")
        try:
            connection.execute("CREATE VIRTUAL TABLE docs_fts USING fts5(title, body, path, content='docs', content_rowid='rowid')")
            has_fts = True
        except sqlite3.OperationalError:
            has_fts = False
        for file in files:
            content = safe_read(file)
            record = item_record(file)
            cursor = connection.execute(
                "INSERT INTO docs(path, title, type, body, updated_at) VALUES (?, ?, ?, ?, ?)",
                (str(file), record["title"], record["type"], body_for(content), record["updated_at"]),
            )
            if has_fts:
                connection.execute(
                    "INSERT INTO docs_fts(rowid, title, body, path) VALUES (?, ?, ?, ?)",
                    (cursor.lastrowid, record["title"], body_for(content), str(file)),
                )
        connection.commit()
    finally:
        connection.close()
    return {"indexed": len(records), "index_db": str(p.index_db), "index_json": str(p.index_json)}


def search_library(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query") or "").strip()
    kind = args.get("type")
    if not query:
        return list_library({"type": kind})
    p = paths()
    if not p.index_db.exists():
        rebuild_index({})
    results: list[dict[str, Any]] = []
    connection = sqlite3.connect(p.index_db)
    connection.row_factory = sqlite3.Row
    try:
        try:
            rows = connection.execute(
                """
                SELECT docs.path, docs.title, docs.type, snippet(docs_fts, 1, '[', ']', '...', 12) AS snippet
                FROM docs_fts
                JOIN docs ON docs.rowid = docs_fts.rowid
                WHERE docs_fts MATCH ?
                LIMIT 40
                """,
                (query,),
            ).fetchall()
        except sqlite3.OperationalError:
            like = f"%{query.lower()}%"
            rows = connection.execute(
                "SELECT path, title, type, substr(body, 1, 280) AS snippet FROM docs WHERE lower(title) LIKE ? OR lower(body) LIKE ? LIMIT 40",
                (like, like),
            ).fetchall()
        for row in rows:
            if kind and row["type"] != kind:
                continue
            path = Path(row["path"])
            record = item_record(path, row["type"])
            record["snippet"] = row["snippet"]
            results.append(record)
    finally:
        connection.close()
    return {"items": results, "count": len(results)}


def search(args: dict[str, Any]) -> dict[str, Any]:
    return search_library(args)


def fetch(args: dict[str, Any]) -> dict[str, Any]:
    return get_object(str(args.get("id") or ""))


def write_proposal(title: str, content: str, source: str) -> Path:
    p = paths()
    ensure_dirs(p)
    path = p.review / f"{timestamp_slug()}-{slugify(title)}.md"
    body = f"# {title}\n\n{content.strip()}\n"
    path.write_text(markdown(title, "proposal", body, {"status": "pending", "source": source}), encoding="utf-8")
    return path


def propose_note(args: dict[str, Any]) -> dict[str, Any]:
    path = write_proposal(str(args.get("title") or "Untitled proposal"), str(args.get("content") or ""), str(args.get("source") or "agent"))
    return {"path": str(path), "status": "pending"}


def propose_update(args: dict[str, Any]) -> dict[str, Any]:
    title = f"Update: {args.get('target') or 'memory'}"
    path = write_proposal(title, str(args.get("content") or ""), str(args.get("source") or "agent"))
    return {"path": str(path), "status": "pending"}


def list_runbooks(_: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    runbooks = list_objects("runbook")
    defaults = [
        {"id": "rebuild-index", "title": "Rebuild Index", "command": "python3 -m tremotino_core rebuild_index"},
        {"id": "migrate-vault-dry-run", "title": "Migration Dry Run", "command": "python3 -m tremotino_core migrate_vault --json '{\"dry_run\": true}'"},
        {"id": "backup-vault", "title": "Backup Private Vault", "command": "./script/backup_vault.sh \"Tremotino vault snapshot\""},
    ]
    return {"runbooks": defaults + runbooks}


def run_runbook_dry_run(args: dict[str, Any]) -> dict[str, Any]:
    identifier = str(args.get("id") or "")
    for runbook in list_runbooks({})["runbooks"]:
        if identifier in (runbook.get("id"), runbook.get("title")):
            return {"id": identifier, "dry_run": True, "command": runbook.get("command", "manual")}
    return {"id": identifier, "dry_run": True, "command": "manual review required"}


def build_project_context(args: dict[str, Any]) -> dict[str, Any]:
    query = str(args.get("query") or "")
    projects = search_library({"query": query, "type": "project"})["items"][:8]
    gold = search_library({"query": query, "type": "gold"})["items"][:8]
    bibliography = search_library({"query": query, "type": "bibliography"})["items"][:8]
    return {"query": query, "projects": projects, "gold": gold, "bibliography": bibliography}


def assemble_context(args: dict[str, Any]) -> dict[str, Any]:
    task = str(args.get("task") or "")
    client = str(args.get("client") or "agent")
    workflow = str(args.get("workflow") or "")
    sections = [
        f"# Tremotino Context\n\nClient: {client}\nTask: {task}",
        f"## Source Use Contract\n{CITABLE_SOURCE_RULE}",
        objects_section("Operating Profile", list_objects("profile")),
        objects_section("Prompts", list_objects("prompt")),
        objects_section("Workflow", [get_object(workflow, "workflow")] if workflow else list_objects("workflow")[:4]),
        objects_section("Gold", search_library({"query": task, "type": "gold"})["items"][:8]),
        objects_section("Bibliography", search_library({"query": task, "type": "bibliography"})["items"][:8]),
    ]
    return {"client": client, "task": task, "content": "\n\n".join(section for section in sections if section.strip())}


def objects_section(title: str, records: list[dict[str, Any]]) -> str:
    chunks = [f"## {title}"]
    for record in records:
        if record.get("error"):
            continue
        path = Path(record["path"])
        content = safe_read(path)
        chunks.append(f"### {record['title']}\nPath: {path}\n\n{body_for(content)[:1800]}")
    return "\n\n".join(chunks)


def assemble_context_pack(args: dict[str, Any]) -> dict[str, Any]:
    identifier = str(args.get("id") or "codex-default")
    client = str(args.get("client") or "agent")
    task = str(args.get("task") or "")
    pack = get_object(identifier, "context_pack")
    if pack.get("error"):
        pack = {"title": identifier, "path": "", "body": ""}
    content = assemble_context({"task": task or identifier, "client": client})["content"]
    skills = recommend_skills({"task": task or identifier, "limit": 8})["skills"]
    skill_section = ["## Recommended Skills"]
    for skill in skills:
        skill_section.append(f"- {skill['title']} ({skill['id']})")
    full = "\n\n".join(
        [
            f"# Tremotino Context Pack: {pack.get('title', identifier)}",
            f"Client: {client}",
            f"Task: {task}",
            f"Pack path: {pack.get('path', '')}",
            str(pack.get("body") or pack.get("content") or ""),
            "\n".join(skill_section),
            content,
        ]
    )
    return {"id": identifier, "client": client, "task": task, "content": full}


def create_codex_job(args: dict[str, Any]) -> dict[str, Any]:
    p = paths()
    ensure_dirs(p)
    title = str(args.get("title") or "Codex Job")
    workflow = str(args.get("workflow") or "Manual")
    prompt = str(args.get("prompt") or "")
    working_directory = str(args.get("working_directory") or p.vault)
    writable_paths = args.get("writable_paths") or [str(p.vault)]
    source_paths = args.get("source_paths") or []
    folder = p.jobs / f"{timestamp_slug()}-{slugify(title)}"
    folder.mkdir(parents=True, exist_ok=True)
    job_path = folder / "job.md"
    job_body = "# {0}\n\nJob artifacts live next to this file.\n".format(title)
    job_path.write_text(
        markdown(
            title,
            "codex_job",
            job_body,
            {
                "status": "queued",
                "workflow": workflow,
                "client": "codex",
                "working_directory": working_directory,
                "sandbox": "workspace-write",
                "writable_paths": "|".join(map(str, writable_paths)),
                "source_paths": "|".join(map(str, source_paths)),
                "started_at": "",
                "finished_at": "",
                "exit_code": "",
            },
        ),
        encoding="utf-8",
    )
    (folder / "prompt.md").write_text(prompt, encoding="utf-8")
    return {"path": str(job_path), "folder": str(folder), "status": "queued"}


def create_spin_job(args: dict[str, Any]) -> dict[str, Any]:
    source_paths = args.get("source_paths") or args.get("paths") or []
    if isinstance(source_paths, str):
        source_paths = [source_paths]
    goal = str(args.get("goal") or "Extract durable signal from raw material")
    title = str(args.get("title") or "Spin hay into gold")
    p = paths()
    prompt = f"""You are running from Tremotino.

Spin hay into gold: inspect the provided files or folders as disordered raw material, extract durable signal, and write the refined result into the Tremotino vault.

Treat source paths as read-only raw material. Do not edit, delete, move, rename, or reformat source files.

{CITABLE_SOURCE_RULE}

Goal:
{goal}

Source paths:
{chr(10).join('- ' + str(path) for path in source_paths)}

Output rules:
- Create Gold items for reusable claims, arguments, summaries, or research signal.
- Create review proposals for uncertain durable memory.
- Preserve source paths and uncertainty.
- Keep private data in the vault; do not add anything to the public Tremotino repo.
"""
    return create_codex_job(
        {
            "title": title,
            "workflow": "Spin Into Gold",
            "prompt": prompt,
            "working_directory": str(p.vault),
            "writable_paths": [str(p.vault)],
            "source_paths": source_paths,
        }
    )


def create_hay_ingestion_job(args: dict[str, Any]) -> dict[str, Any]:
    identifier = str(args.get("id") or "")
    hay = get_object(identifier, "hay")
    source_paths = args.get("source_paths") or []
    goal = str(args.get("goal") or hay.get("body") or "Extract signal from hay")
    return create_spin_job({"title": f"Spin hay into gold: {hay.get('title', identifier)}", "goal": goal, "source_paths": source_paths})


def list_codex_jobs(_: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return {"jobs": list_objects("codex_job")}


def get_codex_job(args: dict[str, Any]) -> dict[str, Any]:
    return get_object(str(args.get("id") or ""), "codex_job")


def propose_gold(args: dict[str, Any]) -> dict[str, Any]:
    title = str(args.get("title") or "Untitled Gold")
    content = str(args.get("content") or "")
    source = str(args.get("source") or "agent")
    path = object_primary_dirs()["gold"] / f"{timestamp_slug()}-{slugify(title)}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(markdown(title, "gold", f"# {title}\n\n{content}", {"source": source}), encoding="utf-8")
    return {"path": str(path)}


def parse_bibtex_entries(content: str) -> list[dict[str, Any]]:
    try:
        import bibtexparser  # type: ignore

        library = bibtexparser.parse_string(content)
        entries = []
        for block in getattr(library, "blocks", []):
            if getattr(block, "key", None):
                fields = {}
                for field in getattr(block, "fields", []):
                    fields[getattr(field, "key", "")] = str(getattr(field, "value", ""))
                entries.append(
                    {
                        "key": block.key,
                        "type": getattr(block, "entry_type", "article"),
                        "fields": fields,
                        "raw": render_bibtex_entry(getattr(block, "entry_type", "article"), block.key, fields),
                    }
                )
        if entries:
            return entries
    except Exception:
        pass
    return fallback_parse_bibtex_entries(content)


def fallback_parse_bibtex_entries(content: str) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    pattern = re.compile(r"@(\w+)\s*\{\s*([^,]+),(.+?)(?=\n@|\Z)", re.S)
    for match in pattern.finditer(content):
        entry_type, key, body = match.groups()
        fields: dict[str, str] = {}
        for field_match in re.finditer(r"(\w+)\s*=\s*[\{\"](.+?)[\}\"]\s*,?", body, re.S):
            fields[field_match.group(1).lower()] = re.sub(r"\s+", " ", field_match.group(2)).strip()
        entries.append({"key": key.strip(), "type": entry_type.lower(), "fields": fields, "raw": match.group(0).strip()})
    return entries


def render_bibtex_entry(entry_type: str, key: str, fields: dict[str, str]) -> str:
    lines = [f"@{entry_type}{{{key},"]
    for field, value in fields.items():
        lines.append(f"  {field} = {{{value}}},")
    lines.append("}")
    return "\n".join(lines)


def bibliography_title(entry: dict[str, Any]) -> str:
    fields = entry.get("fields") or {}
    title = fields.get("title") or entry.get("title") or entry.get("key") or "Untitled source"
    year = fields.get("year") or entry.get("year") or ""
    return f"{title} ({year})" if year else str(title)


def import_bibtex(args: dict[str, Any]) -> dict[str, Any]:
    content = str(args.get("content") or "")
    source = str(args.get("source") or "mcp")
    entries = parse_bibtex_entries(content)
    paths_written = [str(write_bibliography_entry(entry, source)) for entry in entries]
    return {"imported": len(paths_written), "paths": paths_written}


def write_bibliography_entry(entry: dict[str, Any], source: str) -> Path:
    p = paths()
    ensure_dirs(p)
    fields = entry.get("fields") or {}
    key = str(entry.get("key") or fields.get("bibtex_key") or slugify(fields.get("title", "source")))
    title = bibliography_title(entry)
    raw = str(entry.get("raw") or render_bibtex_entry(str(entry.get("type") or "misc"), key, fields))
    path = p.bibliography / f"{timestamp_slug()}-{slugify(key)}.md"
    path.write_text(
        markdown(
            title,
            "bibliography",
            f"""# {title}

## Citation Metadata
- bibtex_key: {key}
- entry_type: {entry.get('type', 'misc')}
- authors: {fields.get('author') or fields.get('authors') or ''}
- year: {fields.get('year') or ''}
- doi: {fields.get('doi') or ''}
- url: {fields.get('url') or ''}
- source: {source}

## Agent Notes
- Verify citation metadata before using in a paper, report, or grant.

## Use Annotations

## Raw BibTeX
```bibtex
{raw}
```
""",
            {
                "bibtex_key": key,
                "entry_type": entry.get("type", "misc"),
                "authors": fields.get("author") or fields.get("authors") or "",
                "year": fields.get("year") or "",
                "doi": fields.get("doi") or "",
                "url": fields.get("url") or "",
                "source": source,
            },
        ),
        encoding="utf-8",
    )
    return path


def bibliography_field(content: str, key: str) -> str:
    frontmatter = parse_frontmatter(content)
    if key in frontmatter:
        return frontmatter[key]
    match = re.search(rf"^\s*-\s*{re.escape(key)}:\s*(.+)$", content, re.M)
    return match.group(1).strip() if match else ""


def bibliography_paths() -> list[Path]:
    return [Path(item["path"]) for item in list_objects("bibliography")]


def find_bibliography_path(identifier: str) -> Optional[Path]:
    raw = str(identifier or "").strip().lower()
    if not raw:
        return None
    for path in bibliography_paths():
        content = safe_read(path)
        keys = [
            path.stem.lower(),
            title_for(path, content).lower(),
            bibliography_field(content, "bibtex_key").lower(),
            bibliography_field(content, "doi").lower(),
            bibliography_field(content, "url").lower(),
        ]
        if raw in keys or any(raw and raw in key for key in keys):
            return path
    return None


def source_entry_from_args(args: dict[str, Any]) -> dict[str, Any]:
    fields: dict[str, str] = {}
    fields["title"] = str(args.get("title") or "Untitled source")
    authors = args.get("authors") or ""
    if isinstance(authors, list):
        authors = " and ".join(map(str, authors))
    fields["author"] = str(authors)
    for key in ("year", "doi", "url", "journal", "publisher"):
        if args.get(key):
            fields[key] = str(args[key])
    key = str(args.get("bibtex_key") or slugify(f"{fields.get('author', 'source').split(' and ')[0]}-{fields.get('year', '')}-{fields.get('title', '')[:24]}"))
    raw = str(args.get("bibtex") or render_bibtex_entry(str(args.get("entry_type") or "misc"), key, fields))
    return {"key": key, "type": str(args.get("entry_type") or args.get("source_type") or "misc"), "fields": fields, "raw": raw}


def append_bibliography_annotation(path: Path, args: dict[str, Any]) -> None:
    annotation = str(args.get("annotation") or args.get("note") or "")
    used_for = str(args.get("used_for") or "unspecified")
    confidence = str(args.get("confidence") or "unspecified")
    agent = str(args.get("agent") or "agent")
    with path.open("a", encoding="utf-8") as handle:
        handle.write(
            f"\n\n### Use Annotation - {now_iso()}\n"
            f"- agent: {agent}\n"
            f"- used_for: {used_for}\n"
            f"- confidence: {confidence}\n\n"
            f"{annotation.strip()}\n"
        )


def record_citable_source(args: dict[str, Any]) -> dict[str, Any]:
    entry = source_entry_from_args(args)
    existing = None
    for key in (entry["key"], entry["fields"].get("doi", ""), entry["fields"].get("url", ""), entry["fields"].get("title", "")):
        existing = find_bibliography_path(str(key))
        if existing:
            break
    path = existing or write_bibliography_entry(entry, str(args.get("source_path") or args.get("source") or "agent"))
    if args.get("annotation") or args.get("used_for"):
        append_bibliography_annotation(path, args)
    return {"path": str(path), "created": existing is None}


def annotate_bibliography_entry(args: dict[str, Any]) -> dict[str, Any]:
    path = find_bibliography_path(str(args.get("id") or ""))
    if path is None:
        return {"error": "Bibliography entry not found"}
    append_bibliography_annotation(path, args)
    return {"path": str(path), "status": "annotated"}


def validate_bibliography(_: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    keys: dict[str, int] = {}
    missing: list[str] = []
    for path in bibliography_paths():
        content = safe_read(path)
        key = bibliography_field(content, "bibtex_key") or path.stem
        keys[key] = keys.get(key, 0) + 1
        problems = []
        if not bibliography_field(content, "year"):
            problems.append("year")
        if not bibliography_field(content, "doi") and not bibliography_field(content, "url"):
            problems.append("doi/url")
        if problems:
            missing.append(f"{title_for(path, content)}: missing {', '.join(problems)}")
    duplicates = {key: count for key, count in keys.items() if count > 1}
    return {"entries": len(keys), "duplicate_keys": duplicates, "missing_metadata": missing}


def create_bibliography_review_job(args: dict[str, Any]) -> dict[str, Any]:
    goal = str(args.get("goal") or "Review the Tremotino bibliography library")
    entries = list_objects("bibliography")
    prompt = f"""{goal}

{CITABLE_SOURCE_RULE}

Review entries for duplicate keys, missing DOI/URL/year/author metadata, citation-integrity risks, and links to Gold or research projects.

Entries:
{json.dumps(entries, indent=2)}
"""
    return create_codex_job({"title": "Review bibliography library", "workflow": "Bibliography Management", "prompt": prompt})


def list_bibliography(_: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    return {"entries": list_objects("bibliography")}


def get_bibliography_entry(args: dict[str, Any]) -> dict[str, Any]:
    path = find_bibliography_path(str(args.get("id") or ""))
    if path is None:
        return {"error": "Bibliography entry not found"}
    return get_object(str(path), "bibliography")


def recommend_skills(args: dict[str, Any]) -> dict[str, Any]:
    task = str(args.get("task") or args.get("query") or "").lower()
    limit = int(args.get("limit") or 8)
    words = {word for word in re.findall(r"[a-z0-9]{3,}", task)}
    scored = []
    for skill in list_skills({})["skills"]:
        haystack = " ".join(
            [
                skill.get("title", ""),
                skill.get("description", ""),
                skill.get("excerpt", ""),
                skill.get("path", ""),
            ]
        ).lower()
        score = sum(1 for word in words if word in haystack)
        if "research" in task and any(marker in haystack for marker in ("research", "scientific", "citation", "literature")):
            score += 3
        if "write" in task and any(marker in haystack for marker in ("writing", "doc", "style", "paper")):
            score += 3
        if "design" in task and "design" in haystack:
            score += 3
        if score > 0:
            item = dict(skill)
            item["score"] = score
            scored.append(item)
    scored.sort(key=lambda item: (-item["score"], item["title"].lower()))
    return {"skills": scored[:limit], "count": len(scored[:limit])}


def compose_workflow(args: dict[str, Any]) -> dict[str, Any]:
    task = str(args.get("task") or "")
    skills = recommend_skills({"task": task, "limit": args.get("limit") or 6})["skills"]
    steps = [
        "Assemble Tremotino context pack for the task.",
        "Load recommended skills lazily through MCP before doing substantive work.",
        "Record citable sources when sources are consulted.",
        "Write durable uncertain outputs as Review proposals and stable reusable outputs as Gold.",
    ]
    return {"task": task, "skills": skills, "steps": steps}


def install_plugin_pack_dry_run(args: dict[str, Any]) -> dict[str, Any]:
    identifier = str(args.get("id") or "")
    pack = get_object(identifier, "plugin")
    root = Path(pack["path"]).parent if not pack.get("error") else paths().packs / identifier
    assets = []
    if root.exists():
        assets = [str(path.relative_to(root)) for path in sorted(root.rglob("*")) if path.is_file()]
    return {"pack": identifier, "dry_run": True, "assets": assets, "policy": "Markdown assets only; no executable code runs."}


def create_document_tool(kind: str, args: dict[str, Any]) -> dict[str, Any]:
    return save_object({"type": kind, "title": args.get("title") or f"Untitled {kind}", "body": args.get("content") or args.get("body") or ""})


def dispatch(command: str, args: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    args = args or {}
    table = {
        "bootstrap": bootstrap,
        "migrate_vault": migrate_vault,
        "scan_vault": lambda a: list_library(a),
        "rebuild_index": rebuild_index,
        "list_objects": lambda a: {"items": list_objects(a.get("type")), "count": len(list_objects(a.get("type")))},
        "get_object": lambda a: get_object(str(a.get("id") or ""), a.get("type")),
        "save_object": save_object,
        "list_library": list_library,
        "search_library": search_library,
        "get_library_item": lambda a: get_object(str(a.get("id") or ""), a.get("type")),
        "search": search,
        "fetch": fetch,
        "propose_note": propose_note,
        "propose_update": propose_update,
        "build_project_context": build_project_context,
        "list_projects": lambda a: {"projects": list_objects("project")},
        "list_runbooks": list_runbooks,
        "run_runbook_dry_run": run_runbook_dry_run,
        "list_workflows": lambda a: {"workflows": list_objects("workflow")},
        "get_workflow": lambda a: get_object(str(a.get("id") or ""), "workflow"),
        "list_prompts": lambda a: {"prompts": list_objects("prompt")},
        "get_prompt_pack": lambda a: {"prompts": list_objects("prompt"), "client": a.get("client", "agent")},
        "get_operating_profile": lambda a: {"profile": list_objects("profile")},
        "list_directories": lambda a: {"directories": list_objects("directory")},
        "list_bibliography": list_bibliography,
        "get_bibliography_entry": get_bibliography_entry,
        "record_citable_source": record_citable_source,
        "annotate_bibliography_entry": annotate_bibliography_entry,
        "annotate_source": annotate_bibliography_entry,
        "import_bibtex": import_bibtex,
        "validate_bibliography": validate_bibliography,
        "create_bibliography_review_job": create_bibliography_review_job,
        "assemble_context": assemble_context,
        "assemble_context_pack": assemble_context_pack,
        "create_codex_job": create_codex_job,
        "create_spin_job": create_spin_job,
        "create_hay_ingestion_job": create_hay_ingestion_job,
        "list_codex_jobs": list_codex_jobs,
        "get_codex_job": get_codex_job,
        "propose_gold": propose_gold,
        "list_skills": list_skills,
        "get_skill": get_skill,
        "upsert_skill": upsert_skill,
        "annotate_skill_usage": annotate_skill_usage,
        "sync_cross_agent_skills": sync_cross_agent_skills,
        "recommend_skills": recommend_skills,
        "compose_workflow": compose_workflow,
        "list_plugins": lambda a: {"plugins": list_objects("plugin")},
        "get_plugin": lambda a: get_object(str(a.get("id") or ""), "plugin"),
        "list_designs": lambda a: {"designs": list_objects("design_md")},
        "get_design": lambda a: get_object(str(a.get("id") or ""), "design_md"),
        "list_stills": lambda a: {"stills": list_objects("still")},
        "get_still": lambda a: get_object(str(a.get("id") or ""), "still"),
        "list_context_packs": lambda a: {"context_packs": list_objects("context_pack")},
        "list_hay": lambda a: {"hay": list_objects("hay")},
        "get_hay": lambda a: get_object(str(a.get("id") or ""), "hay"),
        "install_plugin_pack_dry_run": install_plugin_pack_dry_run,
    }
    handler = table.get(command)
    if handler is None:
        return {"error": f"Unknown command: {command}"}
    return handler(args)
