import abc
from enum import Enum

from installer._compat import with_metaclass
from installer._compat.typing import TYPE_CHECKING

if TYPE_CHECKING:
    from io import BufferedReader
    from typing import List, Sequence, Tuple

    from installer._compat.typing import Text, FSPath


Scheme = Enum("Scheme", ["purelib", "platlib", "headers", "scripts", "data"])


@with_metaclass(abc.ABCMeta)
class WheelSource(object):
    
    """Represents an installable wheel."""

    def __init__(self, distribution, version):
        # type: (Text, Text) -> None
        super(WheelSource, self).__init__()
        self.distribution = distribution
        self.version = version

    @property
    def dist_info_dir(self):
        """Name of the dist-info directory."""
        return u"{}-{}.dist-info".format(self.distribution, self.version)

    @property
    def data_dir(self):
        """Name of the data directory."""
        return u"{}-{}.data".format(self.distribution, self.version)

    @abc.abstractproperty
    def dist_info_filenames(self):
        # type: () -> List[FSPath]
        """Get names of all files in the dist-info directory.

        Sample usage/behavior::

            >>> wheel_source.dist_info_filenames
            ["INSTALLER", "METADATA", "WHEEL"]
        """
        raise NotImplementedError()

    @abc.abstractmethod
    def open_dist_info(self, filename):
        # type: (FSPath) -> BufferedReader
        """Get readable stream of data, from ``filename`` in the dist-info directory.

        Sample usage/behavior::

            >>> f = wheel_source.open_dist_info("INSTALLER")
            >>> f.read()
            'pip'
        """
        raise NotImplementedError()

    # All files in the wheel
    @abc.abstractmethod
    def iter_files(self):
        # type: () -> Iterator[Tuple[FSPath, BufferedReader]]
        """Sequential access to all contents of the wheel (including dist-info files).

        All paths must be posix-style paths (i.e. can be used with ``posixpath`` module)
        relative to the root of the wheel.

        Sample usage/behavior::

            >>> iterable = wheel_source.iter_files()
            >>> next(iterable)
            ('pkg-1.0.0.dist-info/METADATA', <...>)

        This method may be called multiple times, and each iterator returned must
        provide the same content upon reading from the streams.
        """
        raise NotImplementedError()


@with_metaclass(abc.ABCMeta)
class Destination(object):
    """Represents the location for installation.

    Subclasses are expected to handle script generation and rewriting of the
    RECORD file after installation.
    """

    @abc.abstractmethod
    def write_file(self, scheme, path, stream):
        # type: (Scheme, FSPath, BufferedReader) -> None
        """TODO: write a good one line description of this function.

        Example usage/behavior::

            >>> stream = open("__init__.py")
            >>> dest.write_file(Scheme.purelib, "__init__.py", stream)

        """
        raise NotImplementedError()

    @abc.abstractmethod
    def rewrite_record(self, scheme):
        # type: (Scheme) -> None
        """Rewrite RECORD, using information already provided via ``write_file`` calls.

        Example usage/behavior::

            >>> dest.write_file(Scheme.purelib, "__init__.py", stream1)
            >>> dest.write_file(Scheme.purelib, "awesome_wrapper.py", stream2)
            >>> dest.write_file(Scheme.purelib, "_awesome.pyd", stream3)
            >>> dest.rewrite_record(Scheme.purelib)

        """
        raise NotImplementedError()
