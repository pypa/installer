import csv
import warnings

from installer._compat.typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Iterable, Iterator, Optional


__all__ = [
    "Hash",
    "Path",
    "RecordItem",
    "SuperfulousRecordColumnsWarning",
    "parse_record_file",
]


class SuperfulousRecordColumnsWarning(UserWarning):
    pass


class Path(object):
    """A light-weight path interface.

    This is used like ``pathlib.PurePosixPath``, but slim.
    """

    __slots__ = ("_parts",)

    def __init__(self, *parts):
        # type: (*str) -> None
        self._parts = tuple(self._iter_parts(parts))

    @staticmethod
    def _iter_parts(parts):
        # type: (Iterable[str]) -> Iterator[str]
        for part in parts:
            for p in part.split("/"):
                if p:
                    yield p

    def __repr__(self):
        # type: () -> str
        return "Path({})".format(", ".join(repr(p) for p in self._parts))

    def __str__(self):
        # type: () -> str
        return self.as_posix()

    def __fspath__(self):  # pragma: no cover
        # type: () -> str
        return self.as_posix()

    def as_posix(self):
        # type: () -> str
        return "/".join(self._parts)


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
        # type: (Path, Optional[Hash], Optional[int]) -> None
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
            path=Path(path),
            hash_=Hash.parse(hash_) if hash_ else None,
            size=int(size) if size else None,
        )


def parse_record_file(f):
    # type: (Iterator[str]) -> Iterator[RecordItem]
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
