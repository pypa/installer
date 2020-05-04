try:  # pragma: no cover
    from typing import TYPE_CHECKING
except ImportError:  # pragma: no cover
    TYPE_CHECKING = False

__all__ = ["TYPE_CHECKING"]
