"""Compatibility utilities for supporting multiple Python versions."""


try:  # pragma: no cover
    FileExistsError = FileExistsError
except NameError:  # pragma: no cover
    FileExistsError = OSError  # type: ignore
