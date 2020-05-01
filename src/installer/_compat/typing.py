__all__ = ["TYPE_CHECKING"]

try:  # pragma: no cover
    from typing import TYPE_CHECKING
except ImportError:  # pragma: no cover
    TYPE_CHECKING = False
