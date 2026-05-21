#!/usr/bin/env python3
"""Offline repository validation for MySkill."""

from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {".git", ".venv", "__pycache__"}
SENSITIVE_RE = re.compile(r"(api[_-]?key|token|secret|cookie|authorization)", re.I)
PLACEHOLDER_SECRET_RE = re.compile(
    r"(sk-[A-Za-z0-9_-]{12,}|ghp_[A-Za-z0-9_]{12,}|xox[baprs]-[A-Za-z0-9-]{12,})"
)
TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|TBD)\b", re.I)
MD_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")
SCHEMA_HINT_RE = re.compile(r"\b(schema|summary|metadata|manifest)\b", re.I)
REFERENCE_LINK_RE = re.compile(r"\(([^)]+references/[^)]+)\)", re.I)
PACK_INSTALL_STATUS = {"required", "optional", "quarantined"}
PACK_VERIFY_STATUS = {"ok", "missing", "drift", "unverified", "quarantined"}
PACK_REQUIRED_SKILLS = {"frontend-design", "docx", "xlsx", "pdf", "pptx", "web-access", "pua"}
PACK_REQUIRED_AGENTS = {"Claude", "Codex", "Cursor"}
RICH_REFERENCE_FILES = {
    "references/ASSETS-SCREENSHOTS.md",
    "references/RUN-MANIFEST.md",
    "references/FEEDBACK-AND-PARALLEL.md",
}
RICH_EXAMPLE_FILES = {
    "examples/run-manifest-rich.example.json",
    "examples/assets-and-screenshots.example.json",
}
ASSET_TYPES = {
    "source-screenshot",
    "user-provided",
    "code-drawn",
    "ai-generated",
    "placeholder",
    "formula-render",
}
RICH_STATUSES = {"ok", "partial", "failed", "blocked", "skipped", "pending", "approved", "needs-replacement"}
FORMAT_NAMES = {"markdown", "html", "pptx", "word", "docx", "pdf"}


class Reporter:
    def __init__(self) -> None:
        self.errors: list[str] = []
        self.warnings: list[str] = []

    def error(self, message: str) -> None:
        self.errors.append(message)

    def warn(self, message: str) -> None:
        self.warnings.append(message)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def iter_files(*patterns: str) -> list[Path]:
    files: list[Path] = []
    for pattern in patterns:
        files.extend(ROOT.glob(pattern))
    return sorted(path for path in files if path.is_file() and not any(part in SKIP_DIRS for part in path.parts))


def skill_dirs() -> list[Path]:
    return sorted(
        path
        for path in ROOT.iterdir()
        if path.is_dir()
        and not path.name.startswith(".")
        and path.name not in {"docs", "scripts", "openspec"}
        and (path / "SKILL.md").is_file()
    )


def parse_frontmatter(path: Path, reporter: Reporter) -> dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        reporter.error(f"{rel(path)}: missing YAML frontmatter")
        return {}
    end = text.find("\n---", 4)
    if end == -1:
        reporter.error(f"{rel(path)}: frontmatter is not closed")
        return {}
    raw = text[4:end].strip().splitlines()
    data: dict[str, Any] = {}
    for line in raw:
        if not line.strip() or line.startswith(" "):
            continue
        if ":" not in line:
            reporter.error(f"{rel(path)}: invalid frontmatter line: {line}")
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip().strip("\"'")
    for key in ("name", "description"):
        if not data.get(key):
            reporter.error(f"{rel(path)}: missing frontmatter field '{key}'")
    return data


def parse_simple_yaml(path: Path) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue
        indent = len(line) - len(line.lstrip(" "))
        key, _, value = line.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
            continue
        text = value.strip().strip("\"'")
        if text.lower() == "true":
            parent[key] = True
        elif text.lower() == "false":
            parent[key] = False
        else:
            parent[key] = text
    return root


