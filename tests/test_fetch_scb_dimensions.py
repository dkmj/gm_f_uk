# tests/test_fetch_scb_dimensions.py
"""Tester för SCB-dimensionshämtning."""
import json
from pathlib import Path


def test_parse_dimension_response():
    """PxWeb API-svar ska parsas till year/value-lista."""
    from scripts.fetch_scb_dimensions import parse_dimension_response

    api_response = {
        "data": [
            {"key": ["0380", "2020"], "values": ["233839"]},
            {"key": ["0380", "2021"], "values": ["236842"]},
        ],
    }

    result = parse_dimension_response(api_response)
    assert len(result) == 2
    assert result[0] == {"year": 2020, "value": 233839}
    assert result[1] == {"year": 2021, "value": 236842}


def test_parse_float_values():
    """Decimalvärden ska hanteras korrekt."""
    from scripts.fetch_scb_dimensions import parse_dimension_response

    api_response = {
        "data": [
            {"key": ["0380", "2020"], "values": ["8.5"]},
        ],
    }

    result = parse_dimension_response(api_response)
    assert result[0]["value"] == 8.5


def test_build_dimensions_data():
    """Dimensionsdata ska struktureras per dimension med year/value."""
    from scripts.fetch_scb_dimensions import build_dimensions_data

    raw = {
        "population": [
            {"year": 2020, "value": 233839},
            {"year": 2021, "value": 236842},
        ],
        "vehicles_total": [
            {"year": 2020, "value": 98500},
        ],
    }

    result = build_dimensions_data(raw)
    assert "population" in result
    assert result["population"][2020] == 233839
    assert result["population"][2021] == 236842
    assert result["vehicles_total"][2020] == 98500


def test_save_scb_dimensions(tmp_path):
    """Data ska sparas som JSON och sources.json ska uppdateras."""
    from scripts.fetch_scb_dimensions import save_scb_dimensions

    dimensions = {
        "population": {2020: 233839},
        "vehicles_total": {2020: 98500},
    }

    output = tmp_path / "scb_dimensions.json"
    sources = tmp_path / "sources.json"
    sources.write_text("[]", encoding="utf-8")

    save_scb_dimensions(dimensions, output, sources)

    assert output.exists()
    data = json.loads(output.read_text(encoding="utf-8"))
    assert "population" in data
    assert data["population"]["2020"] == 233839

    src = json.loads(sources.read_text(encoding="utf-8"))
    assert any(s["source_id"] == "scb_dimensions" for s in src)
