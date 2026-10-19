from collections.abc import Callable
from pathlib import Path
from core.models import ConversionRequest

# Type describing the converter function: takes (source_file, target_folder) and returns (result_file)
Converter = Callable[[Path, Path], Path]

# Main registry storing supported conversions
REGISTRY: dict[tuple[str, str], Converter] = {}


def converter(source: str, target: str):
    """Decorator registering a converter for a specific pair of extensions."""

    def register(func: Converter) -> Converter:
        REGISTRY[(source.lower(), target.lower())] = func
        return func

    return register


def available_targets(source: Path) -> list[str]:
    """Returns a list of available target formats for a given file."""
    return sorted(target for (src, target) in REGISTRY if src == source.suffix.lower())


def execute(request: ConversionRequest) -> Path:
    """Executes the appropriate converter based on the request."""
    request.validate(REGISTRY)
    key = (request.source.suffix.lower(), request.target_format.lower())

    # Call the registered function
    convert_func = REGISTRY[key]
    return convert_func(request.source, request.output_dir)