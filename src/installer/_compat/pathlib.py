import sys

__all__ = ["Path", "PurePath", "PurePosixPath"]

if sys.version_info >= (3, 4):  # pragma: no cover
    from pathlib import Path, PurePath, PurePosixPath
else:  # pragma: no cover
    from pathlib2 import Path, PurePath, PurePosixPath
