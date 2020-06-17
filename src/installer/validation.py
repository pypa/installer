"""Validation checks for wheel files.
"""


class InvalidWheelSource(Exception):
    """Raised when a ``WheelSource`` is not valid.
    """

    def __init__(self, source, reason):
        super(InvalidWheelSource, self).__init__(source, reason)
        self.source = source
        self.reason = reason

    @classmethod
    def from_multiple(cls, source, exceptions):
        # type: (WheelSource, Iterable[InvalidWheelSource])
        reason = ", ".join(e.reason for e in exceptions)
        return cls(source=source, reason=reason)


#
# Basic Validators
#
def validate_contents_match_RECORD_file(source):
    # TODO: implement this, after #9 is merged.
    pass
