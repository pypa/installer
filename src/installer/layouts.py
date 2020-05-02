import os
import re

import six

from installer._compat import pathlib
from installer._compat.typing import TYPE_CHECKING
from installer.exceptions import MetadataNotFound

if TYPE_CHECKING:
    from typing import Iterable, Union

    if six.PY2:
        FileName = Union[str, six.text_type]
    else:
        FileName = str

__all__ = ["DistInfo"]

_NAME_ESCAPE_REGEX = re.compile(r"[^A-Za-z0-9]+")

_VERSION_ESCAPE_REGEX = re.compile(r"[^A-Za-z0-9\.]+")


def _name_escape(s):
    # type: (six.text_type) -> six.text_type
    """Filename-escape the distribution name according to PEP 376.

    1. Replace any runs of non-alphanumeric characters with a single ``-``.
    2.  Any ``-`` characters are replaced with ``_``.
    """
    return _NAME_ESCAPE_REGEX.sub("_", s)


def _version_escape(v):
    # type: (six.text_type) -> six.text_type
    """Filename-escape the version string according to PEP 376.

    1. Spaces become dots, and all other non-alphanumeric characters (except
       dots) become dashes, with runs of multiple dashes condensed to a single
       dash.
    2. Any ``-`` characters are replaced with ``_``.
    """
    return _VERSION_ESCAPE_REGEX.sub("_", v.replace(" ", "."))


class DistInfo(object):
    def __init__(self, directory_name):
        # type: (str) -> None
        self.directory_name = directory_name

    @classmethod
    def find(cls, project_name, project_version, entry_names):
        # type: (str, str, Iterable[FileName]) -> DistInfo
        escaped_project_name = _name_escape(project_name).lower()
        escaped_project_version = _version_escape(project_version)

        for entry_name in entry_names:
            stem, ext = os.path.splitext(entry_name)
            if ext.lower() != ".dist-info":
                continue
            name, _, version = stem.partition("-")
            if not version:  # Dash not found.
                continue
            if escaped_project_name != _name_escape(name).lower():
                continue
            if escaped_project_version != _version_escape(version):
                continue
            # The directory name needs to be str on Python 2 so we can
            # correctly build paths with pathlib2, which does not take unicode.
            return cls(six.ensure_str(entry_name))

        expected_name = "{}-{}.dist-info".format(
            escaped_project_name, escaped_project_version,
        )
        raise MetadataNotFound(expected_name)

    @property
    def record(self):
        # type: () -> pathlib.PurePosixPath
        return pathlib.PurePosixPath(self.directory_name, "RECORD")

    @property
    def installer(self):
        # type: () -> pathlib.PurePosixPath
        return pathlib.PurePosixPath(self.directory_name, "INSTALLER")

    @property
    def direct_url_json(self):
        # type: () -> pathlib.PurePosixPath
        return pathlib.PurePosixPath(self.directory_name, "direct_url.json")
