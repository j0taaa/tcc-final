"""Check the compiled manuscript, rather than a prose estimate of its length."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def validate_build(pdf_info: str, latex_log: str, *, max_pages: int = 16) -> int:
    match = re.search(r"^Pages:\s+(\d+)\s*$", pdf_info, re.MULTILINE)
    if match is None:
        raise ValueError("pdfinfo did not report a page count")
    pages = int(match.group(1))
    if not 10 <= pages <= max_pages:
        raise ValueError(f"Compiled article has {pages} pages; required range is 10-{max_pages}")
    if re.search(r"Overfull \\[hv]box|undefined|Rerun to get cross-references right", latex_log):
        raise ValueError("Final LaTeX pass has overflow or unresolved references")
    return pages


def main() -> None:
    paper = Path(__file__).resolve().parents[1] / "paper"
    info = subprocess.run(
        ["pdfinfo", str(paper / "main.pdf")], check=True, text=True, capture_output=True
    ).stdout
    pages = validate_build(info, (paper / "main.log").read_text())
    print(f"Compiled article verified: {pages} pages, no overflow or unresolved references")


if __name__ == "__main__":
    main()
