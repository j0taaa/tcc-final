"""Keep new differential runs separate from immutable historical summaries."""

import json
import tempfile
from collections.abc import Iterable, Mapping
from pathlib import Path


def prepare_output_directory(requested: Path | None, summary_names: Iterable[str]) -> Path:
    directory = (requested or Path(tempfile.mkdtemp(prefix="mwpc-differential-"))).resolve()
    directory.mkdir(parents=True, exist_ok=True)
    for name in summary_names:
        destination = directory / Path(name).name
        if destination.exists():
            raise FileExistsError(f"refusing to overwrite existing summary: {destination}")
    return directory


def write_summary(directory: Path, name: str, summary: Mapping[str, object]) -> None:
    # Exclusive creation also protects concurrent runs that passed preflight.
    with (directory / Path(name).name).open("x", encoding="utf-8") as output:
        output.write(json.dumps(dict(summary), indent=2, sort_keys=True, allow_nan=False) + "\n")
