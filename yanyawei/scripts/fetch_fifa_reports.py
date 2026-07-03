import concurrent.futures
import html
import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from pypdf import PdfReader


BASE = "https://www.fifatrainingcentre.com"
PAGES = {
    "group": f"{BASE}/en/fifa-world-cup-2026/match-report-hub.php",
    "knockout": f"{BASE}/en/fifa-world-cup-2026/match-report-hub-knockout-stage.php",
}
PROJECT = Path(__file__).resolve().parents[1]
ROOT = PROJECT / "data" / ".cache" / "fifa_reports"
OUTPUT = PROJECT / "data" / "fifa_match_stats_0702.json"
TARGETS = {
    "ESP", "AUT", "POR", "CRO", "SUI", "ALG", "AUS", "EGY", "ARG", "CPV",
    "COL", "GHA", "CAN", "MAR", "PAR", "FRA", "BRA", "NOR", "MEX", "ENG",
}
TEAM_NAMES = {
    "ESP": "Spain", "AUT": "Austria", "POR": "Portugal", "CRO": "Croatia",
    "SUI": "Switzerland", "ALG": "Algeria", "AUS": "Australia", "EGY": "Egypt",
    "ARG": "Argentina", "CPV": "Cabo Verde", "COL": "Colombia", "GHA": "Ghana",
    "CAN": "Canada", "MAR": "Morocco", "PAR": "Paraguay", "FRA": "France",
    "BRA": "Brazil", "NOR": "Norway", "MEX": "Mexico", "ENG": "England",
    "RSA": "South Africa", "JPN": "Japan", "GER": "Germany", "NED": "Netherlands",
    "CIV": "Cote d'Ivoire", "SWE": "Sweden", "ECU": "Ecuador", "COD": "Congo DR",
    "JOR": "Jordan", "URU": "Uruguay", "KSA": "Saudi Arabia", "UZB": "Uzbekistan",
    "PAN": "Panama", "BIH": "Bosnia and Herzegovina", "QAT": "Qatar", "QAR": "Qatar",
    "HAI": "Haiti", "SCO": "Scotland", "USA": "USA", "TUR": "Turkiye",
    "BEL": "Belgium", "IRN": "Iran", "NZL": "New Zealand", "IRQ": "Iraq",
    "SEN": "Senegal", "CUW": "Curacao", "CZE": "Czechia", "KOR": "South Korea",
    "UZB": "Uzbekistan",
}
NAME_TO_CODE = {name.casefold(): code for code, name in TEAM_NAMES.items()}
NAME_TO_CODE.update({
    "korea republic": "KOR", "ir iran": "IRN", "türkiye": "TUR", "turkiye": "TUR",
    "côte d'ivoire": "CIV", "curaçao": "CUW", "congo dr": "COD",
})


def fetch_text(url: str) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=45) as response:
        return response.read().decode("utf-8", errors="replace")


def discover_reports() -> list[dict]:
    reports = []
    for stage, page in PAGES.items():
        body = fetch_text(page)
        hrefs = re.findall(r'href=["\']([^"\']+\.pdf)["\']', body, re.I)
        for raw_href in hrefs:
            href = html.unescape(raw_href)
            filename = urllib.parse.unquote(Path(urllib.parse.urlparse(href).path).name)
            codes = [code for code in re.findall(r"[A-Z]{3}", filename.upper()) if code in TEAM_NAMES]
            if len(codes) >= 2 and TARGETS.intersection(codes):
                absolute = urllib.parse.urljoin(BASE, href)
                parsed_url = urllib.parse.urlsplit(absolute)
                safe_url = urllib.parse.urlunsplit(
                    (parsed_url.scheme, parsed_url.netloc, urllib.parse.quote(parsed_url.path), parsed_url.query, "")
                )
                reports.append({
                    "stage": stage,
                    "url": safe_url,
                    "filename": filename,
                    "home_code": codes[-2],
                    "away_code": codes[-1],
                })
    unique = {report["url"]: report for report in reports}
    return list(unique.values())


def download(report: dict) -> Path:
    ROOT.mkdir(parents=True, exist_ok=True)
    path = ROOT / report["filename"]
    if path.exists() and path.stat().st_size > 100_000:
        return path
    request = urllib.request.Request(report["url"], headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=90) as response:
        data = response.read()
    if not data.startswith(b"%PDF"):
        raise ValueError(f"Not a PDF: {report['url']}")
    path.write_bytes(data)
    return path


def parse_report(report: dict, path: Path) -> dict:
    reader = PdfReader(str(path))
    cover = reader.pages[0].extract_text() or ""
    stats = ""
    for page in reader.pages:
        text = page.extract_text() or ""
        if "xG (Expected Goals)" in text:
            stats = text
            break
    if not stats:
        raise ValueError(f"No statistics page in {path.name}")
    score = re.search(r"^(.+?)\s*(\d+)\s*-\s*(\d+)\s*\n(.+?)\n", cover, re.M)
    goals = re.search(r"(\d+)\s+Goals\s+(\d+)", stats)
    xg = re.search(r"([0-9.]+)\s+xG \(Expected Goals\)\s+([0-9.]+)", stats)
    shots = re.search(
        r"(\d+) \((\d+)\)\s+Attempts at Goal \(On Target\)\s+(\d+) \((\d+)\)",
        stats,
    )
    if not all((score, goals, xg, shots)):
        raise ValueError(f"Could not parse statistics in {path.name}")
    home_name = score.group(1).strip()
    away_name = score.group(4).strip()
    home_code = NAME_TO_CODE.get(home_name.casefold())
    away_code = NAME_TO_CODE.get(away_name.casefold())
    if not home_code or not away_code:
        raise ValueError(f"Unknown teams in {path.name}: {home_name} vs {away_name}")
    return {
        **report,
        "home_code": home_code,
        "away_code": away_code,
        "home": home_name,
        "away": away_name,
        "home_goals": int(goals.group(1)),
        "away_goals": int(goals.group(2)),
        "home_xg": float(xg.group(1)),
        "away_xg": float(xg.group(2)),
        "home_shots": int(shots.group(1)),
        "home_sot": int(shots.group(2)),
        "away_shots": int(shots.group(3)),
        "away_sot": int(shots.group(4)),
    }


def main() -> None:
    reports = discover_reports()
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
        paths = list(executor.map(download, reports))
    parsed = [parse_report(report, path) for report, path in zip(reports, paths)]
    parsed.sort(key=lambda item: (item["stage"], item["filename"]))
    OUTPUT.write_text(json.dumps(parsed, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {len(parsed)} reports to {OUTPUT}")


if __name__ == "__main__":
    main()
