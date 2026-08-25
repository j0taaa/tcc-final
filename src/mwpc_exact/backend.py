"""Parser backend selection shared by reference and production orchestration."""

from enum import StrEnum


class ExactBackend(StrEnum):
    """Available finite-lattice parser implementations."""

    PYTHON = "python"
    RUST = "rust"


__all__ = ["ExactBackend"]
