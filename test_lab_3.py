import os
from pathlib import Path
from core.models import ConversionRequest
from core.registry import execute, available_targets

# Important: import all converters so decorators can register them
import converters.structural
import converters.office

from unittest.mock import patch


def test_missing_tool_detection():
    """Demonstrates Lab 3 requirement: detecting missing tool."""
    print("\n--- Testing missing tool detection ---")

    # We use 'patch' to temporarily trick Python.
    # shutil.which will return None, and Path.exists will return False.
    with patch('shutil.which', return_value=None), \
            patch('converters.office.Path.exists', return_value=False):

        try:
            # Trigger the check directly
            converters.office.get_libreoffice_path()
            # If it didn't crash, the test failed
            print("FAIL: Tool absence was not detected!")
        except FileNotFoundError as e:
            print(f"SUCCESS: Tool absence correctly detected.\nError message: {e}")


def main():
    input_dir = Path("test-files")
    input_dir.mkdir(exist_ok=True)

    source_docx = input_dir / "dokument.docx"

    if not source_docx.exists():
        print(
            f"WARNING: Please place a valid Word document named '{source_docx.name}' in the '{input_dir}' directory to run this test.")
        return

    print(f"\nFound test file: {source_docx}")
    print(f"Available conversions for .docx: {available_targets(source_docx)}")

    # 1. Test DOCX -> PDF
    print("\n--- Step 1: DOCX -> PDF ---")
    req_pdf = ConversionRequest(
        source=source_docx,
        target_format=".pdf",
        output_dir=input_dir
    )

    print("Executing LibreOffice... This may take a few seconds.")
    try:
        pdf_path = execute(req_pdf)
        print(f"Successfully created PDF: {pdf_path}")
    except Exception as e:
        print(f"Conversion error: {e}")

    # 2. Test DOCX -> ODT
    print("\n--- Step 2: DOCX -> ODT ---")
    req_odt = ConversionRequest(
        source=source_docx,
        target_format=".odt",
        output_dir=input_dir
    )

    print("Executing LibreOffice... This may take a few seconds.")
    try:
        odt_path = execute(req_odt)
        print(f"Successfully created ODT: {odt_path}")
    except Exception as e:
        print(f"Conversion error: {e}")

    # 3. Test ODT -> PDF
    print("\n--- Step 3: ODT -> PDF ---")
    odt_path = odt_path.rename(input_dir / "document_copy.odt")

    req_odt_pdf = ConversionRequest(
        source=odt_path,
        target_format=".pdf",
        output_dir=input_dir
    )

    print(f"Available conversions for .odt: {available_targets(odt_path)}")

    print("Executing LibreOffice... This may take a few seconds.")
    try:
        odt_pdf_path = execute(req_odt_pdf)
        print(f"Successfully created PDF: {odt_pdf_path}")
    except Exception as e:
        print(f"Conversion error: {e}")


if __name__ == "__main__":
    # First, prove that we handle missing tool
    test_missing_tool_detection()

    # Then run the actual conversions
    main()
