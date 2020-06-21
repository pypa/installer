"""Compatibility cover for importlib.resources, for older Python versions."""

from __future__ import absolute_import

import sys

__all__ = ["read_binary"]

if sys.version_info >= (3, 7):  # pragma: no cover
    from importlib.resources import read_binary
else:  # pragma: no cover
    from importlib_resources import read_binary
