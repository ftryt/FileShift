from pathlib import Path
from core.models import ConversionRequest
from core.registry import execute, available_targets

# NOTE: To make decorators work, we must import the module with converters!
import converters.structural


def main():
    # Prepare the test environment
    input_dir = Path("test-files")
    input_dir.mkdir(exist_ok=True)

    # 1. Create a sample CSV file (with Polish characters)
    sample_csv = input_dir / "pracownicy.csv"
    sample_csv.write_text("Imię,Stanowisko,Wiek\nMichał,Inżynier,30\nŻaneta,Główna Księgowa,45", encoding="utf-8")

    print(f"Created test file: {sample_csv}")
    print(f"Available conversions for .csv: {available_targets(sample_csv)}")

    # 2. Test conversion: CSV -> JSON
    print("\n--- Step 1: CSV -> JSON ---")
    req_to_json = ConversionRequest(
        source=sample_csv,
        target_format=".json",
        output_dir=input_dir
    )
    json_path = execute(req_to_json)
    print(f"Successfully saved: {json_path}")
    print(f"Content:\n{json_path.read_text(encoding='utf-8')}")

    # 3. Test reverse conversion: JSON -> CSV
    print("\n--- Step 2: JSON -> CSV ---")

    renamed_json_path = json_path.rename(input_dir / "pracownicy_odczyt.json")

    req_to_csv = ConversionRequest(
        source=renamed_json_path,
        target_format=".csv",
        output_dir=input_dir
    )

    csv_path = execute(req_to_csv)
    print(f"Successfully saved back to CSV: {csv_path}")
    print(f"Content:\n{csv_path.read_text(encoding='utf-8')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Controlled error occurred: {e}")