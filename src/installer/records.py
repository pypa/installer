"""Provides an object-oriented model for handling :pep:`376` RECORD files."""

import base64
import csv
import hashlib
import os
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO, Optional, cast

from installer.utils import copyfileobj_with_hashing, get_stream_length

__all__ = [
    "Hash",
    "InvalidRecordEntry",
    "RecordEntry",
    "parse_record_file",
]


@dataclass
class InvalidRecordEntry(Exception):
    """Raised when a RecordEntry is not valid, due to improper element values or count."""

    elements: Iterable[str]
    issues: Iterable[str]

    def __post_init__(self) -> None:
        super().__init__(", ".join(self.issues))


@dataclass
class Hash:
    """Represents the "hash" element of a RecordEntry.

    Most consumers should use :py:meth:`Hash.parse` instead, since no
    validation or parsing is performed by this constructor.
    """

    name: str
    """Name of the hash function."""

    value: str
    """Hashed value."""

    def __str__(self) -> str:
        return f"{self.name}={self.value}"

    def validate(self, data: bytes) -> bool:
        """Validate that ``data`` matches this instance.

        :param data: Contents of the file.
        :return: Whether ``data`` matches the hashed value.
        """
        digest = hashlib.new(self.name, data).digest()
        value = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return self.value == value

    @classmethod
    def parse(cls, h: str) -> "Hash":
        """Build a Hash object, from a "name=value" string.

        This accepts a string of the format for the second element in a record,
        as described in :pep:`376`.

        Typical usage::

            Hash.parse("sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4")

        :param h: a name=value string
        """
        name, value = h.split("=", 1)
        return cls(name, value)


@dataclass
class RecordEntry:
    """Represents a single record in a RECORD file.

    A list of :py:class:`RecordEntry` objects fully represents a RECORD file.

    Most consumers should use :py:meth:`RecordEntry.from_elements`, since no
    validation or parsing is performed by this constructor.
    """

    path: str
    """File's path."""

    hash_: Optional[Hash]
    """Hash of the file's contents."""

    size: Optional[int]
    """File's size in bytes."""

    def to_row(self, path_prefix: Optional[str] = None) -> tuple[str, str, str]:
        """Convert this into a 3-element tuple that can be written in a RECORD file.

        :param path_prefix: A prefix to attach to the path -- must end in `/`
        :return: a (path, hash, size) row
        """
        if path_prefix is not None:
            assert path_prefix.endswith("/")
            path = path_prefix + self.path
        else:
            path = self.path

        # Convert Windows paths to use / for consistency
        if os.sep == "\\":
            path = path.replace("\\", "/")  # pragma: no cover

        return (
            path,
            str(self.hash_ or ""),
            str(self.size) if self.size is not None else "",
        )

    def __repr__(self) -> str:
        return (
            f"RecordEntry(path={self.path!r}, hash_={self.hash_!r}, size={self.size!r})"
        )

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, RecordEntry):
            return NotImplemented
        return (
            self.path == other.path
            and self.hash_ == other.hash_
            and self.size == other.size
        )

    def validate(self, data: bytes) -> bool:
        """Validate that ``data`` matches this instance.

        .. attention::
            .. deprecated:: 0.8.0
                Use :py:meth:`validate_stream` instead, with ``BytesIO(data)``.

        :param data: Contents of the file corresponding to this instance.
        :return: whether ``data`` matches hash and size.
        """
        if self.size is not None and len(data) != self.size:
            return False

        if self.hash_:
            return self.hash_.validate(data)

        return True

    def validate_stream(self, stream: BinaryIO) -> bool:
        """Validate that data read from stream matches this instance.

        :param stream: Representing the contents of the file.
        :return: Whether data read from stream matches hash and size.
        """
        if self.hash_ is not None:
            with Path(os.devnull).open("wb") as new_target:
                hash_, size = copyfileobj_with_hashing(
                    stream, cast("BinaryIO", new_target), self.hash_.name
                )

            if self.size is not None and size != self.size:
                return False
            return self.hash_.value == hash_

        elif self.size is not None:
            assert self.hash_ is None
            size = get_stream_length(stream)
            return size == self.size

        return True

    @classmethod
    def from_elements(cls, path: str, hash_: str, size: str) -> "RecordEntry":
        r"""Build a RecordEntry object, from values of the elements.

        Typical usage::

            for row in parse_record_file(f):
                record = RecordEntry.from_elements(row[0], row[1], row[2])

        Meaning of each element is specified in :pep:`376`.

        :param path: first element (file's path)
        :param hash\_: second element (hash of the file's contents)
        :param size: third element (file's size in bytes)
        :raises InvalidRecordEntry: if any element is invalid
        """
        # Validate the passed values.
        issues = []

        if not path:
            issues.append("`path` cannot be empty")

        hash_value: Optional[Hash] = None
        if hash_:
            try:
                hash_value = Hash.parse(hash_)
                if hash_value.name not in hashlib.algorithms_available:
                    issues.append(f"invalid hash algorithm '{hash_value.name}'")
                    hash_value = None
            except ValueError:
                issues.append("`hash` does not follow the required format")

        if size:
            try:
                size_value: Optional[int] = int(size)
            except ValueError:
                issues.append("`size` cannot be non-integer")
        else:
            size_value = None

        if issues:
            raise InvalidRecordEntry(elements=(path, hash_, size), issues=issues)

        return cls(path=path, hash_=hash_value, size=size_value)


def parse_record_file(rows: Iterable[str]) -> Iterator[tuple[str, str, str]]:
    """Parse a :pep:`376` RECORD.

    Returns an iterable of 3-value tuples, that can be passed to
    :any:`RecordEntry.from_elements`.

    :param rows: iterator providing lines of a RECORD (no trailing newlines).
    """
    reader = csv.reader(rows, delimiter=",", quotechar='"', lineterminator="\n")
    for row_index, elements in enumerate(reader):
        if len(elements) != 3:
            message = f"Row Index {row_index}: expected 3 elements, got {len(elements)}"
            raise InvalidRecordEntry(elements=elements, issues=[message])

        # Convert Windows paths to use / for consistency
        elements[0] = elements[0].replace("\\", "/")

        value = cast("tuple[str, str, str]", tuple(elements))
        yield value
