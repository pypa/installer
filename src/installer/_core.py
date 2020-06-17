"""Wheel Installation logic, sans I/O
"""

import posixpath

from installer._compat import StringIO
from installer._compat.typing import TYPE_CHECKING
from installer.parsers import parse_metadata_file
from installer.protocols import Destination, Scheme, WheelSource
from installer.validation import InvalidWheelSource

if TYPE_CHECKING:
    from typing import Callable, List, Optional

    from installer._compat.typing import Text

    Validator = Callable[[WheelSource], None]


__all__ = ["Installer"]


class Installer(object):
    """Implements wheel installation logic

    Supports Wheel version 1.0 (PEP 427).
    """

    def __init__(self, name, validators):
        # type: (Optional[Text], List[Validator]) -> None
        super(Installer, self).__init__()
        self.name = name
        self._validators = validators

    def install(self, source, destination, requested=False):
        # type: (WheelSource, Destination, bool) -> None
        """Install a wheel, as described by ``source``, to ``destination``.
        """

        # Process the WHEEL file
        wheel_metadata_stream = source.open_dist_info(u"WHEEL")
        metadata = parse_metadata_file(wheel_metadata_stream)

        # Ensure compatibility with this wheel version.
        if metadata["Wheel-Version"] != "1.0":
            raise InvalidWheelSource(
                source, "Incompatible Wheel-Version: only support version 1.0",
            )

        self._pass_through_validators(source)

        # Determine where archive root should go.
        if metadata["Root-Is-Purelib"]:
            root_scheme = Scheme.purelib
        else:
            root_scheme = Scheme.platlib

        # Unpack all the files, directly into the correct scheme.
        for path, stream in source.iter_files():
            scheme = self._determine_scheme(path, source=source, fallback=root_scheme)
            destination.write_file(scheme=scheme, path=path, stream=stream)

        # Write INSTALLER, if name is provided.
        if self.name is not None:
            destination.write_file(
                scheme=root_scheme,
                path=posixpath.join(source.dist_info, u"INSTALLER"),
                stream=StringIO(self.name),
            )
        # Write REQUESTED, if requested.
        if requested:
            destination.write_file(
                scheme=root_scheme,
                path=posixpath.join(source.dist_info, u"REQUESTED"),
                stream=StringIO(u""),
            )

        # Rewrite the RECORD at the end.
        destination.rewrite_record(scheme=root_scheme)

    def _pass_through_validators(self, source):
        # type: (WheelSource) -> None
        errors = []
        for validator in self._validators:
            try:
                validator(source)
            except InvalidWheelSource as e:
                errors.append(e)

        if errors:
            raise InvalidWheelSource.from_multiple(source, errors)

    def _determine_scheme(self, path, source, fallback):
        # type: (FSPath, WheelSource, Scheme) -> Scheme
        data_dir = source.data_dir

        # If it's in not `{distribution}-{version}.data`, then it's in root_scheme.
        if not posixpath.commonprefix([data_dir, path]) == data_dir:
            return fallback

        left, right = posixpath.split(path)
        while left != data_dir:
            left, right = posixpath.split(left)

        scheme_name = right
        if scheme_name not in Scheme.__members__:
            msg_fmt = u"{path} is not contained in a valid .data subdirectory."
            raise InvalidWheelSource(
                source,
                msg_fmt.format(path=path)
            )

        return Scheme.__members__[scheme_name]
