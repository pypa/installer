"""Utilities related to handling / interacting with wheel files."""

import contextlib
import hashlib
import io
import os
import re
import sys
from collections import namedtuple
from email.parser import FeedParser
from typing import NewType

from installer._compat import ConfigParser
from installer._compat.typing import TYPE_CHECKING, Text, cast

Scheme = NewType("Scheme", str)

if TYPE_CHECKING:
    from email.message import Message
    from typing import BinaryIO, Iterable, Iterator, Tuple

    from installer.records import RecordEntry
    from installer.scripts import LauncherKind, ScriptSection

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

# Adapted from https://github.com/python/importlib_metadata/blob/v3.4.0/importlib_metadata/__init__.py#L90  # noqa
_ENTRYPOINT_REGEX = re.compile(
    r"""
    (?P<module>[\w.]+)\s*
    (:\s*(?P<attrs>[\w.]+))\s*
    (?P<extras>\[.*\])?\s*$
    """,
    re.VERBOSE | re.UNICODE,
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


def get_launcher_kind():  # pragma: no cover
    # type: () -> LauncherKind
    """Get the launcher kind for the current machine."""
    if os.name != "nt":
        return "posix"

    if "amd64" in sys.version.lower():
        return "win-amd64"
    if "(arm64)" in sys.version.lower():
        return "win-arm64"
    if "(arm)" in sys.version.lower():
        return "win-arm"
    if sys.platform == "win32":
        return "win-ia32"

    raise NotImplementedError("Unknown launcher kind for this machine")


@contextlib.contextmanager
def fix_shebang(stream, interpreter):
    # type: (BinaryIO, str) -> Iterator[BinaryIO]
    """Replace ^#!python shebang in a stream with the correct interpreter.

    The original stream should be closed by the caller.
    """
    stream.seek(0)
    if stream.read(8) == b"#!python":
        new_stream = io.BytesIO()
        # write our new shebang
        new_stream.write("#!{}\n".format(interpreter).encode())
        # copy the rest of the stream
        stream.seek(0)
        stream.readline()  # skip first line
        while True:
            buf = stream.read(_COPY_BUFSIZE)
            if not buf:
                break
            new_stream.write(buf)
        new_stream.seek(0)
        yield new_stream
        new_stream.close()
    else:
        stream.seek(0)
        yield stream


def construct_record_file(records):
    # type: (Iterable[Tuple[Scheme, RecordEntry]]) -> BinaryIO
    """Construct a RECORD file given some records.

    The original stream should be closed by the caller.
    """
    stream = io.BytesIO()
    for scheme, record in records:
        stream.write(str(record).encode("utf-8") + b"\n")
    stream.seek(0)
    return stream


def parse_entrypoints(text):
    # type: (Text) -> Iterable[Tuple[Text, Text, Text, ScriptSection]]
    # Borrowed from https://github.com/python/importlib_metadata/blob/v3.4.0/importlib_metadata/__init__.py#L115  # noqa
    config = ConfigParser(delimiters="=")
    config.optionxform = Text  # type: ignore
    config.read_string(text)

    for section in config.sections():
        if section not in ["console_scripts", "gui_scripts"]:
            continue

        for name, value in config.items(section):
            assert isinstance(name, Text)
            match = _ENTRYPOINT_REGEX.match(value)
            assert match

            module = match.group("module")
            assert isinstance(module, Text)

            attrs = match.group("attrs")
            # TODO: make this a proper error, which can be caught.
            assert attrs is not None
            assert isinstance(attrs, Text)

            script_section = cast("ScriptSection", section[: -len("_scripts")])

            yield name, module, attrs, script_section
