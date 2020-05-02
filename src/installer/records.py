__all__ = [
    "Hash",
    "RecordItem",
    "SuperfulousRecordColumnsWarning",
    "parse_record_file",
]

import base64
import csv
import hashlib
import warnings

import six

from installer._compat import pathlib
from installer._compat.typing import TYPE_CHECKING
from installer.exceptions import RecordItemHashMismatch, RecordItemSizeMismatch

if TYPE_CHECKING:
    from typing import IO, Iterable, Iterator, Optional, Tuple


class SuperfulousRecordColumnsWarning(UserWarning):
    pass


class Hash(object):
    __slots__ = ("name", "value")

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

    def raise_for_validation(self, data):
        # type: (six.binary_type) -> None
        digest = hashlib.new(self.name, data).digest()
        value = base64.urlsafe_b64encode(digest).decode("ascii").rstrip("=")
        if value != self.value:
            raise RecordItemHashMismatch(self, value)


class RecordItem(object):
    def __init__(self, path, hash_, size):
        # type: (pathlib.PurePosixPath, Optional[Hash], Optional[int]) -> None
        self.path = path
        self.hash_ = hash_
        self.size = size

    def __repr__(self):
        # type: () -> str
        return "RecordItem(path={!r}, hash_={!r}, size={!r})".format(
            self.path, self.hash_, self.size,
        )

    @classmethod
    def parse(cls, path, hash_, size):
        # type: (str, str, str) -> RecordItem
        """Build a Record from parsing elements in a record row.

        Typical usage::

            reader = csv.reader(f)
            for row in reader:
                record = Record.parse(row[0], row[1], row[2])

        All arguments are in string form. Meaning of elements are specified in
        PEP 376. Raises ``ValueError`` if any of the elements is invalid.
        """
        return cls(
            path=pathlib.PurePosixPath(path),
            hash_=Hash.parse(hash_) if hash_ else None,
            size=int(size) if size else None,
        )

    def raise_for_validation(self, data):
        # type: (six.binary_type) -> None
        if self.hash_ is not None:
            self.hash_.raise_for_validation(data)
        if self.size is not None and self.size != len(data):
            raise RecordItemSizeMismatch(self, data)

    def as_row(self):
        # type: () -> Tuple[str, str, str]
        h = self.hash_
        return (
            str(self.path),
            "{}={}".format(h.name, h.value) if h is not None else "",
            str(self.size) if self.size is not None else "",
        )


def parse_record_file(f):
    # type: (Iterable[str]) -> Iterator[RecordItem]
    for row_index, row in enumerate(csv.reader(f)):
        if len(row) > 3:
            warnings.warn(
                "Dropping columns [3:] from row {}".format(row_index),
                SuperfulousRecordColumnsWarning,
            )
        try:
            record = RecordItem.parse(row[0], row[1], row[2])
        except (IndexError, ValueError):
            raise ValueError("invalid row {}: {!r}".format(row_index, row))
        yield record


def write_record_file(f, items):
    # type: (IO[str], Iterable[RecordItem]) -> None
    writer = csv.writer(f)
    writer.writerows(sorted(item.as_row() for item in items))
