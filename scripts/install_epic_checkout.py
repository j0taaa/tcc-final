#!/usr/bin/env python3
"""Expose the read-only EPIC checkout to one Python environment.

The pinned upstream metadata is not valid PEP 621 (`project.authors` is a
string rather than a table), so recent setuptools cannot perform an editable
install. This script keeps the submodule unchanged and writes a `.pth` file
into the active environment instead.
"""

from __future__ import annotations

import argparse
import site
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EPIC_CHECKOUT = ROOT / "vendor" / "EPIC-Decoding"


def install_path_file(site_packages: Path, checkout: Path = EPIC_CHECKOUT) -> Path:
    """Write an environment-local path file for the pinned EPIC checkout."""
    if not (checkout / "constrained_diffusion" / "__init__.py").is_file():
        raise RuntimeError(f"EPIC checkout is not initialized: {checkout}")
    site_packages.mkdir(parents=True, exist_ok=True)
    path_file = site_packages / "epic_decoding_checkout.pth"
    path_file.write_text(f"{checkout.resolve()}\n", encoding="utf-8")
    return path_file


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--site-packages",
        type=Path,
        default=None,
        help="target site-packages directory; defaults to the active environment",
    )
    args = parser.parse_args()
    target = args.site_packages or Path(site.getsitepackages()[0])
    path_file = install_path_file(target)
    print(f"EPIC checkout exposed through {path_file}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
