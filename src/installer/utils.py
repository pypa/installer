"""Utilities related to handling / interacting with wheel files."""

import re
from collections import namedtuple
from email.parser import FeedParser

from installer._compat.typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from email.message import Message
    from typing import NewType, Tuple

    from installer._compat.typing import Text

    Scheme = NewType("Scheme", str)
    AllSchemes = Tuple[Scheme, ...]

__all__ = [
    "parse_metadata_file",
    "parse_wheel_filename",
    "WheelFilename",
    "SCHEME_NAMES",
]

_WHEEL_FILENAME_REGEX = re.compile(
    r"""
    ^
    (?P<distribution>.+?)
    -(?P<version>.*?)
    (?:-(?P<build_tag>\d[^-]*?))?
    -(?P<tag>.+?-.+?-.+?)
    \.whl
    $
    """,
    re.VERBOSE | re.UNICODE,
)

# Taken directly from PEP 376
SCHEME_NAMES = cast("AllSchemes", ("purelib", "platlib", "headers", "scripts", "data"))
WheelFilename = namedtuple(
    "WheelFilename", ["distribution", "version", "build_tag", "tag"]
)


def parse_metadata_file(contents):
    # type: (Text) -> Message
    """Parse :pep:`376` ``PKG-INFO``-style metadata files.

    ``METADATA`` and ``WHEEL`` files (as per :pep:`427`) use the same syntax
    and can also be parsed using this function.

    :param contents: The entire contents of the file.
    """
    feed_parser = FeedParser()
    feed_parser.feed(contents)
    return feed_parser.close()


def parse_wheel_filename(filename):
    # type: (Text) -> WheelFilename
    """Parse a wheel filename, into it's various components.

    :param filename: The filename to parse.
    """
    wheel_info = _WHEEL_FILENAME_REGEX.match(filename)
    if not wheel_info:
        raise ValueError("Not a valid wheel filename: {}".format(filename))
    return WheelFilename(*wheel_info.groups())
