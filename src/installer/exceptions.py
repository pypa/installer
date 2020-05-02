__all__ = [
    "InvalidWheel",
    "MetadataNotFound",
    "RecordItemError",
    "RecordItemHashMismatch",
    "RecordItemSizeMismatch",
]


class InvalidWheel(Exception):
    pass


class MetadataNotFound(InvalidWheel):
    pass


class RecordItemError(InvalidWheel):
    pass


class RecordItemHashMismatch(RecordItemError):
    pass


class RecordItemSizeMismatch(RecordItemError):
    pass
