"""Repository/path health checks for the World Cup prediction project.

This script is intentionally standard-library only so it can run before the
research dependencies are installed.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEXT_SUFFIXES = {".py", ".md", ".json", ".txt", ".toml", ".yaml", ".yml", ".ini", ".cfg", ".ps1", ".sh"}
SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
LOCAL_PATH_PATTERNS = (
    re.compile(r"(?i)[a-z]:[\\/]users[\\/][^\\/\s]+"),
    re.compile(r"(?i)/(?:users|home)/[^/\s]+"),
    re.compile(r"(?i)/(?:sessions|mnt)/[^/\s]+"),
)
MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")


def iter_text_files():
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.suffix.lower() not in TEXT_SUFFIXES:
            continue
        if path.stat().st_size > 2 * 1024 * 1024:
            continue
        yield path


def check_local_absolute_paths(errors: list[str]) -> None:
    for path in iter_text_files():
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for number, line in enumerate(text.splitlines(), 1):
            if any(pattern.search(line) for pattern in LOCAL_PATH_PATTERNS):
                relative = path.relative_to(ROOT).as_posix()
                errors.append(f"local absolute path: {relative}:{number}")


def iter_path_like_values(value):
    if isinstance(value, dict):
        for item in value.values():
            yield from iter_path_like_values(item)
    elif isinstance(value, list):
        for item in value:
            yield from iter_path_like_values(item)
    elif isinstance(value, str):
        normalized = value.replace("\\", "/")
        if normalized.startswith(("data/", "config/", "outputs/", "docs/")):
            yield normalized


def check_json_paths(errors: list[str]) -> None:
    paths = list((ROOT / "config").glob("*.json"))
    paths.extend((ROOT / "data" / "inputs").glob("*.json"))
    for path in sorted(paths):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"invalid config: {path.relative_to(ROOT)} ({exc})")
            continue
        for value in iter_path_like_values(payload):
            target = ROOT / value
            if not target.exists():
                errors.append(f"broken config path: {path.relative_to(ROOT)} -> {value}")


def check_pointer_files(errors: list[str]) -> None:
    pointer_dir = ROOT / "data" / "raw" / "polymarket"
    for path in sorted(pointer_dir.glob("LATEST*.txt")):
        target_text = path.read_text(encoding="utf-8-sig").strip()
        target = Path(target_text)
        if not target_text:
            errors.append(f"empty pointer: {path.relative_to(ROOT)}")
        elif target.is_absolute():
            errors.append(f"absolute pointer: {path.relative_to(ROOT)} -> {target_text}")
        elif "\\" in target_text:
            errors.append(f"pointer must use '/': {path.relative_to(ROOT)} -> {target_text}")
        elif not (ROOT / target).resolve().is_relative_to(ROOT.resolve()):
            errors.append(f"pointer escapes repository: {path.relative_to(ROOT)} -> {target_text}")
        elif not (ROOT / target).exists():
            errors.append(f"broken pointer: {path.relative_to(ROOT)} -> {target_text}")


def check_repository_shape(errors: list[str]) -> None:
    for name in ("config", "data", "docs", "outputs", "scripts", "src", "tests"):
        if not (ROOT / name).is_dir():
            errors.append(f"missing required directory: {name}/")
    for name in ("README.md", "requirements.txt", ".gitignore", ".gitattributes"):
        if not (ROOT / name).is_file():
            errors.append(f"missing required file: {name}")


def check_markdown_links(errors: list[str]) -> None:
    for path in ROOT.rglob("*.md"):
        if any(part in SKIP_PARTS for part in path.parts):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        for raw_target in MARKDOWN_LINK.findall(text):
            target = raw_target.strip().strip("<>").split("#", 1)[0]
            if not target or target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            if not resolved.exists():
                errors.append(f"broken Markdown link: {path.relative_to(ROOT)} -> {raw_target}")


def check_lfs_policy(errors: list[str]) -> None:
    attributes = (ROOT / ".gitattributes").read_text(encoding="utf-8-sig", errors="replace")
    for pattern in ("*.pdf filter=lfs", "*.gz filter=lfs", "data/raw/polymarket/*_live_*.json filter=lfs"):
        if pattern not in attributes:
            errors.append(f"missing Git LFS policy: {pattern}")


def check_github_file_limit(errors: list[str], warnings: list[str]) -> None:
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        size = path.stat().st_size
        relative = path.relative_to(ROOT).as_posix()
        if size > 100 * 1024 * 1024:
            errors.append(f"file exceeds GitHub 100 MiB hard limit: {relative}")
        elif size > 10 * 1024 * 1024:
            warnings.append(f"large file: {relative} ({size / 1024 / 1024:.1f} MiB)")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    check_repository_shape(errors)
    check_local_absolute_paths(errors)
    check_json_paths(errors)
    check_pointer_files(errors)
    check_markdown_links(errors)
    check_lfs_policy(errors)
    check_github_file_limit(errors, warnings)

    print(f"project_root={ROOT}")
    for item in warnings:
        print(f"WARNING: {item}")
    for item in errors:
        print(f"ERROR: {item}")
    print(f"repository_check: errors={len(errors)}, warnings={len(warnings)}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
