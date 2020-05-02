from __future__ import absolute_import

import sys

__all__ = ["binary_type", "text_type"]


if sys.version_info >= (3,):  # pragma: no cover
    binary_type = bytes
    text_type = str
else:  # pragma: no cover
    binary_type = str
    text_type = unicode  # noqa
