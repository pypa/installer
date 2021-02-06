"""Compatibility utilities for supporting multiple Python versions."""

try:  # pragma: no cover
    from configparser import ConfigParser  # type: ignore
except ImportError:  # pragma: no cover
    from backports.configparser import ConfigParser  # type: ignore # noqa

try:  # pragma: no cover
    FileExistsError = FileExistsError
except NameError:  # pragma: no cover
    FileExistsError = OSError  # type: ignore
