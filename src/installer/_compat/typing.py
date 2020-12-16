"""Static Typing Support logic.

This is shim logic allows this library to use mypy, for static type analysis, while:

- not importing the 'typing' module at runtime.
- maintaining Python 2 support
- not completely confusing mypy :)

This module also provides `FSPath`, a type annotation for Path-like values, which
can only be imported inside an `if TYPE_CHECKING`, and used only in type comments.
"""

__all__ = ["cast", "Text", "Binary", "FSPath", "TYPE_CHECKING"]

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

# typing's cast syntax requires calling typing.cast at runtime, but we don't
# want to import typing at runtime. Here, we inform the type checkers that
# we're importing `typing.cast` as `cast` and re-implement typing.cast's
# runtime behavior in a block that is ignored by type checkers.
if TYPE_CHECKING:  # pragma: no cover
    # not executed at runtime
    from typing import cast
else:
    # executed at runtime
    def cast(type_, value):  # noqa
        return value
