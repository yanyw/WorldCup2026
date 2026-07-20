from __future__ import annotations

import argparse
import html
import json
import re
import time
import unicodedata
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

SOURCES = {
    "England": "https://www.ea.com/en/games/ea-sports-fc/ratings/nations-ratings/england/14",
    "Argentina": "https://www.ea.com/games/ea-sports-fc/ratings/nations-ratings/argentina/52",
}


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    return "".join(ch for ch in value if not unicodedata.combining(ch)).casefold().strip()


def fetch_rows(url: str) -> list[dict]:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    text = urllib.request.urlopen(request, timeout=45).read().decode("utf-8")
    rows: list[dict] = []
    for raw in re.findall(r"<tr[^>]*>.*?</tr>", text, re.S):
        clean = html.unescape(re.sub(r"<[^>]+>", " ", raw))
        clean = re.sub(r"\s+", " ", clean).strip()
        match = re.search(
            r"#\d+\s+(.+?)\s+(GK|CB|LB|RB|LWB|RWB|CDM|CM|CAM|LM|RM|LW|RW|CF|ST)\s+"
            r"OVR\s+(\d+)\s+PAC\s+(\d+)\s+SHO\s+(\d+)\s+PAS\s+(\d+)\s+"
            r"DRI\s+(\d+)\s+DEF\s+(\d+)\s+PHY\s+(\d+)",
            clean,
        )
        if not match:
            continue
        name, position, *values = match.groups()
        rows.append({
            "name": name,
            "position": position,
            **dict(zip(("ovr", "pac", "sho", "pas", "dri", "def", "phy"), map(int, values))),
        })
    return rows


def fetch_team_rows(url: str, wanted: set[str], max_pages: int = 16) -> list[dict]:
    """Fetch pagination only until every requested player has been found."""
    collected: dict[str, dict] = {}
    for page in range(1, max_pages + 1):
        page_url = url if page == 1 else f"{url}?page={page}"
        page_rows = None
        for attempt in range(3):
            try:
                page_rows = fetch_rows(page_url)
                break
            except Exception:
                if attempt == 2:
                    page_rows = []
                    break
                time.sleep(1.0 + attempt)
        if not page_rows:
            break
        for row in page_rows or []:
            collected[normalize(row["name"])] = row
        if wanted.issubset(collected):
            break
    return list(collected.values())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--game-input", default="data/inputs/game_model_eng_arg_20260715.json")
    parser.add_argument("--output", default="data/curated/fc26_eng_arg_20260715.json")
    args = parser.parse_args()

    game = json.loads((ROOT / args.game_input).read_text(encoding="utf-8"))
    output = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "rating_edition": "EA SPORTS FC 26 launch Gold/Silver/Bronze items",
        "limitations": [
            "EA states that these ratings exclude live-form updates and campaign items.",
            "Goalkeeper rows retain EA's displayed six columns; downstream modeling uses goalkeeper OVR only.",
            "Ratings are a bounded prior, not a direct probability forecast.",
        ],
        "sources": SOURCES,
        "teams": {},
    }
    for team, spec in game["teams"].items():
        wanted_players = spec["starting_xi"] + spec.get("bench", [])
        wanted = {normalize(player["name"]) for player in wanted_players}
        rows = fetch_team_rows(SOURCES[team], wanted)
        lookup = {normalize(row["name"]): row for row in rows}
        selected, bench = [], []
        missing = []
        for player in spec["starting_xi"]:
            key = normalize(player["name"])
            row = lookup.get(key)
            if row is None:
                missing.append(player["name"])
                continue
            selected.append({**row, "role": player["role"],
                             "availability": player.get("availability", 1.0)})
        for player in spec.get("bench", []):
            key = normalize(player["name"])
            row = lookup.get(key)
            if row is None:
                missing.append(player["name"])
                continue
            bench.append({**row, "role": player["role"],
                          "availability": player.get("availability", 1.0)})
        if missing:
            raise RuntimeError(f"missing FC 26 rows for {team}: {missing}")
        output["teams"][team] = {"players": selected, "bench": bench,
                                   "source_rows_available": len(rows)}

    path = ROOT / args.output
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(path),
                      "starters": sum(len(x["players"]) for x in output["teams"].values()),
                      "bench": sum(len(x["bench"]) for x in output["teams"].values())}, ensure_ascii=False))


if __name__ == "__main__":
    main()
