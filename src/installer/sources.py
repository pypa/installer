"""Source of information about a wheel file."""

import posixpath
import stat
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from functools import cached_property
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    BinaryIO,
    ClassVar,
    Optional,
    cast,
)

from installer.exceptions import InstallerError
from installer.records import InvalidRecordEntry, RecordEntry, parse_record_file
from installer.utils import canonicalize_name, parse_wheel_filename

if TYPE_CHECKING:
    import os

WheelContentElement = tuple[tuple[str, str, str], BinaryIO, bool]


__all__ = ["WheelSource", "WheelFile"]


class WheelSource:
    """Represents an installable wheel.

    This is an abstract class, whose methods have to be implemented by subclasses.
    """

    validation_error: ClassVar[type[Exception]] = ValueError  #: :meta hide-value:
    """
    .. versionadded:: 0.7.0

    Exception to be raised by :py:meth:`validate_record` when validation fails.
    This is expected to be a subclass of :py:class:`ValueError`.
    """

    def __init__(self, distribution: str, version: str) -> None:
        """Initialize a WheelSource object.

        :param distribution: distribution name (like ``urllib3``)
        :param version: version associated with the wheel
        """
        super().__init__()
        self.distribution = distribution
        self.version = version

    @property
    def dist_info_dir(self) -> str:
        """Name of the dist-info directory."""
        return f"{self.distribution}-{self.version}.dist-info"

    @property
    def data_dir(self) -> str:
        """Name of the data directory."""
        return f"{self.distribution}-{self.version}.data"

    @property
    def dist_info_filenames(self) -> list[str]:
        """Get names of all files in the dist-info directory.

        Sample usage/behaviour::

            >>> wheel_source.dist_info_filenames
            ['METADATA', 'WHEEL']
        """
        raise NotImplementedError

    def read_dist_info(self, filename: str) -> str:
        """Get contents, from ``filename`` in the dist-info directory.

        Sample usage/behaviour::

            >>> wheel_source.read_dist_info("METADATA")
            ...

        :param filename: name of the file
        """
        raise NotImplementedError

    def validate_record(self) -> None:
        """Validate ``RECORD`` of the wheel.

        .. versionadded:: 0.7.0

        This method should be called before :py:func:`install <installer.install>`
        if validation is required.
        """
        raise NotImplementedError

    def get_contents(self) -> Iterator[WheelContentElement]:
        """Sequential access to all contents of the wheel (including dist-info files).

        This method should return an iterable. Each value from the iterable must be a
        tuple containing 3 elements:

        - record: 3-value tuple, to pass to
          :py:meth:`RecordEntry.from_elements <installer.records.RecordEntry.from_elements>`.
        - stream: An :py:class:`io.BufferedReader` object, providing the contents of the
          file at the location provided by the first element (path).
        - is_executable: A boolean, representing whether the item has an executable bit.

        All paths must be relative to the root of the wheel.

        Sample usage/behaviour::

            >>> iterable = wheel_source.get_contents()
            >>> next(iterable)
            (('pkg/__init__.py', '', '0'), <...>, False)

        This method may be called multiple times. Each iterable returned must
        provide the same content upon reading from a specific file's stream.
        """
        raise NotImplementedError


class _WheelFileValidationError(ValueError, InstallerError):
    """Raised when a wheel file fails validation."""

    def __init__(self, issues: list[str]) -> None:
        super().__init__(repr(issues))
        self.issues = issues

    def __repr__(self) -> str:
        return f"WheelFileValidationError(issues={self.issues!r})"


class _WheelFileBadDistInfo(ValueError, InstallerError):
    """Raised when a wheel file has issues around `.dist-info`."""

    def __init__(self, *, reason: str, filename: Optional[str], dist_info: str) -> None:
        super().__init__(reason)
        self.reason = reason
        self.filename = filename
        self.dist_info = dist_info

    def __str__(self) -> str:
        return (
            f"{self.reason} (filename={self.filename!r}, dist_info={self.dist_info!r})"
        )


