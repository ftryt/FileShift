import pytest
import subprocess
from core.models import ConversionRequest
from core.registry import execute, available_targets
import converters.structural
import converters.office


@pytest.fixture
def test_dir(tmp_path):
    """Pytest fixture: creates an isolated temporary directory for each test."""
    return tmp_path


# =====================================================================
# TEST 1: Polskie znaki i puste wartości
# =====================================================================
def test_csv_to_json_polish_and_empty(test_dir):
    """Test 1: Correct file with Polish characters and empty values."""
    csv_file = test_dir / "pracownicy.csv"
    # Tworzymy CSV z polskimi znakami i pustym polem (brak wieku dla Gęślą)
    csv_file.write_text("Imię,Wiek\nZażółć,35\nGęślą,\n", encoding="utf-8")

    req = ConversionRequest(source=csv_file, target_format=".json", output_dir=test_dir)
    result_path = execute(req)

    assert result_path.exists()
    content = result_path.read_text(encoding="utf-8")
    assert "Zażółć" in content
    assert "Gęślą" in content
    assert '""' in content  # Weryfikacja pustej wartości jako pustego stringa w JSON


# =====================================================================
# TEST 2: Poprawny plik w każdej wspieranej grupie
# =====================================================================
def test_docx_to_pdf_success_mocked(monkeypatch, test_dir):
    """Test 2: Group B/C conversion (mocked to run without LibreOffice installed)."""
    docx_file = test_dir / "dokument.docx"
    docx_file.touch()

    # Mockujemy ścieżkę do narzędzia (udajemy, że istnieje)
    monkeypatch.setattr(converters.office, "get_libreoffice_path", lambda: "dummy_path")

    # Mockujemy faktyczne wywołanie procesu w systemie
    def mock_run(*args, **kwargs):
        # Symulujemy, że LibreOffice wykonał pracę i utworzył PDF
        pdf_file = test_dir / "dokument.pdf"
        pdf_file.touch()
        # Zwracamy kod 0 (sukces)
        return subprocess.CompletedProcess(args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr(subprocess, "run", mock_run)

    req = ConversionRequest(source=docx_file, target_format=".pdf", output_dir=test_dir)
    result_path = execute(req)

    assert result_path.exists()
    assert result_path.suffix == ".pdf"


# =====================================================================
# TEST 3: Błędny lub uszkodzony plik
# =====================================================================
def test_corrupted_json(test_dir):
    """Test 3: Corrupted file handles error gracefully."""
    json_file = test_dir / "bad_data.json"
    # Piszemy ewidentnie błędny format JSON
    json_file.write_text("{ broken json, ]", encoding="utf-8")

    req = ConversionRequest(source=json_file, target_format=".csv", output_dir=test_dir)

    # Oczekujemy naszego kontrolowanego błędu, a nie wywalenia aplikacji
    with pytest.raises(ValueError, match="JSON file is corrupted"):
        execute(req)


# =====================================================================
# TEST 4: Nieobsługiwana para
# =====================================================================
def test_unsupported_format_pair(test_dir):
    """Test 4: Unsupported format pair is blocked at the logic level."""
    txt_file = test_dir / "dummy.txt"
    txt_file.touch()

    # .txt -> .json NIE JEST wspierane
    req = ConversionRequest(source=txt_file, target_format=".json", output_dir=test_dir)

    with pytest.raises(ValueError, match="Unsupported format pair"):
        execute(req)


# =====================================================================
# TEST 5: Brak LibreOffice/biblioteki
# =====================================================================
def test_missing_libreoffice(monkeypatch, test_dir):
    """Test 5: Missing external tool is safely detected."""

    # Podmieniamy funkcję na taką, która symuluje, że system nie ma programu
    def mock_missing_tool():
        raise FileNotFoundError("LibreOffice not found in system PATH.")

    monkeypatch.setattr(converters.office, "get_libreoffice_path", mock_missing_tool)

    docx_file = test_dir / "dummy.docx"
    docx_file.touch()

    req = ConversionRequest(source=docx_file, target_format=".pdf", output_dir=test_dir)

    with pytest.raises(FileNotFoundError, match="LibreOffice not found"):
        execute(req)


# =====================================================================
# TEST 6: Plik docelowy już istnieje
# =====================================================================
def test_target_file_overwrite(test_dir):
    """Test 6: Target file already exists (logic handles overwriting securely)."""
    csv_file = test_dir / "dane.csv"
    csv_file.write_text("Kolumna\nWartosc", encoding="utf-8")

    # Tworzymy "stary" plik docelowy, żeby zasymulować, że już istnieje
    existing_json = test_dir / "dane.json"
    existing_json.write_text("STARE_DANE", encoding="utf-8")

    # Krok przypominający działanie GUI po zaakceptowaniu nadpisania
    req = ConversionRequest(source=csv_file, target_format=".json", output_dir=test_dir)
    result_path = execute(req)

    assert result_path.exists()
    content = result_path.read_text(encoding="utf-8")

    # Weryfikujemy, że program skutecznie zniszczył stare dane i zapisał nowe
    assert "STARE_DANE" not in content
    assert "Wartosc" in content
