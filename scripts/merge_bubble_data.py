#!/usr/bin/env python3
"""Slå ihop NVV-sektorsdata + SCB-dimensioner → data/bubble_data.json."""
import json
from datetime import date
from pathlib import Path

AREA_DIMENSIONS = {
    "Transport": ["vehicles_total", "vehicles_electric_pct", "public_transport_trips"],
    "Energi": ["energy_gwh"],
    "Bygg och anläggning": ["energy_gwh", "building_area_m2", "new_construction_units"],
    "Jord- och skogsbruk": ["agriculture_hectares"],
    "Konsumtion": [],
    "Övriga områden": [],
}

SHARED_DIMENSIONS = ["population", "co2e_per_capita"]

DIMENSION_METADATA = {
    "co2e_kton": {"label": "CO₂e-utsläpp (kton)", "unit": "kton", "description": "Territoriella växthusgasutsläpp"},
    "share_pct": {"label": "Andel av totala utsläpp (%)", "unit": "%", "description": "Sektorns andel av kommunens totala utsläpp"},
    "population": {"label": "Befolkning", "unit": "invånare", "description": "Uppsalas folkmängd"},
    "co2e_per_capita": {"label": "CO₂e per capita (ton)", "unit": "ton/invånare", "description": "Totala kommunala utsläpp per invånare"},
    "vehicles_total": {"label": "Antal fordon", "unit": "fordon", "description": "Personbilar i trafik i kommunen"},
    "vehicles_electric_pct": {"label": "Andel elbilar (%)", "unit": "%", "description": "Andel laddbara fordon av totala fordonsflottan"},
    "energy_gwh": {"label": "Energianvändning (GWh)", "unit": "GWh", "description": "Total energianvändning"},
    "building_area_m2": {"label": "Bostadsyta (tusen m²)", "unit": "tusen m²", "description": "Total bostadsyta i kommunen"},
    "new_construction_units": {"label": "Nybyggda lägenheter", "unit": "lägenheter", "description": "Färdigställda lägenheter per år"},
    "public_transport_trips": {"label": "Kollektivtrafikresor per invånare", "unit": "resor/invånare", "description": "Antal kollektivtrafikresor per invånare och år"},
    "agriculture_hectares": {"label": "Jordbruksmark (hektar)", "unit": "hektar", "description": "Åker- och betesmark i kommunen"},
}

ALL_SCB_DIMENSIONS = [
    "population", "vehicles_total", "vehicles_electric_pct", "energy_gwh",
    "building_area_m2", "new_construction_units", "public_transport_trips",
    "agriculture_hectares",
]


def merge_bubble_data(nvv_file: Path, scb_file: Path, output_file: Path) -> dict:
    """Slå ihop NVV-sektorsdata med SCB-dimensioner."""
    nvv = json.loads(nvv_file.read_text(encoding="utf-8"))
    scb = json.loads(scb_file.read_text(encoding="utf-8")) if scb_file.exists() else {}

    area_year = {}
    for row in nvv["sectors"]:
        key = (row["area"], row["year"])
        if key in area_year:
            area_year[key]["co2e_kton"] += row["co2e_kton"]
            area_year[key]["share_pct"] += row["share_pct"]
        else:
            area_year[key] = {
                "area": row["area"],
                "year": row["year"],
                "co2e_kton": row["co2e_kton"],
                "share_pct": row["share_pct"],
            }

    yearly_totals = {}
    for (area, year), row in area_year.items():
        yearly_totals[year] = yearly_totals.get(year, 0) + row["co2e_kton"]

    data = []
    for (area, year), row in sorted(area_year.items()):
        year_str = str(year)
        area_dims = AREA_DIMENSIONS.get(area, [])
        all_dims = SHARED_DIMENSIONS + area_dims

        entry = {
            "area": area,
            "year": year,
            "co2e_kton": round(row["co2e_kton"], 1),
            "share_pct": round(row["share_pct"], 1),
        }

        for dim in ALL_SCB_DIMENSIONS + ["co2e_per_capita"]:
            if dim == "co2e_per_capita":
                pop = scb.get("population", {}).get(year_str)
                total = yearly_totals.get(year)
                if pop and total:
                    entry["co2e_per_capita"] = round(total * 1000 / pop, 2)
                else:
                    entry["co2e_per_capita"] = None
            elif dim in all_dims or dim in SHARED_DIMENSIONS:
                entry[dim] = scb.get(dim, {}).get(year_str)
            else:
                entry[dim] = None

        data.append(entry)

    sources_used = ["nvv_kommun_co2.json"]
    if scb:
        sources_used.append("scb_dimensions.json")

    result = {
        "metadata": {
            "generated": str(date.today()),
            "sources": sources_used,
            "dimensions": DIMENSION_METADATA,
        },
        "data": data,
    }

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    data_dir = Path("data")
    result = merge_bubble_data(
        data_dir / "nvv_kommun_co2.json",
        data_dir / "scb_dimensions.json",
        data_dir / "bubble_data.json",
    )
    print(f"Sammanfogade {len(result['data'])} rader till data/bubble_data.json")
    print(f"Dimensioner: {list(result['metadata']['dimensions'].keys())}")