def validate_agents(skill: Path, expected_name: str, reporter: Reporter) -> None:
    agents_dir = skill / "agents"
    openai_yaml = agents_dir / "openai.yaml"
    if not openai_yaml.is_file():
        reporter.error(f"{rel(skill)}: missing agents/openai.yaml")
        return
    try:
        data = parse_simple_yaml(openai_yaml)
    except Exception as exc:  # noqa: BLE001
        reporter.error(f"{rel(openai_yaml)}: cannot parse YAML: {exc}")
        return
    interface = data.get("interface", {})
    policy = data.get("policy", {})
    for key in ("display_name", "short_description", "default_prompt"):
        if not interface.get(key):
            reporter.error(f"{rel(openai_yaml)}: missing interface.{key}")
    prompt = str(interface.get("default_prompt", ""))
    if expected_name and f"${expected_name}" not in prompt:
        reporter.error(f"{rel(openai_yaml)}: default_prompt must mention ${expected_name}")
    if "allow_implicit_invocation" not in policy:
        reporter.error(f"{rel(openai_yaml)}: missing policy.allow_implicit_invocation")


def validate_required_files(skill: Path, reporter: Reporter) -> None:
    if not (skill / "scripts").is_dir():
        reporter.error(f"{rel(skill)}: missing scripts/")
    elif not list((skill / "scripts").glob("*.py")):
        reporter.error(f"{rel(skill)}: scripts/ contains no Python helpers")
    for optional in ("references", "templates", "examples"):
        target = skill / optional
        if target.exists() and not target.is_dir():
            reporter.error(f"{rel(target)}: optional skill asset must be a directory")
    manifest = skill / "manifest.json"
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            reporter.error(f"{rel(manifest)}: invalid JSON: {exc}")
            return
        for key in ("name", "version", "category", "description", "dependencies"):
            if key not in data:
                reporter.error(f"{rel(manifest)}: missing manifest field '{key}'")
        if "compat" not in data and "compatibility" not in data:
            reporter.error(f"{rel(manifest)}: missing manifest field 'compat'")
        if "default_output_dir" not in data and "default_outputs" not in data:
            reporter.error(f"{rel(manifest)}: missing manifest field 'default_output_dir'")


def validate_python_scripts(reporter: Reporter) -> None:
    for path in iter_files("*/scripts/*.py", "*/*/scripts/*.py", "scripts/*.py"):
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except SyntaxError as exc:
            reporter.error(f"{rel(path)}: Python syntax error: {exc}")
            continue
        if path.parts[-2] == "scripts" and path.parent.parent in skill_dirs():
            proc = subprocess.run(
                [sys.executable, str(path), "--help"],
                cwd=str(path.parent.parent),
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
                check=False,
            )
            output = (proc.stdout + proc.stderr).lower()
            if proc.returncode != 0 or "usage:" not in output:
                reporter.error(f"{rel(path)}: --help failed or did not print usage")


def normalize_link_target(raw: str) -> str | None:
    target = raw.strip().split()[0].strip("<>")
    if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.I):
        return None
    if target.startswith("#"):
        return None
    return target.split("#", 1)[0]


def validate_markdown_links(reporter: Reporter) -> None:
    for path in iter_files("*.md", "docs/**/*.md", "*/*.md", "openspec/**/*.md"):
        text = path.read_text(encoding="utf-8")
        for raw in MD_LINK_RE.findall(text):
            target_text = normalize_link_target(raw)
            if not target_text:
                continue
            target = (path.parent / target_text).resolve()
            try:
                target.relative_to(ROOT.resolve())
            except ValueError:
                reporter.error(f"{rel(path)}: local link escapes repository: {raw}")
                continue
            if not target.exists():
                reporter.error(f"{rel(path)}: broken local Markdown link: {raw}")
        for raw in REFERENCE_LINK_RE.findall(text):
            target_text = normalize_link_target(raw)
            if target_text and not (path.parent / target_text).exists():
                reporter.error(f"{rel(path)}: reference map target is missing: {raw}")


def validate_json_examples(reporter: Reporter) -> None:
    for path in iter_files("docs/**/*.json", "**/examples/**/*.json", "**/references/**/*.json", "**/manifest.json"):
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            reporter.error(f"{rel(path)}: invalid JSON example/schema: {exc}")


