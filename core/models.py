from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ConversionRequest:
    source: Path
    target_format: str
    output_dir: Path

    def validate(self, available_conversions: dict) -> None:
        """Validates input before attempting conversion."""
        if not self.source.is_file():
            raise FileNotFoundError(f"Input file not found: {self.source}")
        if not self.output_dir.is_dir():
            raise NotADirectoryError(f"Target directory not found: {self.output_dir}")

        key = (self.source.suffix.lower(), self.target_format.lower())

        if key not in available_conversions:
            raise ValueError(f"Unsupported format pair: {key[0]} -> {key[1]}")