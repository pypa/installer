"""Source of information about a wheel file."""

import os
import posixpath
import zipfile
from contextlib import contextmanager

import installer.records
import installer.utils
from installer._compat.typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from typing import BinaryIO, Iterator, List, Tuple

    from installer._compat.typing import FSPath, Text

    WheelContentElement = Tuple[Tuple[FSPath, str, str], BinaryIO]


__all__ = ["WheelSource", "WheelFile"]


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
        return u"{}-{}.dist-info".format(self.distribution, self.version)

    @property
    def data_dir(self):
        """Name of the data directory."""
        return u"{}-{}.data".format(self.distribution, self.version)

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
          :py:meth:`RecordEntry.from_elements <installer.records.RecordEntry.from_elements>`.
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


class WheelFile(WheelSource):
    """Implements `WheelSource`, for an existing file from the filesystem.

    Example usage::

        >>> with WheelFile.open("sampleproject-2.0.0-py3-none-any.whl") as source:
        ...     installer.install(source, destination)
    """

    def __init__(self, f):
        # type: (zipfile.ZipFile) -> None
        """Initialize a WheelFile object.

        :param f: An open zipfile, which will stay open as long as this object is used.
        """
        self._zipfile = f
        assert f.filename

        basename = os.path.basename(f.filename)
        parsed_name = installer.utils.parse_wheel_filename(basename)
        super(WheelFile, self).__init__(
            version=parsed_name.version,
            distribution=parsed_name.distribution,
        )

    @classmethod
    @contextmanager
    def open(cls, path):
        # type: (FSPath) -> Iterator[WheelFile]
        """Create a wheelfile from a given path."""
        with zipfile.ZipFile(path) as f:
            yield cls(f)

    @property
    def dist_info_filenames(self):
        # type: () -> List[FSPath]
        """Get names of all files in the dist-info directory."""
        base = self.dist_info_dir
        return [
            name[len(base) + 1 :]
            for name in self._zipfile.namelist()
            if name[-1:] != "/"
            if base == posixpath.commonprefix([name, base])
        ]

    def read_dist_info(self, filename):
        # type: (FSPath) -> Text
        """Get contents, from ``filename`` in the dist-info directory."""
        path = posixpath.join(self.dist_info_dir, filename)
        return self._zipfile.read(path).decode("utf-8")

    def get_contents(self):
        # type: () -> Iterator[WheelContentElement]
        """Sequential access to all contents of the wheel (including dist-info files).

        This implementation requires that every file that is a part of the wheel
        archive has a corresponding entry in RECORD. If they are not, an
        :any:`AssertionError` will be raised.
        """
        # Convert the record file into a useful mapping
        record_lines = self.read_dist_info("RECORD").splitlines()
        records = installer.records.parse_record_file(record_lines)
        record_mapping = {record[0]: record for record in records}

        for item in self._zipfile.infolist():
            if item.filename[-1:] == "/":  # looks like a directory
                continue

            record = record_mapping.pop(item.filename, None)
            assert record is not None, "In {}, {} is not mentioned in RECORD".format(
                self._zipfile.filename,
                item.filename,
            )  # should not happen for valid wheels

            with self._zipfile.open(item) as stream:
                stream_casted = cast("BinaryIO", stream)
                yield record, stream_casted
