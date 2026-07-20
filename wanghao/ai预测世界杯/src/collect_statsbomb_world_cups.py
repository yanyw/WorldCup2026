"""Collect StatsBomb Open Data for the 2018 and 2022 men's World Cups.

The public event stream is used only to estimate generic football dynamics
(minute hazard, score-state, red-card, substitution and player action shares).
Files are stored losslessly as gzip-compressed JSON and never silently replaced.
"""

from __future__ import annotations

import gzip
import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "statsbomb_world_cups"
RAW = "https://raw.githubusercontent.com/statsbomb/open-data/master/data"
SEASONS = {"2018": (43, 3), "2022": (43, 106)}


def fetch(url: str, retries: int = 4) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=90) as response:
                return response.read()
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = exc
            time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"Failed to fetch {url}: {last_error}")


def store_gzip_json(path: Path, content: bytes) -> tuple[int, str]:
    digest = hashlib.sha256(content).hexdigest()
    if path.exists():
        with gzip.open(path, "rb") as fh:
            old = fh.read()
        if hashlib.sha256(old).hexdigest() != digest:
            raise RuntimeError(f"Refusing to replace changed raw file: {path}")
    else:
        with gzip.open(path, "wb", compresslevel=6) as fh:
            fh.write(content)
    return len(content), digest


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    manifest_rows = []
    for season, (competition_id, season_id) in SEASONS.items():
        match_url = f"{RAW}/matches/{competition_id}/{season_id}.json"
        match_bytes = fetch(match_url)
        matches = json.loads(match_bytes)
        match_path = OUT / f"matches_{season}.json.gz"
        size, digest = store_gzip_json(match_path, match_bytes)
        manifest_rows.append(
            {"kind": "matches", "season": season, "url": match_url,
             "filename": match_path.name, "bytes_uncompressed": size, "sha256": digest}
        )

        season_dir = OUT / season / "events"
        season_dir.mkdir(parents=True, exist_ok=True)
        for index, match in enumerate(matches, 1):
            match_id = int(match["match_id"])
            url = f"{RAW}/events/{match_id}.json"
            target = season_dir / f"{match_id}.json.gz"
            if target.exists():
                with gzip.open(target, "rb") as fh:
                    content = fh.read()
            else:
                content = fetch(url)
            size, digest = store_gzip_json(target, content)
            manifest_rows.append(
                {"kind": "events", "season": season, "match_id": match_id,
                 "url": url, "filename": str(target.relative_to(OUT)),
                 "bytes_uncompressed": size, "sha256": digest}
            )
            if index % 16 == 0:
                print(f"{season}: {index}/{len(matches)}", flush=True)

    manifest = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": "StatsBomb Open Data",
        "source_repository": "https://github.com/statsbomb/open-data",
        "license_note": "StatsBomb Open Data terms apply; attribution retained.",
        "files": manifest_rows,
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"files": len(manifest_rows), "directory": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
