__all__ = ["Path", "PurePath", "PurePosixPath"]

import sys

if sys.version_info >= (3, 4):  # pragma: no cover
    from pathlib import Path, PurePath, PurePosixPath
else:  # pragma: no cover
    from pathlib2 import Path, PurePath, PurePosixPath
