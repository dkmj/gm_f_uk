#!/usr/bin/env python3
"""Hämta och konvertera Naturvårdsverkets kommunala utsläppsdata."""
import json
from pathlib import Path

SECTOR_MAP = {
    "Transporter": "Transport",
    "Personbilar": "Transport",
    "Tunga fordon": "Transport",
    "El och fjärrvärme": "Energi",
    "Uppvärmning": "Energi",
    "Egen uppvärmning av bostäder och lokaler": "Energi",
    "Energi": "Energi",
    "Industri": "Bygg och anläggning",
    "Arbetsmaskiner": "Bygg och anläggning",
    "Jordbruk": "Jord- och skogsbruk",
    "Avfall": "Övriga områden",
    "Produktanvändning": "Konsumtion",
    "Lösningsmedel": "Konsumtion",
}


def map_sector_name(nvv_name: str) -> str:
    """Mappa NVV:s sektornamn till klimatbudgetens sex områden."""
    return SECTOR_MAP.get(nvv_name, "Övriga områden")


def convert_nvv_to_json(raw_data: list[dict], output_file: Path) -> dict:
    """Konvertera rå NVV-data till sektorsdata-JSON."""
    yearly_totals: dict[int, float] = {}
    for row in raw_data:
        year = row["år"]
        yearly_totals[year] = yearly_totals.get(year, 0) + row["co2e_kton"]

    sectors = []
    for row in raw_data:
        year = row["år"]
        total = yearly_totals[year]
        share = (row["co2e_kton"] / total * 100) if total > 0 else 0

        sectors.append({
            "area": map_sector_name(row["sektor"]),
            "year": year,
            "co2e_kton": row["co2e_kton"],
            "share_pct": round(share, 1),
            "source_id": "nvv_kommun_co2",
        })

    result = {"sectors": sectors}
    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def update_sources_json(sources_file: Path, row_count: int) -> None:
    """Uppdatera sources.json med senaste hämtningsstatus."""
    from datetime import date

    if sources_file.exists():
        sources = json.loads(sources_file.read_text(encoding="utf-8"))
    else:
        sources = []

    entry = {
        "source_id": "nvv_kommun_co2",
        "source_name": "Naturvårdsverket — Kommunala utsläpp",
        "url": "https://www.naturvardsverket.se/data-och-statistik/klimat/",
        "fetch_script": "scripts/fetch_nvv.py",
        "last_fetched": str(date.today()),
        "format": "excel",
        "license": "Öppen data",
        "data_file": "data/nvv_kommun_co2.json",
        "row_count": row_count,
    }

    for i, s in enumerate(sources):
        if s.get("source_id") == "nvv_kommun_co2":
            sources[i] = entry
            break
    else:
        sources.append(entry)

    sources_file.write_text(json.dumps(sources, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Användning: uv run scripts/fetch_nvv.py <sökväg-till-excel>")
        print("Ladda ner Excel från Naturvårdsverkets webbplats först.")
        sys.exit(1)

    excel_path = Path(sys.argv[1])
    if not excel_path.exists():
        print(f"Filen {excel_path} hittades inte.")
        sys.exit(1)

    import pandas as pd

    df = pd.read_excel(excel_path)
    raw = df.to_dict("records")

    data_dir = Path("data")
    output = data_dir / "nvv_kommun_co2.json"
    result = convert_nvv_to_json(raw, output)

    sources_file = data_dir / "sources.json"
    update_sources_json(sources_file, len(result["sectors"]))

    print(f"Konverterade {len(result['sectors'])} rader till {output}")
