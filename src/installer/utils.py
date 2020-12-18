"""Utilities related to handling / interacting with wheel files."""

import hashlib
import os
import re
from collections import namedtuple
from email.parser import FeedParser

from installer._compat.typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from email.message import Message
    from typing import BinaryIO, NewType, Tuple

    from installer._compat.typing import Text

    Scheme = NewType("Scheme", str)
    AllSchemes = Tuple[Scheme, ...]

__all__ = [
    "parse_metadata_file",
    "parse_wheel_filename",
    "WheelFilename",
    "SCHEME_NAMES",
]

# Borrowed from https://github.com/python/cpython/blob/v3.9.1/Lib/shutil.py#L52
_WINDOWS = os.name == "nt"
_COPY_BUFSIZE = 1024 * 1024 if _WINDOWS else 64 * 1024

# According to https://www.python.org/dev/peps/pep-0427/#file-name-convention
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
WheelFilename = namedtuple(
    "WheelFilename", ["distribution", "version", "build_tag", "tag"]
)

# According to https://www.python.org/dev/peps/pep-0427/#id7
SCHEME_NAMES = cast("AllSchemes", ("purelib", "platlib", "headers", "scripts", "data"))


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


def copyfileobj_with_hashing(
    source,  # type: BinaryIO
    dest,  # type: BinaryIO
    hash_algorithm,  # type: str
):
    # type: (...) -> Tuple[str, int]
    """Copy a buffer while computing the content's hash and size.

    Copies the source buffer into the destination buffer while computing the
    hash of the contents. Adapted from :ref:`shutil.copyfileobj`.

    :param source: buffer holding the source data
    :param dest: destination buffer
    :param hash_algorithm: hashing algorithm

    :return: size, hash digest of the contents
    """
    hasher = hashlib.new(hash_algorithm)
    size = 0
    while True:
        buf = source.read(_COPY_BUFSIZE)
        if not buf:
            break
        hasher.update(buf)
        dest.write(buf)
        size += len(buf)

    return hasher.hexdigest(), size
