"""Handles all file writing and post-installation processing."""

from installer._compat.typing import TYPE_CHECKING
from installer.records import RecordEntry

if TYPE_CHECKING:
    from typing import BinaryIO, Iterable

    from installer._compat.typing import FSPath
    from installer.utils import Scheme


class WheelDestination(object):
    """Represents the location for wheel installation.

    Subclasses are expected to handle script generation and rewriting of the
    RECORD file after installation.
    """

    def write_file(self, scheme, path, stream):
        # type: (Scheme, FSPath, BinaryIO) -> RecordEntry
        """TODO: write a good one line description of this function.

        Example usage/behaviour::

            >>> stream = open("__init__.py")
            >>> dest.write_file("purelib", "pkg/__init__.py", stream)

        """
        raise NotImplementedError

    def finalize_installation(self, scheme, records):
        # type: (Scheme, Iterable[RecordEntry]) -> None
        """Finalize installation, after all the files are written.

        This method is required to (re)write the RECORD file such that it includes
        all given ``records`` as well as any additional generated content (eg: scripts).

        Example usage/behaviour::

            >>> dest.finalize_installation("purelib")
            ...

        """
        raise NotImplementedError
