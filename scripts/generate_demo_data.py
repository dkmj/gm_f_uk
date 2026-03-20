#!/usr/bin/env python3
"""Generera realistisk demodata baserad på Uppsalas utsläppsprofil.

Siffrorna är ungefärliga och baserade på publikt tillgänglig
information om kommunala utsläpp i Uppsala.
"""
import json
from pathlib import Path

from scripts.fetch_nvv import convert_nvv_to_json, update_sources_json

# Ungefärliga utsläpp per sektor för Uppsala kommun (kton CO2e)
# Baserat på Naturvårdsverkets kommunala data och Klimatkollen
DEMO_DATA = []

SECTORS = {
    "Transporter": [310, 305, 298, 295, 290, 285, 260, 270, 265, 255],
    "El och fjärrvärme": [160, 155, 148, 145, 140, 135, 130, 128, 122, 118],
    "Industri": [80, 78, 76, 75, 73, 70, 68, 67, 65, 62],
    "Jordbruk": [55, 55, 54, 54, 53, 52, 52, 51, 51, 50],
    "Produktanvändning": [40, 39, 38, 37, 36, 35, 34, 33, 32, 31],
    "Avfall": [25, 24, 23, 22, 21, 20, 19, 18, 17, 16],
}

YEARS = list(range(2015, 2025))

for sector_name, values in SECTORS.items():
    for year, value in zip(YEARS, values):
        DEMO_DATA.append({
            "kommun": "Uppsala",
            "sektor": sector_name,
            "år": year,
            "co2e_kton": value,
        })


if __name__ == "__main__":
    data_dir = Path("data")
    output = data_dir / "nvv_kommun_co2.json"
    result = convert_nvv_to_json(DEMO_DATA, output)
    update_sources_json(data_dir / "sources.json", len(result["sectors"]))
    print(f"Genererade {len(result['sectors'])} rader demodata till {output}")
