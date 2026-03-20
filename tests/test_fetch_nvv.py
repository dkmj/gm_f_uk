"""Tester för Naturvårdsverkets datapipeline."""
import json
from pathlib import Path


def test_convert_nvv_produces_valid_sectors_json(tmp_path):
    """Konverterad data ska följa sektorsdata-schemat."""
    from scripts.fetch_nvv import convert_nvv_to_json

    raw_data = [
        {"kommun": "Uppsala", "sektor": "Transporter", "år": 2020, "co2e_kton": 285.0},
        {"kommun": "Uppsala", "sektor": "Energi", "år": 2020, "co2e_kton": 150.0},
        {"kommun": "Uppsala", "sektor": "Transporter", "år": 2019, "co2e_kton": 295.0},
    ]

    output_file = tmp_path / "nvv_kommun_co2.json"
    result = convert_nvv_to_json(raw_data, output_file)

    assert output_file.exists()
    data = json.loads(output_file.read_text(encoding="utf-8"))

    assert "sectors" in data
    assert len(data["sectors"]) == 3

    first = data["sectors"][0]
    assert "area" in first
    assert "year" in first
    assert "co2e_kton" in first
    assert "share_pct" in first
    assert "source_id" in first
    assert first["source_id"] == "nvv_kommun_co2"


def test_convert_nvv_calculates_share_pct(tmp_path):
    """share_pct ska beräknas korrekt per år."""
    from scripts.fetch_nvv import convert_nvv_to_json

    raw_data = [
        {"kommun": "Uppsala", "sektor": "Transporter", "år": 2020, "co2e_kton": 300.0},
        {"kommun": "Uppsala", "sektor": "Energi", "år": 2020, "co2e_kton": 200.0},
    ]

    output_file = tmp_path / "nvv.json"
    convert_nvv_to_json(raw_data, output_file)
    data = json.loads(output_file.read_text(encoding="utf-8"))

    transport = next(s for s in data["sectors"] if s["area"] == "Transport")
    assert abs(transport["share_pct"] - 60.0) < 0.1

    energi = next(s for s in data["sectors"] if s["area"] == "Energi")
    assert abs(energi["share_pct"] - 40.0) < 0.1


def test_sector_name_mapping():
    """NVV-sektornamn ska mappas till klimatbudgetens områden."""
    from scripts.fetch_nvv import map_sector_name

    assert map_sector_name("Transporter") == "Transport"
    assert map_sector_name("El och fjärrvärme") == "Energi"
    assert map_sector_name("Jordbruk") == "Jord- och skogsbruk"
