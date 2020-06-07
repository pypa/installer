"""Static Typing Support logic

This is shim logic allows this library to use mypy, for static type analysis, while:

- not importing the 'typing' module at runtime.
- maintaining Python 2 support
- not completely confusing mypy :)
"""

__all__ = ["Text", "Binary", "TYPE_CHECKING"]

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
