import csv
import warnings

from installer._compat.typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator, Optional
    from installer._compat.typing import FSPath


__all__ = [
    "Hash",
    "RecordItem",
    "SuperfluousRecordColumnsWarning",
    "parse_record_file",
]


class SuperfluousRecordColumnsWarning(UserWarning):
    pass


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


class RecordItem(object):
    def __init__(self, path, hash_, size):
        # type: (FSPath, Optional[Hash], Optional[int]) -> None
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
            path=path,
            hash_=Hash.parse(hash_) if hash_ else None,
            size=int(size) if size else None,
        )


def parse_record_file(f):
    # type: (Iterator[str]) -> Iterator[RecordItem]
    for row_index, row in enumerate(csv.reader(f)):
        if len(row) > 3:
            warnings.warn(
                "Dropping columns [3:] from row {}".format(row_index),
                SuperfluousRecordColumnsWarning,
            )
        try:
            record = RecordItem.parse(row[0], row[1], row[2])
        except (IndexError, ValueError):
            raise ValueError("invalid row {}: {!r}".format(row_index, row))
        yield record
