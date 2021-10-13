"""Handles all file writing and post-installation processing."""

import io
import os

from installer._compat import FileExistsError
from installer._compat.typing import TYPE_CHECKING
from installer.records import Hash, RecordEntry
from installer.scripts import Script
from installer.utils import (
    Scheme,
    construct_record_file,
    copyfileobj_with_hashing,
    fix_shebang,
)

if TYPE_CHECKING:
    from typing import BinaryIO, Dict, Iterable, Tuple

    from installer._compat.typing import FSPath, Text
    from installer.scripts import LauncherKind, ScriptSection


class WheelDestination(object):
    """Handles writing the unpacked files, script generation and ``RECORD`` generation.

    Subclasses provide the concrete script generation logic, as well as the RECORD file
    (re)writing.
    """

    def write_script(self, name, module, attr, section):
        # type: (Text, Text, Text, ScriptSection) -> RecordEntry
        """Write a script in the correct location to invoke given entry point.

        :param name: name of the script
        :param module: module path, to load the entry point from
        :param attr: final attribute access, for the entry point
        :param section: Denotes the "entry point section" where this was specified.
            Valid values are ``"gui"`` and ``"console"``.
        :type section: str

        Example usage/behaviour::

            >>> dest.write_script("pip", "pip._internal.cli", "main", "console")

        """
        raise NotImplementedError

    def write_file(self, scheme, path, stream):
        # type: (Scheme, FSPath, BinaryIO) -> RecordEntry
        """Write a file to correct ``path`` within the ``scheme``.

        :param scheme: scheme to write the file in (like "purelib", "platlib" etc).
        :param path: path within that scheme
        :param stream: contents of the file

        The stream would be closed by the caller, after this call.

        Example usage/behaviour::

            >>> with open("__init__.py") as stream:
            ...     dest.write_file("purelib", "pkg/__init__.py", stream)

        """
        raise NotImplementedError

    def finalize_installation(self, scheme, record_file_path, records):
        # type: (Scheme, FSPath, Iterable[Tuple[Scheme, RecordEntry]]) -> None
        """Finalize installation, after all the files are written.

        Handles (re)writing of the ``RECORD`` file.

        :param scheme: scheme to write the ``RECORD`` file in
        :param record_file_path: path of the ``RECORD`` file with that scheme
        :param records: entries to write to the ``RECORD`` file

        Example usage/behaviour::

            >>> dest.finalize_installation("purelib")

        """
        raise NotImplementedError


class SchemeDictionaryDestination(WheelDestination):
    """Destination, based on a mapping of {scheme: file-system-path}."""

    def __init__(
        self,
        scheme_dict,
        interpreter,
        script_kind,
        hash_algorithm="sha256",
    ):
        # type: (Dict[str, str], str, LauncherKind, str) -> None
        """Construct a ``SchemeDictionaryDestination`` object.

        :param scheme_dict: a mapping of {scheme: file-system-path}
        :param interpreter: the interpreter to use for generating scripts
        :param script_kind: the "kind" of launcher script to use
        :param hash_algorithm: the hashing algorithm to use, which is a member
            of :any:`hashlib.algorithms_available` (ideally from
            :any:`hashlib.algorithms_guaranteed`).
        """
        self.scheme_dict = scheme_dict
        self.interpreter = interpreter
        self.script_kind = script_kind
        self.hash_algorithm = hash_algorithm

    def write_to_fs(self, scheme, path, stream):
        # type: (Scheme, FSPath, BinaryIO) -> RecordEntry
        """Write contents of ``stream`` to the correct location on the filesystem.

        :param scheme: scheme to write the file in (like "purelib", "platlib" etc).
        :param path: path within that scheme
        :param stream: contents of the file

        - Ensures that an existing file is not being overwritten.
        - Hashes the written content, to determine the entry in the ``RECORD`` file.
        """
        target_path = os.path.join(self.scheme_dict[scheme], path)
        if os.path.exists(target_path):
            message = "File already exists: {}".format(target_path)
            raise FileExistsError(message)

        parent_folder = os.path.dirname(target_path)
        if not os.path.exists(parent_folder):
            os.makedirs(parent_folder)

        with open(target_path, "wb") as f:
            hash_, size = copyfileobj_with_hashing(stream, f, self.hash_algorithm)

        return RecordEntry(path, Hash(self.hash_algorithm, hash_), size)

    def write_file(self, scheme, path, stream):
        # type: (Scheme, FSPath, BinaryIO) -> RecordEntry
        """Write a file to correct ``path`` within the ``scheme``.

        :param scheme: scheme to write the file in (like "purelib", "platlib" etc).
        :param path: path within that scheme
        :param stream: contents of the file

        - Changes the shebang for files in the "scripts" scheme.
        - Uses :py:meth:`SchemeDictionaryDestination.write_to_fs` for the
          filesystem interaction.
        """
        if scheme == "scripts":
            with fix_shebang(stream, self.interpreter) as stream_with_different_shebang:
                return self.write_to_fs(scheme, path, stream_with_different_shebang)

        return self.write_to_fs(scheme, path, stream)

    def write_script(self, name, module, attr, section):
        # type: (Text, Text, Text, ScriptSection) -> RecordEntry
        """Write a script to invoke an entrypoint.

        :param name: name of the script
        :param module: module path, to load the entry point from
        :param attr: final attribute access, for the entry point
        :param section: Denotes the "entry point section" where this was specified.
            Valid values are ``"gui"`` and ``"console"``.
        :type section: str

        - Generates a launcher using :any:`Script.generate`.
        - Writes to the "scripts" scheme.
        - Uses :py:meth:`SchemeDictionaryDestination.write_to_fs` for the
          filesystem interaction.
        """
        script = Script(name, module, attr, section)
        script_name, data = script.generate(self.interpreter, self.script_kind)

        with io.BytesIO(data) as stream:
            entry = self.write_to_fs(Scheme("scripts"), script_name, stream)

            path = os.path.join(self.scheme_dict[Scheme("scripts")], script_name)
            mode = os.stat(path).st_mode
            mode |= (mode & 0o444) >> 2
            os.chmod(path, mode)

            return entry

    def finalize_installation(self, scheme, record_file_path, records):
        # type: (Scheme, FSPath, Iterable[Tuple[Scheme, RecordEntry]]) -> None
        """Finalize installation, by writing the ``RECORD`` file.

        :param scheme: scheme to write the ``RECORD`` file in
        :param record_file_path: path of the ``RECORD`` file with that scheme
        :param records: entries to write to the ``RECORD`` file
        """
        with construct_record_file(records) as record_stream:
            self.write_to_fs(scheme, record_file_path, record_stream)
