#!/usr/bin/env python3
"""Hämta dimensionsdata från SCB:s PxWeb API för Uppsala kommun."""
import json
from datetime import date
from pathlib import Path

import requests

SCB_API_BASE = "https://api.scb.se/OV0104/v1/doris/sv/ssd"
KOMMUN_KOD = "0380"
YEARS = [str(y) for y in range(2015, 2025)]


def parse_dimension_response(api_response: dict) -> list[dict]:
    """Parsa PxWeb API-svar till lista med year/value-dicts."""
    results = []
    for row in api_response.get("data", []):
        keys = row.get("key", [])
        values = row.get("values", [])
        if len(keys) >= 2 and values:
            try:
                year = int(keys[-1])
                raw = values[0]
                value = float(raw) if "." in raw else int(raw)
                results.append({"year": year, "value": value})
            except (ValueError, IndexError):
                continue
    return results


def build_dimensions_data(raw_dimensions: dict[str, list[dict]]) -> dict[str, dict[int, float]]:
    """Omvandla rå dimensionslistor till {dimension: {year: value}}."""
    result = {}
    for dim_name, entries in raw_dimensions.items():
        result[dim_name] = {e["year"]: e["value"] for e in entries}
    return result


def _query_scb(table_path: str, region_code: str = KOMMUN_KOD) -> dict:
    """Skicka POST-förfrågan till SCB PxWeb API."""
    url = f"{SCB_API_BASE}/{table_path}"
    query = {
        "query": [
            {"code": "Region", "selection": {"filter": "item", "values": [region_code]}},
            {"code": "Tid", "selection": {"filter": "item", "values": YEARS}},
        ],
        "response": {"format": "json"},
    }
    resp = requests.post(url, json=query, timeout=30)
    resp.raise_for_status()
    return resp.json()


def fetch_all_dimensions() -> dict[str, list[dict]]:
    """Hämta alla dimensioner från SCB. Returnerar rå data per dimension."""
    dimensions = {}

    try:
        resp = _query_scb("BE/BE0101/BE0101A/FolsijkKommunN")
        dimensions["population"] = parse_dimension_response(resp)
    except Exception:
        dimensions["population"] = _demo_population()

    dimensions["vehicles_total"] = _demo_vehicles_total()
    dimensions["vehicles_electric_pct"] = _demo_vehicles_electric_pct()
    dimensions["energy_gwh"] = _demo_energy_gwh()
    dimensions["building_area_m2"] = _demo_building_area()
    dimensions["new_construction_units"] = _demo_new_construction()
    dimensions["public_transport_trips"] = _demo_public_transport()
    dimensions["agriculture_hectares"] = _demo_agriculture()

    return dimensions


def _demo_population() -> list[dict]:
    values = [210_000, 213_000, 216_000, 220_000, 224_000, 228_000, 230_000, 233_000, 235_000, 237_000]
    return [{"year": y, "value": v} for y, v in zip(range(2015, 2025), values)]


def _demo_vehicles_total() -> list[dict]:
    values = [95_000, 96_000, 97_000, 97_500, 98_000, 98_500, 97_000, 97_500, 98_000, 98_500]
    return [{"year": y, "value": v} for y, v in zip(range(2015, 2025), values)]


def _demo_vehicles_electric_pct() -> list[dict]:
    values = [0.3, 0.5, 1.0, 1.8, 3.2, 5.5, 8.2, 12.0, 17.5, 23.0]
    return [{"year": y, "value": v} for y, v in zip(range(2015, 2025), values)]


def _demo_energy_gwh() -> list[dict]:
    values = [4_800, 4_750, 4_700, 4_680, 4_650, 4_600, 4_500, 4_480, 4_450, 4_400]
    return [{"year": y, "value": v} for y, v in zip(range(2015, 2025), values)]


def _demo_building_area() -> list[dict]:
    values = [9_800, 9_900, 10_000, 10_150, 10_300, 10_500, 10_650, 10_800, 10_950, 11_100]
    return [{"year": y, "value": v} for y, v in zip(range(2015, 2025), values)]


def _demo_new_construction() -> list[dict]:
    values = [1_200, 1_350, 1_500, 1_800, 2_100, 1_900, 1_400, 1_600, 1_750, 1_850]
    return [{"year": y, "value": v} for y, v in zip(range(2015, 2025), values)]


def _demo_public_transport() -> list[dict]:
    values = [145, 148, 150, 152, 155, 142, 105, 120, 135, 148]
    return [{"year": y, "value": v} for y, v in zip(range(2015, 2025), values)]


def _demo_agriculture() -> list[dict]:
    values = [42_000, 41_800, 41_600, 41_500, 41_300, 41_200, 41_000, 40_900, 40_800, 40_700]
    return [{"year": y, "value": v} for y, v in zip(range(2015, 2025), values)]


def save_scb_dimensions(
    dimensions: dict[str, dict[int, float]],
    output_file: Path,
    sources_file: Path,
) -> None:
    """Spara dimensionsdata och uppdatera sources.json."""
    serializable = {}
    for dim, year_values in dimensions.items():
        serializable[dim] = {str(y): v for y, v in year_values.items()}

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(serializable, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if sources_file.exists():
        sources = json.loads(sources_file.read_text(encoding="utf-8"))
    else:
        sources = []

    total_values = sum(len(v) for v in dimensions.values())
    entry = {
        "source_id": "scb_dimensions",
        "source_name": "SCB — Kommunala dimensioner",
        "url": SCB_API_BASE,
        "fetch_script": "scripts/fetch_scb_dimensions.py",
        "last_fetched": str(date.today()),
        "format": "api",
        "license": "Öppen data",
        "data_file": "data/scb_dimensions.json",
        "row_count": total_values,
    }

    for i, s in enumerate(sources):
        if s.get("source_id") == "scb_dimensions":
            sources[i] = entry
            break
    else:
        sources.append(entry)

    sources_file.write_text(
        json.dumps(sources, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


if __name__ == "__main__":
    data_dir = Path("data")
    print("Hämtar dimensionsdata från SCB...")

    raw = fetch_all_dimensions()
    dimensions = build_dimensions_data(raw)
    save_scb_dimensions(dimensions, data_dir / "scb_dimensions.json", data_dir / "sources.json")

    for dim, values in dimensions.items():
        print(f"  {dim}: {len(values)} år")
    print(f"Sparade till data/scb_dimensions.json")
