#!/usr/bin/env python3
"""Hämta data från SCB:s PxWeb API."""
import json
from datetime import date
from pathlib import Path

import requests

SCB_API_BASE = "https://api.scb.se/OV0104/v1/doris/sv/ssd"
KOMMUN_KOD = "0380"


def parse_scb_response(api_response: dict, indicator: str) -> list[dict]:
    """Parsa SCB:s PxWeb API-svar till enkel lista."""
    results = []
    for row in api_response.get("data", []):
        keys = row.get("key", [])
        values = row.get("values", [])
        if len(keys) >= 2 and values:
            try:
                year = int(keys[-1])
                value = int(values[0]) if "." not in values[0] else float(values[0])
                results.append({
                    "year": year,
                    "value": value,
                    "indicator": indicator,
                })
            except (ValueError, IndexError):
                continue
    return results


def save_scb_data(data: list[dict], output_file: Path, sources_file: Path) -> None:
    """Spara SCB-data som JSON och uppdatera sources.json."""
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps({"data": data}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if sources_file.exists():
        sources = json.loads(sources_file.read_text(encoding="utf-8"))
    else:
        sources = []

    entry = {
        "source_id": "scb_energy",
        "source_name": "SCB — Energi och befolkning",
        "url": SCB_API_BASE,
        "fetch_script": "scripts/fetch_scb.py",
        "last_fetched": str(date.today()),
        "format": "api",
        "license": "Öppen data",
        "data_file": "data/scb_energy.json",
        "row_count": len(data),
    }

    for i, s in enumerate(sources):
        if s.get("source_id") == "scb_energy":
            sources[i] = entry
            break
    else:
        sources.append(entry)

    sources_file.write_text(
        json.dumps(sources, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def fetch_population() -> list[dict]:
    """Hämta befolkningsdata för Uppsala kommun från SCB."""
    url = f"{SCB_API_BASE}/BE/BE0101/BE0101A/FolkmijkdKommunN"
    query = {
        "query": [
            {"code": "Region", "selection": {"filter": "item", "values": [KOMMUN_KOD]}},
        ],
        "response": {"format": "json"},
    }

    resp = requests.post(url, json=query, timeout=30)
    resp.raise_for_status()
    return parse_scb_response(resp.json(), "befolkning")


if __name__ == "__main__":
    data_dir = Path("data")
    output = data_dir / "scb_energy.json"
    sources = data_dir / "sources.json"

    print("Hämtar befolkningsdata från SCB...")
    pop_data = fetch_population()

    save_scb_data(pop_data, output, sources)
    print(f"Sparade {len(pop_data)} rader till {output}")
