# tests/test_fetch_klimatkollen.py
"""Tester för Klimatkollen-datapipeline."""
import json
from pathlib import Path


def test_fetch_klimatkollen_returns_data():
    """Funktionen ska returnera en lista med utsläppsdata."""
    from scripts.fetch_klimatkollen import fetch_klimatkollen_municipality

    data = fetch_klimatkollen_municipality()
    assert isinstance(data, list)
    assert len(data) > 0
    assert "year" in data[0]
    assert "co2e_kton_total" in data[0]


def test_save_klimatkollen_data(tmp_path):
    """Data ska sparas korrekt och sources.json uppdateras."""
    from scripts.fetch_klimatkollen import save_klimatkollen_data

    data = [{"year": 2020, "co2e_kton_total": 570, "trend": "minskning", "source": "Klimatkollen"}]
    output = tmp_path / "klimatkollen.json"
    sources = tmp_path / "sources.json"

    save_klimatkollen_data(data, output, sources)

    assert output.exists()
    saved = json.loads(output.read_text(encoding="utf-8"))
    assert len(saved["data"]) == 1

    assert sources.exists()
    src = json.loads(sources.read_text(encoding="utf-8"))
    assert any(s["source_id"] == "klimatkollen" for s in src)
