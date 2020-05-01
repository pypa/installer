import collections
import csv
import warnings

from installer._compat import pathlib
from installer._compat.typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterator, Optional


class SuperfulousRecordColumnsWarning(UserWarning):
    pass


Hash = collections.namedtuple("Hash", "name value")


class Record(object):
    def __init__(self, path, hash_, size):
        # type: (pathlib.PurePosixPath, Optional[Hash], Optional[int]) -> None
        self.path = path
        self.hash_ = hash_
        self.size = size

    def __repr__(self):
        # type: () -> str
        return "Record(path={!r}, hash_={!r}, size={!r})".format(
            self.path, self.hash_, self.size,
        )

    @classmethod
    def parse(cls, p, h, s):
        # type: (str, str, str) -> Record
        if h:
            name, value = h.split("=", 1)
            hash_ = Hash(name, value)  # type: Optional[Hash]
        else:
            hash_ = None
        return cls(
            path=pathlib.PurePosixPath(p),
            hash_=hash_,
            size=int(s) if s else None,
        )


def parse_record_file(f):
    # type: (Iterator[str]) -> Iterator[Record]
    for i, row in enumerate(csv.reader(f)):
        if len(row) > 3:
            warnings.warn(
                "Dropping columns [3:] from row {}".format(i),
                SuperfulousRecordColumnsWarning,
            )
        try:
            record = Record.parse(row[0], row[1], row[2])
        except (IndexError, ValueError):
            raise ValueError("invalid row {}: {!r}".format(i, row))
        yield record
