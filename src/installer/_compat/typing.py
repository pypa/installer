"""Static Typing Support logic.

This is shim logic allows this library to use mypy, for static type analysis, while:

- not importing the 'typing' module at runtime.
- maintaining Python 2 support
- not completely confusing mypy :)

This module also provides `FSPath`, a type annotation for Path-like values, which
can only be imported inside an `if TYPE_CHECKING`, and used only in type comments.
"""

__all__ = ["Text", "Binary", "FSPath", "TYPE_CHECKING"]

import sys

try:  # pragma: no cover
    from typing import TYPE_CHECKING
except ImportError:  # pragma: no cover
    TYPE_CHECKING = False

if sys.version_info >= (3,):  # pragma: no cover
    Binary = bytes
    Text = str
else:  # pragma: no cover
    Binary = str
    Text = unicode  # noqa

# FSPath declaration (only for Python 2 support)
if TYPE_CHECKING:
    if sys.version_info[:2] >= (3, 4):
        from pathlib import Path
        from typing import Union

        FSPath = Union[Text, Path]
    else:
        FSPath = Text
