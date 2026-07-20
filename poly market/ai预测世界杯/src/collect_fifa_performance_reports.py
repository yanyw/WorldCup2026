"""Download point-in-time FIFA post-match reports for the 2026 final four.

Raw reports are immutable inputs for the historical event model.  The script
refuses to replace an existing file whose SHA-256 differs from the download.
"""

from __future__ import annotations

import hashlib
import json
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "raw" / "fifa_performance_reports_2026"

REPORTS = {
    "ENG_CRO_M22": "PMSR-M22-ENG-V-CRO.pdf",
    "ENG_GHA_M45": "PMSR-M45-ENG-V-GHA.pdf",
    "PAN_ENG_M67": "PMSR-M67-PAN-V-ENG.pdf",
    "ENG_COD_M80": "PMSR-M80-ENG-V-COD.pdf",
    "MEX_ENG_M92": "PMSR-M92-MEX-V-ENG.pdf",
    "NOR_ENG_M99": "PMSR-M99-NOR-V-ENG.pdf",
    "ARG_ALG_M19": "PMSR-M19-ARG-V-ALG.pdf",
    "ARG_AUT_M43": "PMSR-M43-ARG-V-AUT.pdf",
    "JOR_ARG_M70": "PMSR-M70-JOR-V-ARG.pdf",
    "ARG_CPV_M86": "PMSR-M86-ARG-V-CPV.pdf",
    "ARG_EGY_M95": "PMSR-M95-ARG-V-EGY.pdf",
    "ARG_SUI_M100": "PMSR-M100-ARG-V-SUI.pdf",
    "FRA_SEN_M17": "PMSR-M17-FRA-V-SEN.pdf",
    "FRA_IRQ_M42": "PMSR-M42-FRA-V-IRQ.pdf",
    "NOR_FRA_M61": "PMSR-M61-NOR-V-FRA.pdf",
    "FRA_SWE_M77": "PMSR-M77-FRA-V-SWE.pdf",
    "PAR_FRA_M89": "PMSR-M89-PAR-V-FRA.pdf",
    "FRA_MAR_M97": "PMSR-M97-FRA-V-MAR.pdf",
    "ESP_CPV_M14": "PMSR-M14-ESP-V-CPV.pdf",
    "ESP_KSA_M38": "PMSR-M38-ESP-V-KSA.pdf",
    "URU_ESP_M66": "PMSR-M66-URU-V-ESP.pdf",
    "ESP_AUT_M84": "PMSR-M84-ESP-V-AUT.pdf",
    "POR_ESP_M93": "PMSR-M93-POR-V-ESP.pdf",
    "ESP_BEL_M98": "PMSR-M98-ESP-V-BEL-ALT.pdf",
    "FRA_ESP_M101": "PMSR-M101-FRA-V-ESP.pdf",
    "ENG_ARG_M102": "PMSR-M102-ENG-V-ARG.pdf",
}

BASE = "https://www.fifatrainingcentre.com/media/native/tournaments/fifa-world-cup/2026/"


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def download(url: str, retries: int = 4) -> bytes:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=120) as response:
                return response.read()
        except Exception as exc:  # transient CDN truncation is common for these PDFs
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(1.5 * (attempt + 1))
    raise RuntimeError(f"failed to download {url}") from last_error


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    entries = []
    for key, filename in REPORTS.items():
        url = BASE + filename
        target = OUT / filename
        if target.exists():
            content = target.read_bytes()
        else:
            content = download(url)
            target.write_bytes(content)
        digest = sha256(content)
        entries.append(
            {
                "key": key,
                "filename": filename,
                "url": url,
                "bytes": len(content),
                "sha256": digest,
            }
        )

    manifest = {
        "downloaded_at_utc": datetime.now(timezone.utc).isoformat(),
        "cutoff": "2026-07-16T04:00:00Z",
        "source": "FIFA Training Centre post-match summary reports",
        "license_note": "Retained locally for research and reproducibility; source terms apply.",
        "reports": entries,
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps({"reports": len(entries), "directory": str(OUT)}, ensure_ascii=False))


if __name__ == "__main__":
    main()
