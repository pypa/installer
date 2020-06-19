"""Utilities for parsing and handling PEP 376 RECORD files.
"""

import base64
import csv
import hashlib
import os

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
    """Raised when a Record is not valid, due to improper element values or count.
    """

    def __init__(self, elements, issues):
        super(InvalidRecord, self).__init__(", ".join(issues))
        self.issues = issues
        self.elements = elements

    def __repr__(self):
        return "InvalidRecord(elements={!r}, issues={!r})".format(
            self.elements, self.issues
        )


class Hash(object):
    def __init__(self, name, value):
        # type: (str, str) -> None
        self.name = name
        self.value = value

    def __repr__(self):
        return "Hash(name={!r}, value={!r})".format(self.name, self.value)

    @classmethod
    def parse(cls, h):
        # type: (str) -> Hash
        name, value = h.split("=", 1)
        return Hash(name, value)


class Record(object):
    def __init__(self, path, hash_, size):
        # type: (FSPath, Optional[Hash], Optional[int]) -> None
        super(Record, self).__init__()

        self.path = path
        self.hash_ = hash_
        self.size = size

    def __repr__(self):
        # type: () -> str
        return "Record(path={!r}, hash_={!r}, size={!r})".format(
            self.path, self.hash_, self.size,
        )

    def validate(self, data):
        # type: (bytes) -> bool
        if self.size is not None and len(data) != self.size:
            return False

        if self.hash_:
            digest = hashlib.new(self.hash_.name, data).digest()
            value = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
            return self.hash_.value == value

        return True

    @classmethod
    def from_elements(cls, path, hash_, size):
        # type: (FSPath, str, str) -> Record
        """Build a Record object, from values of the elements.

        All arguments must be in string form, except `path` which can also be a
        ``pathlib.Path`` instance on Python 3.

        Typical usage::

            reader = csv.reader(f)
            for row in reader:
                record = Record.from_elements(row[0], row[1], row[2])

        All arguments are in string form. Meaning of each element is specified in
        PEP 376. Raises ``InvalidRecord`` if any element is invalid.
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
    """Parse a RECORD file, provided as an iterator of record lines.
    """
    reader = csv.reader(rows, delimiter=",", quotechar='"', lineterminator=os.linesep)
    for row_index, elements in enumerate(reader):
        if len(elements) != 3:
            message = "Row Index {}: expected 3 elements, got {}".format(
                row_index, len(elements)
            )
            raise InvalidRecord(elements=elements, issues=[message])

        record = Record.from_elements(elements[0], elements[1], elements[2])
        yield record
