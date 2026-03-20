"""Tester för merge av NVV + SCB → bubble_data.json."""
import json
from pathlib import Path


def test_merge_produces_valid_format(tmp_path):
    """Merge ska producera bubble_data.json med metadata och data."""
    from scripts.merge_bubble_data import merge_bubble_data

    nvv_data = {
        "sectors": [
            {"area": "Transport", "year": 2020, "co2e_kton": 285, "share_pct": 45.2, "source_id": "nvv"},
            {"area": "Energi", "year": 2020, "co2e_kton": 135, "share_pct": 21.4, "source_id": "nvv"},
        ]
    }
    scb_data = {
        "population": {"2020": 233839},
        "vehicles_total": {"2020": 98500},
        "vehicles_electric_pct": {"2020": 8.2},
        "energy_gwh": {"2020": 4600},
        "building_area_m2": {"2020": 10500},
        "new_construction_units": {"2020": 1900},
        "public_transport_trips": {"2020": 142},
        "agriculture_hectares": {"2020": 41200},
    }

    nvv_file = tmp_path / "nvv.json"
    scb_file = tmp_path / "scb.json"
    output = tmp_path / "bubble_data.json"

    nvv_file.write_text(json.dumps(nvv_data, ensure_ascii=False), encoding="utf-8")
    scb_file.write_text(json.dumps(scb_data, ensure_ascii=False), encoding="utf-8")

    merge_bubble_data(nvv_file, scb_file, output)

    result = json.loads(output.read_text(encoding="utf-8"))

    assert "metadata" in result
    assert "dimensions" in result["metadata"]
    assert "sources" in result["metadata"]
    assert "data" in result
    assert len(result["data"]) == 2


def test_merge_sets_correct_dimensions(tmp_path):
    """Transport ska ha fordonsdata, Energi ska ha energidata."""
    from scripts.merge_bubble_data import merge_bubble_data

    nvv_data = {
        "sectors": [
            {"area": "Transport", "year": 2020, "co2e_kton": 285, "share_pct": 45.2, "source_id": "nvv"},
            {"area": "Energi", "year": 2020, "co2e_kton": 135, "share_pct": 21.4, "source_id": "nvv"},
        ]
    }
    scb_data = {
        "population": {"2020": 233839},
        "vehicles_total": {"2020": 98500},
        "vehicles_electric_pct": {"2020": 8.2},
        "energy_gwh": {"2020": 4600},
        "building_area_m2": {"2020": 10500},
        "new_construction_units": {"2020": 1900},
        "public_transport_trips": {"2020": 142},
        "agriculture_hectares": {"2020": 41200},
    }

    nvv_file = tmp_path / "nvv.json"
    scb_file = tmp_path / "scb.json"
    output = tmp_path / "bubble_data.json"

    nvv_file.write_text(json.dumps(nvv_data, ensure_ascii=False), encoding="utf-8")
    scb_file.write_text(json.dumps(scb_data, ensure_ascii=False), encoding="utf-8")

    merge_bubble_data(nvv_file, scb_file, output)
    result = json.loads(output.read_text(encoding="utf-8"))

    transport = next(d for d in result["data"] if d["area"] == "Transport")
    assert transport["vehicles_total"] == 98500
    assert transport["energy_gwh"] is None

    energi = next(d for d in result["data"] if d["area"] == "Energi")
    assert energi["energy_gwh"] == 4600
    assert energi["vehicles_total"] is None


def test_merge_calculates_co2e_per_capita(tmp_path):
    """co2e_per_capita ska beräknas från totala utsläpp / befolkning."""
    from scripts.merge_bubble_data import merge_bubble_data

    nvv_data = {
        "sectors": [
            {"area": "Transport", "year": 2020, "co2e_kton": 300, "share_pct": 60, "source_id": "nvv"},
            {"area": "Energi", "year": 2020, "co2e_kton": 200, "share_pct": 40, "source_id": "nvv"},
        ]
    }
    scb_data = {"population": {"2020": 250000}}

    nvv_file = tmp_path / "nvv.json"
    scb_file = tmp_path / "scb.json"
    output = tmp_path / "bubble_data.json"

    nvv_file.write_text(json.dumps(nvv_data, ensure_ascii=False), encoding="utf-8")
    scb_file.write_text(json.dumps(scb_data, ensure_ascii=False), encoding="utf-8")

    merge_bubble_data(nvv_file, scb_file, output)
    result = json.loads(output.read_text(encoding="utf-8"))

    # Totalt 500 kton = 500_000 ton / 250_000 inv = 2.0 ton/inv
    transport = next(d for d in result["data"] if d["area"] == "Transport")
    assert abs(transport["co2e_per_capita"] - 2.0) < 0.01


def test_merge_handles_missing_scb_year(tmp_path):
    """År utan SCB-data ska ge null för SCB-dimensioner."""
    from scripts.merge_bubble_data import merge_bubble_data

    nvv_data = {
        "sectors": [
            {"area": "Transport", "year": 2019, "co2e_kton": 290, "share_pct": 100, "source_id": "nvv"},
        ]
    }
    scb_data = {"population": {"2020": 233839}}

    nvv_file = tmp_path / "nvv.json"
    scb_file = tmp_path / "scb.json"
    output = tmp_path / "bubble_data.json"

    nvv_file.write_text(json.dumps(nvv_data, ensure_ascii=False), encoding="utf-8")
    scb_file.write_text(json.dumps(scb_data, ensure_ascii=False), encoding="utf-8")

    merge_bubble_data(nvv_file, scb_file, output)
    result = json.loads(output.read_text(encoding="utf-8"))

    row = result["data"][0]
    assert row["population"] is None
    assert row["co2e_per_capita"] is None
