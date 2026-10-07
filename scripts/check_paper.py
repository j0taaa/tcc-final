"""Check the compiled manuscript, rather than a prose estimate of its length."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


def validate_build(
    pdf_info: str, latex_log: str, *, min_pages: int = 10, max_pages: int = 16
) -> int:
    match = re.search(r"^Pages:\s+(\d+)\s*$", pdf_info, re.MULTILINE)
    if match is None:
        raise ValueError("pdfinfo did not report a page count")
    pages = int(match.group(1))
    if not min_pages <= pages <= max_pages:
        raise ValueError(
            f"Compiled article has {pages} pages; required range is {min_pages}-{max_pages}"
        )
    if re.search(r"Overfull \\[hv]box|undefined|Rerun to get cross-references right", latex_log):
        raise ValueError("Final LaTeX pass has overflow or unresolved references")
    return pages


def main() -> None:
    paper = Path(__file__).resolve().parents[1] / "paper"
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--pdf", default="main.pdf")
    parser.add_argument("--min-pages", type=int, default=10)
    parser.add_argument("--max-pages", type=int, default=16)
    args = parser.parse_args()
    pdf = paper / args.pdf
    info = subprocess.run(["pdfinfo", str(pdf)], check=True, text=True, capture_output=True).stdout
    pages = validate_build(
        info,
        pdf.with_suffix(".log").read_text(),
        min_pages=args.min_pages,
        max_pages=args.max_pages,
    )
    print(f"Compiled article verified: {pages} pages, no overflow or unresolved references")


if __name__ == "__main__":
    main()
