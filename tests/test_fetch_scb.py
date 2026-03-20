"""Tester för SCB:s datapipeline."""
import json
from pathlib import Path
from unittest.mock import patch, MagicMock


def test_parse_scb_response(tmp_path):
    """Parsning av SCB PxWeb API-svar ska ge korrekt JSON."""
    from scripts.fetch_scb import parse_scb_response

    api_response = {
        "columns": [
            {"code": "Region", "text": "region"},
            {"code": "Tid", "text": "år"},
            {"code": "ContentsCode", "text": "Folkmängd"},
        ],
        "data": [
            {"key": ["0380", "2020"], "values": ["233839"]},
            {"key": ["0380", "2021"], "values": ["236842"]},
        ],
    }

    result = parse_scb_response(api_response, "befolkning")
    assert len(result) == 2
    assert result[0]["year"] == 2020
    assert result[0]["value"] == 233839


def test_save_scb_data(tmp_path):
    """Sparad data ska följa rätt format och uppdatera sources.json."""
    from scripts.fetch_scb import save_scb_data

    data = [
        {"year": 2020, "value": 233839, "indicator": "befolkning"},
        {"year": 2021, "value": 236842, "indicator": "befolkning"},
    ]

    output_file = tmp_path / "scb_energy.json"
    sources_file = tmp_path / "sources.json"

    save_scb_data(data, output_file, sources_file)

    assert output_file.exists()
    saved = json.loads(output_file.read_text(encoding="utf-8"))
    assert "data" in saved
    assert len(saved["data"]) == 2

    assert sources_file.exists()
    sources = json.loads(sources_file.read_text(encoding="utf-8"))
    assert any(s["source_id"] == "scb_energy" for s in sources)