class WheelFile(WheelSource):
    """Implements `WheelSource`, for an existing file from the filesystem.

    Example usage::

        >>> with WheelFile.open("sampleproject-2.0.0-py3-none-any.whl") as source:
        ...     installer.install(source, destination)
    """

    validation_error = _WheelFileValidationError

    def __init__(self, f: zipfile.ZipFile) -> None:
        """Initialize a WheelFile object.

        :param f: An open zipfile, which will stay open as long as this object is used.
        """
        self._zipfile = f
        assert f.filename

        basename = Path(f.filename).name
        parsed_name = parse_wheel_filename(basename)
        super().__init__(
            version=parsed_name.version,
            distribution=parsed_name.distribution,
        )

    @classmethod
    @contextmanager
    def open(cls, path: "os.PathLike[str]") -> Iterator["WheelFile"]:
        """Create a wheelfile from a given path."""
        with zipfile.ZipFile(path) as f:
            yield cls(f)

    @cached_property
    def dist_info_dir(self) -> str:
        """Name of the dist-info directory."""
        top_level_directories = {
            path.split("/", 1)[0] for path in self._zipfile.namelist()
        }
        dist_infos = [
            name for name in top_level_directories if name.endswith(".dist-info")
        ]

        try:
            (dist_info_dir,) = dist_infos
        except ValueError:
            raise _WheelFileBadDistInfo(
                reason="Wheel doesn't contain exactly one .dist-info directory",
                filename=self._zipfile.filename,
                dist_info=str(sorted(dist_infos)),
            ) from None

        # NAME-VER.dist-info
        di_dname = dist_info_dir.rsplit("-", 2)[0]
        norm_di_dname = canonicalize_name(di_dname)
        norm_file_dname = canonicalize_name(self.distribution)

        if norm_di_dname != norm_file_dname:
            raise _WheelFileBadDistInfo(
                reason="Wheel .dist-info directory doesn't match wheel filename",
                filename=self._zipfile.filename,
                dist_info=dist_info_dir,
            )

        return dist_info_dir

    @property
    def dist_info_filenames(self) -> list[str]:
        """Get names of all files in the dist-info directory."""
        base = self.dist_info_dir
        return [
            name[len(base) + 1 :]
            for name in self._zipfile.namelist()
            if name[-1:] != "/"
            if base == posixpath.commonprefix([name, base])
        ]

    def read_dist_info(self, filename: str) -> str:
        """Get contents, from ``filename`` in the dist-info directory."""
        path = posixpath.join(self.dist_info_dir, filename)
        return self._zipfile.read(path).decode("utf-8")

    def validate_record(self, *, validate_contents: bool = True) -> None:
        """Validate ``RECORD`` of the wheel.

        This method should be called before :py:func:`install <installer.install>`
        if validation is required.

        File names will always be validated against ``RECORD``.

        If ``validate_contents`` is true, sizes and hashes of files
        will also be validated against ``RECORD``.

        :param validate_contents: Whether to validate content integrity.
        """
        try:
            record_lines = self.read_dist_info("RECORD").splitlines()
            record_mapping = {
                record[0]: record for record in parse_record_file(record_lines)
            }
        except Exception as exc:
            raise _WheelFileValidationError(
                [f"Unable to retrieve `RECORD` from {self._zipfile.filename}: {exc!r}"]
            ) from exc

        issues: list[str] = []

        for item in self._zipfile.infolist():
            if item.filename[-1:] == "/":  # looks like a directory
                continue

            record_args = record_mapping.pop(item.filename, None)

            if self.dist_info_dir == posixpath.commonprefix(
                [self.dist_info_dir, item.filename]
            ) and item.filename.split("/")[-1] in ("RECORD.p7s", "RECORD.jws"):
                # both are for digital signatures, and not mentioned in RECORD
                if record_args is not None:
                    # Incorrectly contained
                    issues.append(
                        f"In {self._zipfile.filename}, digital signature file {item.filename} is incorrectly contained in RECORD."
                    )
                continue

            if record_args is None:
                issues.append(
                    f"In {self._zipfile.filename}, {item.filename} is not mentioned in RECORD"
                )
                continue

            try:
                record = RecordEntry.from_elements(*record_args)
            except InvalidRecordEntry as e:
                for issue in e.issues:
                    issues.append(
                        f"In {self._zipfile.filename}, entry in RECORD file for "
                        f"{item.filename} is invalid: {issue}"
                    )

                # coverage on Windows and python < 3.10 claims that the next line is not
                # reached, pragma to deal with this false positive.
                continue  # pragma: no cover

            if item.filename == f"{self.dist_info_dir}/RECORD":
                # Assert that RECORD doesn't have size and hash.
                if record.hash_ is not None or record.size is not None:
                    # Incorrectly contained hash / size
                    issues.append(
                        f"In {self._zipfile.filename}, RECORD file incorrectly contains hash / size."
                    )
                continue
            if record.hash_ is None or record.size is None:
                # Report empty hash / size
                issues.append(
                    f"In {self._zipfile.filename}, hash / size of {item.filename} is not included in RECORD"
                )
            if validate_contents:
                with self._zipfile.open(item, "r") as stream:
                    if not record.validate_stream(cast(BinaryIO, stream)):
                        issues.append(
                            f"In {self._zipfile.filename}, hash / size of {item.filename} didn't match RECORD"
                        )

        if issues:
            raise _WheelFileValidationError(issues)

    def get_contents(self) -> Iterator[WheelContentElement]:
        """Sequential access to all contents of the wheel (including dist-info files).

        This implementation requires that every file that is a part of the wheel
        archive has a corresponding entry in RECORD. If they are not, an
        :any:`AssertionError` will be raised.
        """
        # Convert the record file into a useful mapping
        record_lines = self.read_dist_info("RECORD").splitlines()
        records = parse_record_file(record_lines)
        record_mapping = {record[0]: record for record in records}

        for item in self._zipfile.infolist():
            if item.filename[-1:] == "/":  # looks like a directory
                continue

            # Pop record with empty default, because validation is handled by `validate_record`
            record = record_mapping.pop(item.filename, (item.filename, "", ""))

            # Borrowed from:
            # https://github.com/pypa/pip/blob/0f21fb92/src/pip/_internal/utils/unpacking.py#L96-L100
            mode = item.external_attr >> 16
            is_executable = bool(mode and stat.S_ISREG(mode) and mode & 0o111)

            with self._zipfile.open(item) as stream:
                stream_casted = cast("BinaryIO", stream)
                yield record, stream_casted, is_executable
