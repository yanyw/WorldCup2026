"""Extract real final-four team/player features from FIFA 2026 reports.

No game ratings, odds, Elo values, or prior prediction outputs are read here.
The source PDF checksum manifest provides the point-in-time audit trail.
"""

from __future__ import annotations

import csv
import json
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import pdfplumber
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw" / "fifa_performance_reports_2026"
CURATED = ROOT / "data" / "curated"
LINEUP_INPUT = ROOT / "data" / "inputs" / "final_four_lineups_20260716.json"
TEAMS = ("France", "England", "Spain", "Argentina")

DURATION = {
    "PMSR-M86-ARG-V-CPV.pdf": 120,
    "PMSR-M99-NOR-V-ENG.pdf": 120,
    "PMSR-M100-ARG-V-SUI.pdf": 120,
}


def norm(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(c for c in value if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def canonical_roster() -> tuple[dict[str, str], dict[str, str]]:
    payload = json.loads(LINEUP_INPUT.read_text(encoding="utf-8"))
    names: dict[str, str] = {}
    roles: dict[str, str] = {}
    for team in TEAMS:
        for player in payload["teams"][team]["starting_xi"] + payload["teams"][team]["bench"]:
            key = " ".join(sorted(norm(player["name"]).split()))
            names[key] = player["name"]
            roles[player["name"]] = player["role"]
    # FIFA sometimes drops accents and uses Nico rather than Nicolas.
    aliases = {
        "gonzalez nico": "Nico Gonzalez",
        "martinez emiliano": "Emiliano Martínez",
        "martinez lisandro": "Lisandro Martínez",
        "martinez lautaro": "Lautaro Martínez",
        "alvarez julian": "Julián Alvarez",
        "fernandez enzo": "Enzo Fernández",
        "tagliafico nicolas": "Nicolás Tagliafico",
        "oreilly nico": "Nico O'Reilly",
        "guehi marc": "Marc Guéhi",
        "mbappe kylian": "Kylian Mbappé",
        "tchouameni aurelien": "Aurélien Tchouaméni",
        "dembele ousmane": "Ousmane Dembélé",
        "kounde jules": "Jules Koundé",
        "doué désiré": "Désiré Doué",
        "simon unai": "Unai Simón",
        "cubarsi pau": "Pau Cubarsí",
        "ruiz fabian": "Fabián Ruiz",
        "baena alex": "Álex Baena",
    }
    for alias, name in aliases.items():
        names[" ".join(sorted(norm(alias).split()))] = name
    return names, roles


CANONICAL, ROLES = canonical_roster()


def player_name(raw: str) -> str | None:
    key = " ".join(sorted(norm(raw).split()))
    return CANONICAL.get(key)


def pct_pair(text: str, label: str) -> tuple[float, float]:
    m = re.search(rf"([\d.]+)%\s+{re.escape(label)}\s+([\d.]+)%", text)
    if not m:
        raise ValueError(f"Cannot parse percentage pair for {label}")
    return float(m.group(1)), float(m.group(2))


def num_pair(text: str, label: str) -> tuple[float, float]:
    m = re.search(rf"([\d.]+)\s+{re.escape(label)}\s+([\d.]+)", text)
    if not m:
        raise ValueError(f"Cannot parse numeric pair for {label}")
    return float(m.group(1)), float(m.group(2))


def longest_table_text(page: pdfplumber.page.Page) -> str:
    cells = [str(cell) for table in page.extract_tables() for row in table for cell in row if cell]
    return max(cells, key=len) if cells else (page.extract_text() or "")


def parse_team_report(path: Path) -> tuple[list[dict], list[dict]]:
    reader = PdfReader(str(path))
    page0 = (reader.pages[0].extract_text() or "").replace("\x00", "f")
    date_match = re.search(r"(\d{1,2} [A-Za-z]+ 2026)", page0)
    match_date = datetime.strptime(date_match.group(1), "%d %B %Y").date().isoformat()
    duration = DURATION.get(path.name, 90)

    key = " ".join((reader.pages[2].extract_text() or "").split())
    teams = re.search(r"Key Statistics\s+(.+?)\s+(.+?)\s+Possession", key)
    if not teams:
        raise ValueError(f"Cannot parse teams from {path.name}")
    team_a, team_b = teams.group(1), teams.group(2)

    pos = re.search(r"Possession Total ([\d.]+)% ([\d.]+)% ([\d.]+)% Total", key)
    values: dict[str, tuple[float, float]] = {
        "goals": num_pair(key, "Goals"),
        "xg": num_pair(key, "xG (Expected Goals)"),
        "pass_completion_pct": num_pair(key, "% Pass Completion %"),
        "completed_line_breaks": num_pair(key, "Completed Line Breaks"),
        "defensive_line_breaks": num_pair(key, "Defensive Line Breaks"),
        "final_third_receptions": num_pair(key, "Receptions in the Final Third"),
        "crosses": num_pair(key, "Crosses"),
        "ball_progressions": num_pair(key, "Ball Progressions"),
        "forced_turnovers": num_pair(key, "Forced Turnovers"),
        "second_balls": num_pair(key, "Second Balls"),
    }
    attempts = re.search(r"(\d+) \((\d+)\) Attempts at Goal \(On Target\) (\d+) \((\d+)\)", key)
    passstats = re.search(r"(\d+) \((\d+)\) Total Passes \(Complete\) (\d+) \((\d+)\)", key)
    pressure = re.search(r"(\d+) \((\d+)\) Defensive Pressures Applied \(Direct Pressures\) (\d+) \((\d+)\)", key)
    distance = re.search(r"([\d.]+) km Total Distance Covered ([\d.]+) km", key)
    zone4 = re.search(r"([\d.]+) km Zone 4 .+?20-25 km/h ([\d.]+) km", key)

    phase_text = " ".join((reader.pages[3].extract_text() or "").split())
    phase_labels = [
        "Build Up Unopposed", "Build Up Opposed", "Progression", "Final Third",
        "Long Ball", "Attacking Transition", "Counter Attack", "Set Piece",
        "High Press", "Mid Press", "Low Press", "High Block", "Mid Block",
        "Low Block", "Recovery", "Defensive Transition", "Counter-press",
    ]
    phases: dict[str, tuple[float, float]] = {}
    for label in phase_labels:
        try:
            phases[label] = pct_pair(phase_text, label)
        except ValueError:
            phases[label] = (0.0, 0.0)

    extras: dict[str, dict[str, float]] = defaultdict(dict)
    for report_page in reader.pages:
        raw_page_text = " ".join((report_page.extract_text() or "").split())
        for team in (team_a, team_b):
            if f"Set Plays {team}" in raw_page_text:
                for metric, label in (("set_plays", "Total Set Plays"),
                                      ("free_kicks", "Total Free Kicks"),
                                      ("penalties", "Total Penalties"),
                                      ("corners", "Total Corners"),
                                      ("throw_ins", "Total Throw Ins")):
                    match = re.search(rf"(\d+)\s+{label}", raw_page_text)
                    if match:
                        extras[team][metric] = float(match.group(1))
            if f"Defensive Actions {team}" in raw_page_text:
                patterns = {
                    "possession_regains": r"(\d+) Possession Regained",
                    "interceptions": r"(\d+) Interceptions",
                    "tackles": r"(\d+) Tackles",
                }
                for metric, pattern in patterns.items():
                    match = re.search(pattern, raw_page_text)
                    if match:
                        extras[team][metric] = float(match.group(1))

    rows: list[dict] = []
    for idx, (team, opponent) in enumerate(((team_a, team_b), (team_b, team_a))):
        other = 1 - idx
        row = {
            "report": path.name,
            "date": match_date,
            "team": team,
            "opponent": opponent,
            "duration_minutes": duration,
            "possession_active_pct": float(pos.group(1 if idx == 0 else 3)),
            "possession_contested_pct": float(pos.group(2)),
            "attempts": int(attempts.group(1 if idx == 0 else 3)),
            "shots_on_target": int(attempts.group(2 if idx == 0 else 4)),
            "attempts_against": int(attempts.group(3 if idx == 0 else 1)),
            "shots_on_target_against": int(attempts.group(4 if idx == 0 else 2)),
            "passes": int(passstats.group(1 if idx == 0 else 3)),
            "passes_complete": int(passstats.group(2 if idx == 0 else 4)),
            "passes_against": int(passstats.group(3 if idx == 0 else 1)),
            "passes_complete_against": int(passstats.group(4 if idx == 0 else 2)),
            "pressures": int(pressure.group(1 if idx == 0 else 3)),
            "direct_pressures": int(pressure.group(2 if idx == 0 else 4)),
            "distance_km": float(distance.group(1 + idx)),
            "zone4_km": float(zone4.group(1 + idx)),
        }
        for label, pair in values.items():
            row[label] = pair[idx]
            row[label + "_against"] = pair[other]
        for label, pair in phases.items():
            row["phase_" + norm(label).replace(" ", "_")] = pair[idx]
        row.update(extras.get(team, {}))
        for metric, value in extras.get(opponent, {}).items():
            row[metric + "_against"] = value
        for metric in (
            "goals", "xg", "attempts", "shots_on_target", "attempts_against", "shots_on_target_against", "passes",
            "completed_line_breaks", "defensive_line_breaks", "final_third_receptions",
            "crosses", "ball_progressions", "pressures", "direct_pressures",
            "forced_turnovers", "second_balls", "distance_km", "zone4_km",
            "set_plays", "free_kicks", "penalties", "corners", "throw_ins",
            "possession_regains", "interceptions", "tackles",
        ):
            row[metric + "_per90"] = row.get(metric, 0.0) * 90.0 / duration
        rows.append(row)

    player_rows: list[dict] = []
    distribution_pages = []
    for page_idx, reader_page in enumerate(reader.pages):
        title = " ".join((reader_page.extract_text() or "").split()[:6])
        if "In Possession - Distributions" in title:
            distribution_pages.append((page_idx, title))
    with pdfplumber.open(path) as pdf:
        for page_idx, title in distribution_pages:
            page = pdf.pages[page_idx]
            team = next((candidate for candidate in TEAMS if candidate in title), None)
            if team is None:
                continue
            table_text = longest_table_text(page)
            for line in table_text.splitlines():
                m = re.match(
                    r"^(\d+) (.+?) (\d+) (\d+) (\d+)% (\d+) (\d+) (\d+) "
                    r"(\d+) (\d+) (\d+)% (\d+) (\d+) (\d+) (\d+) (\d+)$", line
                )
                if not m:
                    continue
                name = player_name(m.group(2))
                if not name:
                    continue
                nums = [int(m.group(i)) for i in range(3, 17)]
                fields = [
                    "passes_attempted", "passes_completed", "pass_completion_pct",
                    "switches", "crosses_attempted", "crosses_completed",
                    "line_breaks_attempted", "line_breaks_completed", "line_break_completion_pct",
                    "ball_progressions", "take_ons", "step_ins", "attempts", "goals",
                ]
                record = {"report": path.name, "date": match_date, "team": team,
                          "player": name, "role": ROLES.get(name, "UNK"),
                          "duration_match": duration}
                record.update(dict(zip(fields, nums)))
                player_rows.append(record)

    # Reconstruct minutes from shared substitution timestamps on the team sheet.
    line_text = (reader.pages[1].extract_text() or "").splitlines()
    for team in TEAMS:
        if team not in (team_a, team_b):
            continue
        target_players = [r for r in player_rows if r["team"] == team]
        for record in target_players:
            record["minutes"] = duration if record["player"] in {
                # conservative fallback, corrected below from the event row
                r["player"] for r in target_players
            } else 0

        player_info: dict[str, dict] = {}
        # Determine team order and slice its STARTING/SUBSTITUTES section.
        start_marks = [i for i, line in enumerate(line_text) if line == "STARTING"]
        sub_marks = [i for i, line in enumerate(line_text) if line == "SUBSTITUTES"]
        side = 0 if team == team_a else 1
        section_start = start_marks[side] + 1
        section_sub = sub_marks[side]
        section_end = start_marks[side + 1] if side == 0 else len(line_text)
        for is_starter, segment in ((True, line_text[section_start:section_sub]),
                                    (False, line_text[section_sub + 1:section_end])):
            for line in segment:
                found = None
                for canonical in ROLES:
                    compact_name = norm(canonical).replace(" ", "")
                    compact_line = norm(line).replace(" ", "")
                    if compact_name in compact_line:
                        found = canonical
                        break
                if found and found in {r["player"] for r in target_players}:
                    times = [min(int(x), duration) for x in re.findall(r"(\d+)(?:\+\d+)?'", line)]
                    player_info[found] = {"starter": is_starter, "times": times}
        starter_times = defaultdict(int)
        sub_times = defaultdict(int)
        for info in player_info.values():
            for minute in info["times"]:
                (starter_times if info["starter"] else sub_times)[minute] += 1
        shared = set(starter_times) & set(sub_times)
        for record in target_players:
            info = player_info.get(record["player"], {"starter": False, "times": []})
            shared_times = sorted(set(info["times"]) & shared)
            if info["starter"]:
                on, off = 0, (shared_times[0] if shared_times else duration)
            else:
                on, off = (shared_times[0] if shared_times else duration), duration
            record["starter"] = bool(info["starter"])
            record["minutes"] = max(0, off - on)
            for metric in ("attempts", "goals", "passes_attempted", "passes_completed",
                           "crosses_attempted", "line_breaks_completed", "ball_progressions",
                           "take_ons", "step_ins"):
                record[metric + "_per90"] = record[metric] * 90.0 / max(record["minutes"], 15)
    return rows, player_rows


def main() -> None:
    CURATED.mkdir(parents=True, exist_ok=True)
    team_rows: list[dict] = []
    player_rows: list[dict] = []
    for path in sorted(RAW.glob("PMSR-*.pdf")):
        t, p = parse_team_report(path)
        team_rows.extend(r for r in t if r["team"] in TEAMS)
        player_rows.extend(p)

    team_path = CURATED / "fifa_2026_final_four_team_match_features.csv"
    player_path = CURATED / "fifa_2026_final_four_player_match_features.csv"
    for path, rows in ((team_path, team_rows), (player_path, player_rows)):
        with path.open("w", encoding="utf-8-sig", newline="") as fh:
            writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
    print(json.dumps({"team_rows": len(team_rows), "player_rows": len(player_rows),
                      "team_output": str(team_path), "player_output": str(player_path)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
