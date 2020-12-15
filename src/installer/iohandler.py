"""Handling wheel installation I/O-related functionality."""
import contextlib
import hashlib
import os

from installer._compat.typing import TYPE_CHECKING

from .records import Hash, Record

if TYPE_CHECKING:
    from typing import BinaryIO, Callable, Dict, Iterator, Tuple

    from ._compat.typing import FSPath

    CopyHandler = Callable[[BinaryIO, BinaryIO, str], Tuple[int, Hash]]

_BLOCK_SIZE = 4096


def basic_copy_handler(
    source,  # type: BinaryIO
    dest,  # type: BinaryIO
    hash_algorithm="sha256",  # type: str
):
    # type: (...) -> Tuple[int, Hash]
    """Copy a buffer and compute its hash and size.

    Copies the source buffer into the specified destination buffer. It also computes
    the hash of the file to avoid traversing the source twice.

    :param source: buffer holding the source data
    :param dest: destination buffer
    :param hash_algorithm: hashing algorithm

    :return: size and ``Hash`` tuple of the copied buffer
    """
    hasher = hashlib.new(hash_algorithm)
    size = 0
    while True:
        buf = source.read(_BLOCK_SIZE)
        if not buf:
            break
        hasher.update(buf)
        dest.write(buf)
        size += len(buf)

    hash_ = Hash.parse("sha256={}".format(hasher.hexdigest()))
    return size, hash_


class IOHandler(object):
    """Implement I/O operations for installers."""

    def __init__(
        self,
        scheme_path_map,  # type: Dict[str, FSPath]
        hash_algorithm="sha256",  # type: str
        copy_handler=basic_copy_handler,  # type: CopyHandler
    ):
        # type: (...) -> None
        """Construct an ``IOHandler`` instance.

        :param scheme_path_map: mapping of scheme names to paths
        :param hash_algorithm: hashing algorithm passed to the ``copy_handler``
        :param copy_handler: callable implementing the copy and hashing operation
        """
        self._scheme_path_map = scheme_path_map
        self._hash_algorithm = hash_algorithm
        self._copy_handler = copy_handler

    @contextlib.contextmanager
    def open_source(
        self,
        scheme,  # type: str
        source_path,  # type: FSPath
    ):
        # type: (...) -> Iterator[BinaryIO]
        """Open the specified source and provide a destination buffer.

        This function will determine the correct destination based on the specified
        scheme and provide a buffer where the contents can be written.

        :param scheme: scheme of the source
        :param source_path: relative path to the file in the wheel

        :return a buffer for the destination
        """
        try:
            dest_dir = self._scheme_path_map[scheme]
        except KeyError:
            raise ValueError("No such scheme: {}".format(scheme))  # FIXME

        dest_path = os.path.join(dest_dir, source_path)
        parent_path = os.path.dirname(dest_path)

        if not os.path.exists(parent_path):
            # FIXME raise custom exception
            os.makedirs(parent_path)

        with open(dest_path, "wb") as dest_buf:
            yield dest_buf

    def copy_file(
        self,
        scheme,  # type: str
        path,  # type: FSPath
        stream,  # type: BinaryIO
    ):
        # type: (...) -> Record
        """Copy the provided path into the appropriate scheme location.

        :param scheme: destination scheme
        :param path: path inside the Python package
        :param stream: source file contents

        :return record of the installed file
        """
        with self.open_source(scheme, path) as dest_buf:
            size, hash_ = self._copy_handler(stream, dest_buf, self._hash_algorithm)

        return Record(path, hash_=hash_, size=size)
