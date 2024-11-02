import io
import zipfile
from pathlib import Path

import pytest

from installer import _scripts
from installer.scripts import InvalidScript, Script


def test_script_generate_simple():
    script = Script("foo", "foo.bar", "baz.qux", section="console")
    name, data = script.generate("/path/to/my/python", kind="posix")

    assert name == "foo"
    assert data.startswith(b"#!/path/to/my/python\n")
    assert b"\nfrom foo.bar import baz\n" in data
    assert b"baz.qux()" in data


def test_script_generate_space_in_executable():
    script = Script("foo", "foo.bar", "baz.qux", section="console")
    name, data = script.generate("/path to my/python", kind="posix")

    assert name == "foo"
    assert data.startswith(b"#!/bin/sh\n")
    assert b" '/path to my/python'" in data
    assert b"\nfrom foo.bar import baz\n" in data
    assert b"baz.qux()" in data


def _read_launcher_data(section, kind):
    prefix = {"console": "t", "gui": "w"}[section]
    suffix = {"win-ia32": "32", "win-amd64": "64", "win-arm": "_arm"}[kind]
    file = Path(_scripts.__file__).parent / f"{prefix}{suffix}.exe"
    return file.read_bytes()


@pytest.mark.parametrize("section", ["console", "gui"])
@pytest.mark.parametrize("kind", ["win-ia32", "win-amd64", "win-arm"])
def test_script_generate_launcher(section, kind):
    launcher_data = _read_launcher_data(section, kind)

    script = Script("foo", "foo.bar", "baz.qux", section=section)
    name, data = script.generate("#!C:\\path to my\\python.exe\n", kind=kind)

    prefix_len = len(launcher_data) + len(b"#!C:\\path to my\\python.exe\n")
    stream = io.BytesIO(data[prefix_len:])
    with zipfile.ZipFile(stream) as zf:
        code = zf.read("__main__.py")

    assert name == "foo.exe"
    assert data.startswith(launcher_data)
    if section == "gui":
        assert b"#!C:\\path to my\\pythonw.exe\n" in data
    else:
        assert b"#!C:\\path to my\\python.exe\n" in data
    assert b"\nfrom foo.bar import baz\n" in code
    assert b"baz.qux()" in code


@pytest.mark.parametrize(
    "section, kind",
    [("nonexist", "win-ia32"), ("console", "nonexist"), ("nonexist", "nonexist")],
)
def test_script_generate_launcher_error(section, kind):
    script = Script("foo", "foo.bar", "baz.qux", section=section)
    with pytest.raises(InvalidScript):
        script.generate("#!C:\\path to my\\python.exe\n", kind=kind)
