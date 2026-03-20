#!/usr/bin/env python3
"""Generisk Excel/CSV → JSON-konverterare."""
import json
import sys
from pathlib import Path

import pandas as pd


def convert_to_json(input_file: Path, output_file: Path) -> dict:
    """Konvertera Excel eller CSV till JSON.

    Args:
        input_file: Sökväg till .xlsx, .xls eller .csv-fil.
        output_file: Sökväg att skriva JSON till.

    Returns:
        Den genererade datastrukturen.
    """
    suffix = input_file.suffix.lower()
    if suffix in (".xlsx", ".xls"):
        df = pd.read_excel(input_file)
    elif suffix == ".csv":
        df = pd.read_csv(input_file)
    else:
        raise ValueError(f"Format stöds ej: {suffix}. Använd .xlsx, .xls eller .csv.")

    records = df.to_dict("records")
    result = {"data": records}

    output_file.parent.mkdir(parents=True, exist_ok=True)
    output_file.write_text(
        json.dumps(result, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    return result


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Användning: uv run scripts/convert_excel.py <input.xlsx> <output.json>")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])
    result = convert_to_json(input_path, output_path)
    print(f"Konverterade {len(result['data'])} rader till {output_path}")
