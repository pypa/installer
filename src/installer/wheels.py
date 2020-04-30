from __future__ import annotations

import csv
import pathlib
import warnings

from typing import Iterator, NamedTuple, Optional


class SuperfulousRecordColumnsWarning(UserWarning):
    pass


class Hash(NamedTuple):
    name: str
    value: str


class Record(NamedTuple):
    path: pathlib.PurePosixPath
    hash_: Optional[Hash]
    size: Optional[int]


def _parse_record(row: list[str]) -> Record:
    if row[1]:
        name, value = row[1].split("=", 1)
        hash_ = Hash(name, value)
    else:
        hash_ = None
    return Record(
        path=pathlib.PurePosixPath(row[0]),
        hash_=hash_,
        size=int(row[2]) if row[2] else None,
    )


def parse_record_file(f: Iterator[str]) -> Iterator[Record]:
    for i, row in enumerate(csv.reader(f)):
        if len(row) > 3:
            warnings.warn(
                f"Dropping columns [3:] from row {i}",
                SuperfulousRecordColumnsWarning,
            )
        try:
            record = _parse_record(row)
        except (IndexError, ValueError):
            raise ValueError(f"invalid row {i}: {row!r}")
        yield record
