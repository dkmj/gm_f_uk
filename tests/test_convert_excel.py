# tests/test_convert_excel.py
"""Tester för generisk Excel/CSV → JSON-konverterare."""
import json
from pathlib import Path

import pandas as pd


def test_convert_csv_to_json(tmp_path):
    """CSV-fil ska konverteras till JSON med korrekt struktur."""
    from scripts.convert_excel import convert_to_json

    csv_content = "area,year,co2e_kton\nTransport,2020,285\nEnergi,2020,150\n"
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content, encoding="utf-8")

    output_file = tmp_path / "output.json"
    convert_to_json(csv_file, output_file)

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert "data" in data
    assert len(data["data"]) == 2
    assert data["data"][0]["area"] == "Transport"


def test_convert_excel_to_json(tmp_path):
    """Excel-fil ska konverteras till JSON."""
    from scripts.convert_excel import convert_to_json

    df = pd.DataFrame({
        "area": ["Transport", "Energi"],
        "year": [2020, 2020],
        "co2e_kton": [285.0, 150.0],
    })
    excel_file = tmp_path / "test.xlsx"
    df.to_excel(excel_file, index=False)

    output_file = tmp_path / "output.json"
    convert_to_json(excel_file, output_file)

    data = json.loads(output_file.read_text(encoding="utf-8"))
    assert len(data["data"]) == 2
