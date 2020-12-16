"""Parsing and handling :pep:`376` RECORD files."""

import base64
import csv
import hashlib

from installer._compat.typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator, Optional

    from installer._compat.typing import FSPath


__all__ = [
    "Hash",
    "Record",
    "InvalidRecord",
    "parse_record_file",
]


class InvalidRecord(Exception):
    """Raised when a Record is not valid, due to improper element values or count."""

    def __init__(self, elements, issues):  # noqa: D107
        super(InvalidRecord, self).__init__(", ".join(issues))
        self.issues = issues
        self.elements = elements

    def __repr__(self):
        return "InvalidRecord(elements={!r}, issues={!r})".format(
            self.elements, self.issues
        )


class Hash(object):
    """Represents the "hash" element of a Record."""

    def __init__(self, name, value):
        # type: (str, str) -> None
        """Construct a ``Hash`` object.

        Most consumers should use :py:meth:`Hash.parse` instead, since no
        validation or parsing is performed by this constructor.

        :param name: name of the hash function
        :param value: hashed value
        """
        self.name = name
        self.value = value

    def __str__(self):
        # type: () -> str
        return "{}={}".format(self.name, self.value)

    def __repr__(self):
        # type: () -> str
        return "Hash(name={!r}, value={!r})".format(self.name, self.value)

    def validate(self, data):
        # type: (bytes) -> bool
        """Validate that ``data`` matches this instance.

        :param data: Contents of the file.
        :return: Whether ``data`` matches the hashed value.
        """
        digest = hashlib.new(self.name, data).digest()
        value = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        return self.value == value

    @classmethod
    def parse(cls, h):
        # type: (str) -> Hash
        """Build a Hash object, from a "name=value" string.

        This accepts a string of the format for the second element in a record,
        as described in :pep:`376`.

        Typical usage::

            Hash.parse("sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4")

        :param h: a name=value string
        """
        name, value = h.split("=", 1)
        return cls(name, value)


class Record(object):
    """Represents a single record in a RECORD file.

    A list of :py:class:`Record` objects fully represents a RECORD file.
    """

    def __init__(self, path, hash_, size):
        # type: (FSPath, Optional[Hash], Optional[int]) -> None
        r"""Construct a ``Record`` object.

        Most consumers should use :py:meth:`Record.from_elements`, since no
        validation or parsing is performed by this constructor.

        :param path: file's path
        :param hash\_: hash of the file's contents
        :param size: file's size in bytes
        """
        super(Record, self).__init__()

        self.path = path
        self.hash_ = hash_
        self.size = size

    def __str__(self):
        # type: () -> str
        return ",".join(
            [
                (str(elem) if elem is not None else "")
                for elem in [self.path, self.hash_, self.size]
            ]
        )

    def __repr__(self):
        # type: () -> str
        return "Record(path={!r}, hash_={!r}, size={!r})".format(
            self.path, self.hash_, self.size,
        )

    def validate(self, data):
        # type: (bytes) -> bool
        """Validate that ``data`` matches this instance.

        :param data: Contents of the file corresponding to this instance.
        :return: whether ``data`` matches hash and size.
        """
        if self.size is not None and len(data) != self.size:
            return False

        if self.hash_:
            return self.hash_.validate(data)

        return True

    @classmethod
    def from_elements(cls, path, hash_, size):
        # type: (FSPath, str, str) -> Record
        r"""Build a Record object, from values of the elements.

        Typical usage::

            reader = csv.reader(f)
            for row in reader:
                record = Record.from_elements(row[0], row[1], row[2])

        Meaning of each element is specified in :pep:`376`.

        :param path: first element (file's path)
        :param hash\_: second element (hash of the file's contents)
        :param size: third element (file's size in bytes)
        :raises InvalidRecord: if any element is invalid
        """
        # Validate the passed values.
        issues = []

        if not path:
            issues.append("`path` cannot be empty")

        if hash_:
            try:
                hash_value = Hash.parse(hash_)  # type: Optional[Hash]
            except ValueError:
                issues.append("`hash` does not follow the required format")
        else:
            hash_value = None

        if size:
            try:
                size_value = int(size)  # type: Optional[int]
            except ValueError:
                issues.append("`size` cannot be non-integer")
        else:
            size_value = None

        if issues:
            raise InvalidRecord(elements=(path, hash_, size), issues=issues)

        return cls(path=path, hash_=hash_value, size=size_value,)


def parse_record_file(rows):
    # type: (Iterator[str]) -> Iterator[Record]
    """Parse a :pep:`376` RECORD.

    :param rows: iterator providing lines of a RECORD.
    """
    reader = csv.reader(rows, delimiter=",", quotechar='"', lineterminator="\n")
    for row_index, elements in enumerate(reader):
        if len(elements) != 3:
            message = "Row Index {}: expected 3 elements, got {}".format(
                row_index, len(elements)
            )
            raise InvalidRecord(elements=elements, issues=[message])

        record = Record.from_elements(elements[0], elements[1], elements[2])
        yield record
