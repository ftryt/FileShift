import os
import subprocess
import shutil
from pathlib import Path
from core.registry import converter


def get_libreoffice_path() -> str:
    """Finds the LibreOffice executable in the system."""
    # 'soffice' is the command usually used on Windows, 'libreoffice' on Linux/macOS
    for cmd in ["libreoffice", "soffice", "soffice.exe"]:
        path = shutil.which(cmd)
        if path:
            return path

    # Hardcoded fallback for Windows (if PATH is not set)
    if os.name == 'nt':  # 'nt' means Windows
        windows_paths = [
            r"C:\Program Files\LibreOffice\program\soffice.exe",
            r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"
        ]

        for path in windows_paths:
            if Path(path).exists():
                return path

    # If tool is missing - detected and described
    raise FileNotFoundError(
        "LibreOffice not found in system PATH. "
        "Please install LibreOffice to enable document conversions."
    )


def run_libreoffice(source: Path, output_dir: Path, target_ext: str) -> Path:
    """Helper function to execute headless LibreOffice safely."""
    lo_path = get_libreoffice_path()

    # Remove the dot from extension for LibreOffice argument (e.g., '.pdf' -> 'pdf')
    target_format = target_ext.lstrip('.')

    command = [
        lo_path,
        "--headless",
        "--invisible",
        "--nologo",
        "--nodefault",
        "--nofirststartwizard",
        "--norestore",
        "--convert-to", target_format,
        "--outdir", str(output_dir),
        str(source)
    ]

    try:
        # Run the process
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,  # We will manually check the return code below
            timeout=60
        )
    except Exception as e:
        raise RuntimeError(f"Failed to execute the external tool: {e}")

    # Checking the exit code
    if result.returncode != 0:
        error_msg = result.stderr.strip() or result.stdout.strip()
        raise RuntimeError(f"Conversion failed with exit code {result.returncode}: {error_msg}")

    target = output_dir / f"{source.stem}{target_ext}"

    if not target.exists():
        raise RuntimeError("Tool executed successfully, but expected output file is missing.")

    return target


# Registering specific conversion directions
@converter(".docx", ".pdf")
def docx_to_pdf(source: Path, output_dir: Path) -> Path:
    return run_libreoffice(source, output_dir, ".pdf")


@converter(".odt", ".pdf")
def odt_to_pdf(source: Path, output_dir: Path) -> Path:
    return run_libreoffice(source, output_dir, ".pdf")


@converter(".docx", ".odt")
def docx_to_odt(source: Path, output_dir: Path) -> Path:
    return run_libreoffice(source, output_dir, ".odt")