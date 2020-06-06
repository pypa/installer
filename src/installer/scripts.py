import io
import shlex
import zipfile

from installer import _scripts
from installer._compat import builtins, importlib_resources
from installer._compat.typing import TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Literal, Mapping, Optional, Tuple

    LauncherKind = Literal["posix", "win-ia32", "win-amd64", "win-arm"]
    ScriptSection = Literal["console", "gui"]


__all__ = ["InvalidScript", "Script"]


_ALLOWED_LAUNCHERS = {
    ("console", "win-ia32"): "t32.exe",
    ("console", "win-amd64"): "t64.exe",
    ("console", "win-arm"): "t_arm.exe",
    ("gui", "win-ia32"): "w32.exe",
    ("gui", "win-amd64"): "w64.exe",
    ("gui", "win-arm"): "w_arm.exe",
}  # type: Mapping[Tuple[ScriptSection, LauncherKind], str]

_SCRIPT_TEMPLATE = """\
# -*- coding: utf-8 -*-
import re
import sys
from {module} import {import_name}
if __name__ == "__main__":
    sys.argv[0] = re.sub(r"(-script\\.pyw|\\.exe)?$", "", sys.argv[0])
    sys.exit({func_path}())
"""


def _is_executable_simple(executable):
    # type: (builtins.binary_type) -> bool
    if b" " in executable:
        return False
    shebang_length = len(executable) + 3  # Prefix #! and newline after.
    # According to distlib, Darwin can handle up to 512 characters. But I want
    # to avoid platform sniffing to make this as platform agnostic as possible.
    # The "complex" script isn't that bad anyway.
    return shebang_length <= 127


def _quote_compat(s):  # pragma: no cover
    # type: (builtins.text_type) -> builtins.text_type
    """Crude implementation taken from shlex.quote().
    """
    return u"'" + s.replace(u"'", u"'\"'\"'") + u"'"


def _build_shebang(executable, forlauncher):
    # type: (builtins.text_type, bool) -> builtins.binary_type
    """Build a shebang line.

    The non-launcher cases are taken directly from distlib's implementation,
    which tries its best to account for command length, spaces in path, etc.

    https://bitbucket.org/pypa/distlib/src/58cd5c6/distlib/scripts.py#lines-124
    """
    executable_bytes = executable.encode("utf-8")
    if forlauncher:  # The launcher can just use the command as-is.
        return b"#!" + executable_bytes
    if _is_executable_simple(executable_bytes):
        return b"#!" + executable_bytes

    # Shebang support for an executable with a space in it is under-specified
    # and platform-dependent, so we use a clever hack to generate a script to
    # run in ``/bin/sh`` that should work on all reasonably modern platforms.
    # Read the following message to understand how the hack works:
    # https://github.com/pradyunsg/installer/pull/4#issuecomment-623668717

    quote = getattr(shlex, "quote", _quote_compat)
    quoted = quote(executable).encode("utf-8")
    # I don't understand a lick what this is trying to do.
    return b"#!/bin/sh\n'''exec' " + quoted + b' "$0" "$@"\n' + b"' '''"


class InvalidScript(ValueError):
    """Raised if the user provides incorrect script section or kind.
    """


class Script(object):
    __slots__ = ("name", "module", "attr", "section")

    def __init__(self, name, module, attr, section):
        # type: (str, str, str, ScriptSection) -> None
        self.name = name
        self.module = module
        self.attr = attr
        self.section = section

    def __repr__(self):
        # type: () -> str
        return "Script(name={!r}, module={!r}, attr={!r}".format(
            self.name, self.module, self.attr,
        )

    def _get_launcher_data(self, kind):
        # type: (LauncherKind) -> Optional[builtins.binary_type]
        if kind == "posix":
            return None
        key = (self.section, kind)
        try:
            name = _ALLOWED_LAUNCHERS[key]
        except KeyError:
            error = "{!r} not in {!r}".format(key, sorted(_ALLOWED_LAUNCHERS))
            raise InvalidScript(error)
        return importlib_resources.read_binary(_scripts, name)

    def generate(self, executable, kind):
        # type: (str, LauncherKind) -> Tuple[str, builtins.binary_type]
        launcher = self._get_launcher_data(kind)
        shebang = _build_shebang(executable, forlauncher=bool(launcher))
        code = _SCRIPT_TEMPLATE.format(
            module=self.module,
            import_name=self.attr.split(".")[0],
            func_path=self.attr,
        ).encode("utf-8")

        if launcher is None:
            return (self.name, shebang + b"\n" + code)

        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as zf:
            zf.writestr("__main__.py", code)
        name = "{}.exe".format(self.name)
        data = launcher + shebang + b"\n" + stream.getvalue()
        return (name, data)
