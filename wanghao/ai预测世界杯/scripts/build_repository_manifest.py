"""Build a reproducibility manifest with file sizes and SHA-256 hashes."""

from __future__ import annotations

import csv
import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CSV_OUTPUT = ROOT / "docs" / "FILE_MANIFEST.csv"
SUMMARY_OUTPUT = ROOT / "docs" / "FILE_MANIFEST_SUMMARY.md"
SKIP_PARTS = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
SKIP_FILES = {CSV_OUTPUT.resolve(), SUMMARY_OUTPUT.resolve()}


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def category(path: Path) -> str:
    relative = path.relative_to(ROOT)
    return relative.parts[0] if len(relative.parts) > 1 else "root"


def main() -> None:
    files = []
    for path in ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_PARTS for part in path.parts):
            continue
        if path.resolve() in SKIP_FILES:
            continue
        files.append(path)
    files.sort(key=lambda item: item.relative_to(ROOT).as_posix().lower())

    rows = []
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        rows.append({
            "path": relative,
            "category": category(path),
            "size_bytes": path.stat().st_size,
            "sha256": sha256(path),
        })

    CSV_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with CSV_OUTPUT.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["path", "category", "size_bytes", "sha256"])
        writer.writeheader()
        writer.writerows(rows)

    counts = Counter(row["category"] for row in rows)
    sizes = defaultdict(int)
    for row in rows:
        sizes[row["category"]] += int(row["size_bytes"])
    generated = datetime.now(timezone.utc).isoformat()
    lines = [
        "# 文件清单摘要",
        "",
        f"生成时间：{generated}",
        "",
        f"清单包含 {len(rows)} 个文件，总大小 {sum(sizes.values()) / 1024 / 1024:.2f} MiB。",
        "",
        "| 类别 | 文件数 | 大小 (MiB) |",
        "|---|---:|---:|",
    ]
    for name in sorted(counts):
        lines.append(f"| {name} | {counts[name]} | {sizes[name] / 1024 / 1024:.2f} |")
    lines.extend([
        "",
        "逐文件路径、字节数和 SHA-256 见 `docs/FILE_MANIFEST.csv`。清单不包含 `.git/`、Python 缓存、虚拟环境以及清单自身。",
    ])
    SUMMARY_OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"manifest_files={len(rows)} size_mib={sum(sizes.values()) / 1024 / 1024:.2f}")


if __name__ == "__main__":
    main()
