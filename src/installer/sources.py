"""Source of information about a wheel file."""

from installer._compat.typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import BinaryIO, Iterator, List, Tuple

    from installer._compat.typing import FSPath, Text

    WheelContentElement = Tuple[Tuple[FSPath, str, str], BinaryIO]


class WheelSource(object):
    """Represents an installable wheel.

    This is an abstract class, whose methods have to be implemented by subclasses.
    """

    def __init__(self, distribution, version):
        # type: (Text, Text) -> None
        """Initialize a WheelSource object.

        :param distribution: distribution name (like ``urllib3``)
        :param version: version associated with the wheel
        """
        super(WheelSource, self).__init__()
        self.distribution = distribution
        self.version = version

    @property
    def dist_info_dir(self):
        """Name of the dist-info directory."""
        return "{}-{}.dist-info".format(self.distribution, self.version)

    @property
    def data_dir(self):
        """Name of the data directory."""
        return "{}-{}.data".format(self.distribution, self.version)

    @property
    def dist_info_filenames(self):
        # type: () -> List[FSPath]
        """Get names of all files in the dist-info directory.

        Sample usage/behaviour::

            >>> wheel_source.dist_info_filenames
            ['METADATA', 'WHEEL']
        """
        raise NotImplementedError

    def read_dist_info(self, filename):
        # type: (FSPath) -> Text
        """Get contents, from ``filename`` in the dist-info directory.

        Sample usage/behaviour::

            >>> wheel_source.read_dist_info("METADATA")
            ...

        :param filename: name of the file
        """
        raise NotImplementedError

    def get_contents(self):
        # type: () -> Iterator[WheelContentElement]
        """Sequential access to all contents of the wheel (including dist-info files).

        This method should return an iterable. Each value from the iterable must be a
        tuple containing 2 elements:

        - record: 3-value tuple, to pass to
          :py:meth:`Record.from_elements <installer.records.Record.from_elements>`.
        - stream: An :py:class:`io.BufferedReader` object, providing the contents of the
          file at the location provided by the first element (path).

        All paths must be relative to the root of the wheel.

        Sample usage/behaviour::

            >>> iterable = wheel_source.get_contents()
            >>> next(iterable)
            (('pkg/__init__.py', '', '0'), <...>)

        This method may be called multiple times. Each iterable returned must
        provide the same content upon reading from a specific file's stream.
        """
        raise NotImplementedError
