import csv
import json
from pathlib import Path
from core.registry import converter


@converter(".csv", ".json")
def csv_to_json(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.json"

    try:
        # Read CSV (assuming the first row contains headers)
        with open(source, mode='r', encoding='utf-8-sig') as csv_file:
            reader = csv.DictReader(csv_file)
            data = list(reader)
    except UnicodeDecodeError:
        raise ValueError("Encoding error. Make sure the CSV file is saved as UTF-8.")

    # Write to JSON (ensure_ascii=False preserves Polish characters)
    with open(target, mode='w', encoding='utf-8') as json_file:
        json.dump(data, json_file, indent=4, ensure_ascii=False)

    return target


@converter(".json", ".csv")
def json_to_csv(source: Path, output_dir: Path) -> Path:
    target = output_dir / f"{source.stem}.csv"

    try:
        with open(source, mode='r', encoding='utf-8') as json_file:
            data = json.load(json_file)
    except json.JSONDecodeError as e:
        # Controlled message for corrupted JSON (Lab 2 requirement)
        raise ValueError(f"JSON file is corrupted or invalid: {e.msg}")
    except UnicodeDecodeError:
        raise ValueError("Encoding error. Make sure the JSON file is saved as UTF-8.")

    # Validate the defined JSON structure
    if not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError("Required format is an array of objects, e.g., [{\"column\": \"value\"}]")

    if not data:
        raise ValueError("JSON file is empty.")

    # Extract headers from the keys of the first dictionary in the list
    headers = list(data[0].keys())

    with open(target, mode='w', encoding='utf-8', newline='') as csv_file:
        writer = csv.DictWriter(csv_file, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)

    return target