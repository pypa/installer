import csv
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

    @classmethod
    def parse(cls, path, hash_, size):
        # type: (str, str, str) -> Record
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

        record = Record.parse(elements[0], elements[1], elements[2])
        yield record