def require_keys(data: dict[str, Any], keys: set[str], path: Path, reporter: Reporter, context: str = "") -> None:
    missing = sorted(key for key in keys if key not in data)
    if missing:
        label = f" {context}" if context else ""
        reporter.error(f"{rel(path)}:{label} missing required keys: {', '.join(missing)}")


def validate_asset_item(asset: Any, path: Path, reporter: Reporter, index: int) -> None:
    if not isinstance(asset, dict):
        reporter.error(f"{rel(path)}: assets[{index}] must be an object")
        return
    require_keys(asset, {"id", "type", "status", "source", "purpose", "references", "alt_text"}, path, reporter, f"assets[{index}]")
    asset_type = asset.get("type")
    if asset_type not in ASSET_TYPES:
        reporter.error(f"{rel(path)}: assets[{index}].type must be one of {sorted(ASSET_TYPES)}")
    status = asset.get("status")
    if status not in RICH_STATUSES:
        reporter.error(f"{rel(path)}: assets[{index}].status has unknown value '{status}'")
    if not isinstance(asset.get("references"), list) or not asset.get("references"):
        reporter.error(f"{rel(path)}: assets[{index}].references must be a non-empty list")
    if not str(asset.get("alt_text", "")).strip():
        reporter.error(f"{rel(path)}: assets[{index}].alt_text must be non-empty")
    if asset_type == "placeholder" and "replacement" not in json.dumps(asset, ensure_ascii=False).lower():
        reporter.error(f"{rel(path)}: assets[{index}] placeholder must explain replacement")
    if asset_type in {"code-drawn", "ai-generated"}:
        note = json.dumps(asset, ensure_ascii=False).lower()
        if ("真实截图" in note or "real screenshot" in note) and "非真实截图" not in note and "not a real screenshot" not in note:
            reporter.error(f"{rel(path)}: assets[{index}] must not imply generated/drawn assets are real screenshots")


def validate_rich_examples(reporter: Reporter) -> None:
    skill = ROOT / "video-transcript"
    if not skill.exists():
        return
    skill_text = (skill / "SKILL.md").read_text(encoding="utf-8")
    for required in RICH_REFERENCE_FILES:
        if required not in skill_text:
            reporter.error(f"video-transcript/SKILL.md: reference map missing {required}")
        if not (skill / required).is_file():
            reporter.error(f"video-transcript: missing {required}")
    for required in RICH_EXAMPLE_FILES:
        if not (skill / required).is_file():
            reporter.error(f"video-transcript: missing {required}")

    manifest_path = skill / "examples/run-manifest-rich.example.json"
    if manifest_path.is_file():
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        require_keys(
            data,
            {
                "schema_version",
                "contract_note",
                "run_id",
                "status",
                "inputs",
                "metadata_refs",
                "content_plan",
                "web_access",
                "formats",
                "outputs",
                "hashes",
                "formula_fallbacks",
                "assets",
                "screenshots",
                "design_checks",
                "qa_evidence",
                "redacted_argv",
                "privacy_and_copyright",
                "tool_versions",
                "failures",
                "next_actions",
            },
            manifest_path,
            reporter,
        )
        if "只说明契约，不代表真实产物" not in str(data.get("contract_note", "")):
            reporter.error(f"{rel(manifest_path)}: contract_note must say it only describes the contract")
        if data.get("status") not in RICH_STATUSES:
            reporter.error(f"{rel(manifest_path)}: status has unknown value '{data.get('status')}'")
        for index, fmt in enumerate(data.get("formats", [])):
            if not isinstance(fmt, dict):
                reporter.error(f"{rel(manifest_path)}: formats[{index}] must be an object")
                continue
            require_keys(fmt, {"format", "requested", "selected", "status"}, manifest_path, reporter, f"formats[{index}]")
            if fmt.get("format") not in FORMAT_NAMES:
                reporter.error(f"{rel(manifest_path)}: formats[{index}].format has unknown value '{fmt.get('format')}'")
            if fmt.get("status") not in RICH_STATUSES:
                reporter.error(f"{rel(manifest_path)}: formats[{index}].status has unknown value '{fmt.get('status')}'")
        for index, asset in enumerate(data.get("assets", [])):
            validate_asset_item(asset, manifest_path, reporter, index)
        for index, shot in enumerate(data.get("screenshots", [])):
            if not isinstance(shot, dict):
                reporter.error(f"{rel(manifest_path)}: screenshots[{index}] must be an object")
                continue
            require_keys(shot, {"id", "timestamp", "path", "references", "alt_text", "necessity"}, manifest_path, reporter, f"screenshots[{index}]")

    assets_path = skill / "examples/assets-and-screenshots.example.json"
    if assets_path.is_file():
        data = json.loads(assets_path.read_text(encoding="utf-8"))
        require_keys(data, {"schema_version", "contract_note", "assets", "screenshots", "self_check"}, assets_path, reporter)
        if "只说明契约，不代表真实产物" not in str(data.get("contract_note", "")):
            reporter.error(f"{rel(assets_path)}: contract_note must say it only describes the contract")
        seen_types: set[str] = set()
        for index, asset in enumerate(data.get("assets", [])):
            validate_asset_item(asset, assets_path, reporter, index)
            if isinstance(asset, dict) and asset.get("type") in ASSET_TYPES:
                seen_types.add(str(asset["type"]))
        missing_types = sorted(ASSET_TYPES - seen_types)
        if missing_types:
            reporter.error(f"{rel(assets_path)}: assets example missing types: {', '.join(missing_types)}")
        for index, shot in enumerate(data.get("screenshots", [])):
            if not isinstance(shot, dict):
                reporter.error(f"{rel(assets_path)}: screenshots[{index}] must be an object")
                continue
            require_keys(
                shot,
                {"id", "timestamp", "reason", "purpose", "alt_text", "suggested_formats", "dedupe_group", "necessity"},
                assets_path,
                reporter,
                f"screenshots[{index}]",
            )


