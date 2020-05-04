import sys

if sys.version_info >= (3, 4):  # pragma: no cover
    from pathlib import PurePosixPath
else:  # pragma: no cover
    from pathlib2 import PurePosixPath

__all__ = ["PurePosixPath"]
