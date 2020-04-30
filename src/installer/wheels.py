from __future__ import annotations

import csv
import dataclasses
import pathlib
import warnings

from typing import Iterator, Optional


class SuperfulousRecordColumnsWarning(UserWarning):
    pass


@dataclasses.dataclass()
class Hash:
    name: str
    value: str

    @classmethod
    def parse(cls, s: str) -> Optional[Hash]:
        name, value = s.split("=", 1)
        return cls(name, value)


@dataclasses.dataclass()
class Record:
    path: pathlib.PurePosixPath
    hash_: Optional[Hash]
    size: Optional[int]

    @classmethod
    def from_row(cls, row: list[str]) -> Record:
        return cls(
            path=pathlib.PurePosixPath(row[0]),
            hash_=Hash.parse(row[1]) if row[1] else None,
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
            record = Record.from_row(row)
        except (IndexError, ValueError):
            raise ValueError(f"invalid row {i}: {row!r}")
        yield record