def pack_skill_blocks(text: str) -> list[str]:
    blocks: list[str] = []
    current: list[str] = []
    in_skills = False
    for line in text.splitlines():
        if line.startswith("skills:"):
            in_skills = True
            continue
        if in_skills and line and not line.startswith(" ") and not line.startswith("-"):
            break
        if not in_skills:
            continue
        if line.startswith("  - canonicalName:"):
            if current:
                blocks.append("\n".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        blocks.append("\n".join(current))
    return blocks


def block_value(block: str, key: str) -> str | None:
    match = re.search(rf"^\s+(?:-\s+)?{re.escape(key)}:\s*(.+)$", block, re.M)
    if not match:
        return None
    return match.group(1).strip().strip("\"'")


def block_list_value(block: str, key: str) -> list[str]:
    value = block_value(block, key)
    if not value:
        return []
    if value.startswith("[") and value.endswith("]"):
        return [item.strip().strip("\"'") for item in value[1:-1].split(",") if item.strip()]
    return [value]


def validate_agent_skill_pack_yaml(reporter: Reporter) -> set[str]:
    path = ROOT / "agent-skill-pack.yaml"
    if not path.is_file():
        reporter.error("agent-skill-pack.yaml: missing")
        return set()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeDecodeError as exc:
        reporter.error(f"agent-skill-pack.yaml: cannot read as UTF-8: {exc}")
        return set()
    if "\t" in text:
        reporter.error("agent-skill-pack.yaml: tabs are not allowed in this repository YAML")
    if not re.search(r"^schemaVersion:\s*\S+", text, re.M):
        reporter.error("agent-skill-pack.yaml: missing schemaVersion")
    for agent in PACK_REQUIRED_AGENTS:
        if not re.search(rf"^\s+- name:\s*{re.escape(agent)}\s*$", text, re.M):
            reporter.error(f"agent-skill-pack.yaml: missing required agent '{agent}'")
    blocks = pack_skill_blocks(text)
    if not blocks:
        reporter.error("agent-skill-pack.yaml: missing skills entries")
        return set()
    seen: set[str] = set()
    for block in blocks:
        name = block_value(block, "canonicalName")
        if not name:
            reporter.error("agent-skill-pack.yaml: skill entry missing canonicalName")
            continue
        if name in seen:
            reporter.error(f"agent-skill-pack.yaml: duplicate canonicalName '{name}'")
        seen.add(name)
        for key in ("aliases", "capability", "callName", "status"):
            if not block_value(block, key):
                reporter.error(f"agent-skill-pack.yaml: {name}: missing {key}")
        status = block_value(block, "status")
        if status and status not in PACK_INSTALL_STATUS:
            reporter.error(f"agent-skill-pack.yaml: {name}: invalid status '{status}'")
        aliases = block_list_value(block, "aliases")
        if not aliases:
            reporter.error(f"agent-skill-pack.yaml: {name}: aliases must not be empty")
        for required_text in ("source:", "kind:", "path:", "installTargets:", "verificationProbe:", "agentCaveat:"):
            if required_text not in block:
                reporter.error(f"agent-skill-pack.yaml: {name}: missing {required_text.rstrip(':')}")
        for agent in PACK_REQUIRED_AGENTS:
            if not re.search(rf"^\s+- agent:\s*{re.escape(agent)}\s*$", block, re.M):
                reporter.error(f"agent-skill-pack.yaml: {name}: missing install target for {agent}")
    missing = PACK_REQUIRED_SKILLS - seen
    for name in sorted(missing):
        reporter.error(f"agent-skill-pack.yaml: missing required skill '{name}'")
    pua_block = next((block for block in blocks if block_value(block, "canonicalName") == "pua"), "")
    if pua_block and block_value(pua_block, "status") != "quarantined":
        reporter.error("agent-skill-pack.yaml: pua must remain quarantined")
    return seen


def validate_agent_skill_pack_lock(reporter: Reporter, expected_names: set[str]) -> None:
    path = ROOT / "agent-skill-pack.lock.json"
    if not path.is_file():
        reporter.error("agent-skill-pack.lock.json: missing")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        reporter.error(f"agent-skill-pack.lock.json: invalid JSON: {exc}")
        return
    if "schemaVersion" not in data:
        reporter.error("agent-skill-pack.lock.json: missing schemaVersion")
    entries = data.get("entries")
    if not isinstance(entries, list) or not entries:
        reporter.error("agent-skill-pack.lock.json: entries must be a non-empty list")
        return
    seen: set[str] = set()
    for index, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            reporter.error(f"agent-skill-pack.lock.json: entries[{index}] must be an object")
            continue
        name = entry.get("canonicalName")
        if not isinstance(name, str) or not name:
            reporter.error(f"agent-skill-pack.lock.json: entries[{index}] missing canonicalName")
            continue
        if name in seen:
            reporter.error(f"agent-skill-pack.lock.json: duplicate canonicalName '{name}'")
        seen.add(name)
        for key in ("version", "commit", "checksum", "source", "installations", "status", "drift"):
            if key not in entry:
                reporter.error(f"agent-skill-pack.lock.json: {name}: missing {key}")
        status = entry.get("status")
        if status not in PACK_VERIFY_STATUS:
            reporter.error(f"agent-skill-pack.lock.json: {name}: invalid status '{status}'")
        source = entry.get("source")
        if not isinstance(source, dict) or "kind" not in source or ("path" not in source and "url" not in source):
            reporter.error(f"agent-skill-pack.lock.json: {name}: source must include kind and path or url")
        drift = entry.get("drift")
        if not isinstance(drift, dict) or "detected" not in drift:
            reporter.error(f"agent-skill-pack.lock.json: {name}: drift must include detected")
        installations = entry.get("installations")
        if not isinstance(installations, list) or not installations:
            reporter.error(f"agent-skill-pack.lock.json: {name}: installations must be a non-empty list")
            continue
        agents = set()
        for install_index, install in enumerate(installations, 1):
            if not isinstance(install, dict):
                reporter.error(f"agent-skill-pack.lock.json: {name}: installations[{install_index}] must be an object")
                continue
            agent = install.get("agent")
            if isinstance(agent, str):
                agents.add(agent)
            for key in ("agent", "path", "verifiedAt", "status", "verificationProbe"):
                if key not in install:
                    reporter.error(f"agent-skill-pack.lock.json: {name}: installation missing {key}")
            install_status = install.get("status")
            if install_status not in PACK_VERIFY_STATUS:
                reporter.error(f"agent-skill-pack.lock.json: {name}: invalid installation status '{install_status}'")
        for agent in sorted(PACK_REQUIRED_AGENTS - agents):
            reporter.error(f"agent-skill-pack.lock.json: {name}: missing installation for {agent}")
    for name in sorted(expected_names - seen):
        reporter.error(f"agent-skill-pack.lock.json: missing lock entry for '{name}'")
    extra = seen - expected_names if expected_names else set()
    for name in sorted(extra):
        reporter.warn(f"agent-skill-pack.lock.json: lock entry '{name}' is not present in agent-skill-pack.yaml")
    if "pua" in seen:
        pua_entry = next((entry for entry in entries if isinstance(entry, dict) and entry.get("canonicalName") == "pua"), {})
        if pua_entry.get("status") != "quarantined":
            reporter.error("agent-skill-pack.lock.json: pua must remain quarantined")


def validate_agent_skill_pack(reporter: Reporter) -> None:
    names = validate_agent_skill_pack_yaml(reporter)
    validate_agent_skill_pack_lock(reporter, names)


def validate_content_hygiene(reporter: Reporter) -> None:
    checked = iter_files("*.md", "docs/**/*.md", "**/examples/**/*", "**/references/**/*", "**/manifest.json")
    for path in checked:
        if not path.is_file() or path.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".webp"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if PLACEHOLDER_SECRET_RE.search(text):
            reporter.error(f"{rel(path)}: appears to contain a real-looking secret")
        for line_no, line in enumerate(text.splitlines(), 1):
            if TODO_RE.search(line):
                reporter.error(f"{rel(path)}:{line_no}: unresolved TODO-style placeholder")
            if SENSITIVE_RE.search(line) and re.search(r"[:=]\s*['\"]?[A-Za-z0-9_./+-]{16,}", line):
                reporter.error(f"{rel(path)}:{line_no}: sensitive-looking field value")
        if "examples" in path.parts and "example" not in text.lower() and path.suffix.lower() in {".md", ".json"}:
            reporter.warn(f"{rel(path)}: example file should clearly label itself as example material")


def validate_schema_mentions(reporter: Reporter) -> None:
    docs = [p for p in iter_files("docs/**/*.md", "*/*.md") if SCHEMA_HINT_RE.search(p.read_text(encoding="utf-8", errors="ignore"))]
    if not docs:
        reporter.error("docs: no schema/summary/metadata/manifest rules found")


def main() -> int:
    reporter = Reporter()
    skills = skill_dirs()
    if not skills:
        reporter.error("no skill directories found")
    for skill in skills:
        frontmatter = parse_frontmatter(skill / "SKILL.md", reporter)
        expected_name = str(frontmatter.get("name", ""))
        if expected_name and expected_name != skill.name:
            reporter.error(f"{rel(skill / 'SKILL.md')}: name '{expected_name}' does not match directory '{skill.name}'")
        validate_agents(skill, expected_name or skill.name, reporter)
        validate_required_files(skill, reporter)
    validate_python_scripts(reporter)
    validate_markdown_links(reporter)
    validate_json_examples(reporter)
    validate_rich_examples(reporter)
    validate_agent_skill_pack(reporter)
    validate_schema_mentions(reporter)
    validate_content_hygiene(reporter)

    print("Offline repository validation")
    print(f"Skills checked: {', '.join(skill.name for skill in skills) or '(none)'}")
    if reporter.warnings:
        print("\nWarnings:")
        for item in reporter.warnings:
            print(f"  - {item}")
    if reporter.errors:
        print("\nErrors:")
        for item in reporter.errors:
            print(f"  - {item}")
        return 1
    print("\nOK: all offline checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
