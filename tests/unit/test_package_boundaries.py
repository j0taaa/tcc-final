from __future__ import annotations

import ast
from pathlib import Path


def test_runtime_package_does_not_import_unshipped_research_package() -> None:
    runtime_root = Path(__file__).parents[2] / "src" / "mwpc_exact"
    violations: list[str] = []
    for path in sorted(runtime_root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_names = tuple(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module is not None:
                imported_names = (node.module,)
            else:
                continue
            if any(
                name == "mwpc_research" or name.startswith("mwpc_research.")
                for name in imported_names
            ):
                violations.append(f"{path.relative_to(runtime_root)}:{node.lineno}")

    assert violations == []
