"""Provides an object-oriented model for handling :pep:`376` RECORD files."""

import base64
import csv
import hashlib
import os
from typing import BinaryIO, Iterable, Iterator, Optional, Tuple, cast

from installer.utils import copyfileobj_with_hashing, get_stream_length

__all__ = [
    "Hash",
    "RecordEntry",
    "InvalidRecordEntry",
    "parse_record_file",
]


class InvalidRecordEntry(Exception):
    """Raised when a RecordEntry is not valid, due to improper element values or count."""

    def __init__(  # noqa: D107
        self, elements: Iterable[str], issues: Iterable[str]
    ) -> None:
        super().__init__(", ".join(issues))
        self.issues = issues
        self.elements = elements

    def __repr__(self) -> str:
        return f"InvalidRecordEntry(elements={self.elements!r}, issues={self.issues!r})"


class Hash:
    """Represents the "hash" element of a RecordEntry."""

    def __init__(self, name: str, value: str) -> None:
        """Construct a ``Hash`` object.

        Most consumers should use :py:meth:`Hash.parse` instead, since no
        validation or parsing is performed by this constructor.

        :param name: name of the hash function
        :param value: hashed value
        """
        self.name = name
        self.value = value

    def __str__(self) -> str:
        return f"{self.name}={self.value}"

    def __repr__(self) -> str:
        return f"Hash(name={self.name!r}, value={self.value!r})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Hash):
            return NotImplemented
        return self.value == other.value and self.name == other.name

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


class RecordEntry:
    """Represents a single record in a RECORD file.

    A list of :py:class:`RecordEntry` objects fully represents a RECORD file.
    """

    def __init__(self, path: str, hash_: Optional[Hash], size: Optional[int]) -> None:
        r"""Construct a ``RecordEntry`` object.

        Most consumers should use :py:meth:`RecordEntry.from_elements`, since no
        validation or parsing is performed by this constructor.

        :param path: file's path
        :param hash\_: hash of the file's contents
        :param size: file's size in bytes
        """
        super().__init__()

        self.path = path
        self.hash_ = hash_
        self.size = size

    def to_row(self, path_prefix: Optional[str] = None) -> Tuple[str, str, str]:
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
            with open(os.devnull, "wb") as new_target:
                hash_, size = copyfileobj_with_hashing(
                    stream, cast("BinaryIO", new_target), self.hash_.name
                )

            if self.size is not None and size != self.size:
                return False
            if self.hash_.value != hash_:
                return False
            return True

        elif self.size is not None:
            assert self.hash_ is None
            size = get_stream_length(stream)
            if size != self.size:
                return False
            return True

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

        if hash_:
            try:
                hash_value: Optional[Hash] = Hash.parse(hash_)
            except ValueError:
                issues.append("`hash` does not follow the required format")
        else:
            hash_value = None

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


def parse_record_file(rows: Iterable[str]) -> Iterator[Tuple[str, str, str]]:
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

        value = cast(Tuple[str, str, str], tuple(elements))
        yield value
