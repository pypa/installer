"""Tests for installer.utils
"""

import hashlib
import textwrap
from email.message import Message
from io import BytesIO

import pytest
from test_records import SAMPLE_RECORDS

from installer.records import RecordEntry
from installer.utils import (
    WheelFilename,
    construct_record_file,
    copyfileobj_with_hashing,
    fix_shebang,
    parse_entrypoints,
    parse_metadata_file,
    parse_wheel_filename,
)


class TestParseMetadata:
    def test_basics(self):
        result = parse_metadata_file(
            textwrap.dedent(
                """\
            Name: package
            Version: 1.0.0
            Multi-Use-Field: 1
            Multi-Use-Field: 2
            Multi-Use-Field: 3
            """
            )
        )
        assert isinstance(result, Message)
        assert result.get("Name") == "package"
        assert result.get("version") == "1.0.0"
        assert result.get_all("MULTI-USE-FIELD") == ["1", "2", "3"]


class TestParseWheelFilename:
    @pytest.mark.parametrize(
        "string, expected",
        [
            # Crafted package name w/ a "complex" version and build tag
            (
                "package-1!1.0+abc.7-753-py3-none-any.whl",
                WheelFilename("package", "1!1.0+abc.7", "753", "py3-none-any"),
            ),
            # Crafted package name w/ a "complex" version and no build tag
            (
                "package-1!1.0+abc.7-py3-none-any.whl",
                WheelFilename("package", "1!1.0+abc.7", None, "py3-none-any"),
            ),
            # Use real tensorflow wheel names
            (
                "tensorflow-2.3.0-cp38-cp38-macosx_10_11_x86_64.whl",
                WheelFilename(
                    "tensorflow", "2.3.0", None, "cp38-cp38-macosx_10_11_x86_64"
                ),
            ),
            (
                "tensorflow-2.3.0-cp38-cp38-manylinux2010_x86_64.whl",
                WheelFilename(
                    "tensorflow", "2.3.0", None, "cp38-cp38-manylinux2010_x86_64"
                ),
            ),
            (
                "tensorflow-2.3.0-cp38-cp38-win_amd64.whl",
                WheelFilename("tensorflow", "2.3.0", None, "cp38-cp38-win_amd64"),
            ),
        ],
    )
    def test_valid_cases(self, string, expected):
        got = parse_wheel_filename(string)
        assert expected == got, (expected, got)

    @pytest.mark.parametrize(
        "string",
        [
            # Not ".whl"
            "pip-20.0.0-py2.py3-none-any.zip",
            # No tag
            "pip-20.0.0.whl",
            # Empty tag
            "pip-20.0.0---.whl",
        ],
    )
    def test_invalid_cases(self, string):
        with pytest.raises(ValueError):
            parse_wheel_filename(string)


class TestCopyFileObjWithHashing(object):
    def test_basic_functionality(self):
        data = b"input data is this"
        hash_ = hashlib.sha256(data).hexdigest()
        size = len(data)

        with BytesIO(data) as source:
            with BytesIO() as dest:
                result = copyfileobj_with_hashing(source, dest, hash_algorithm="sha256")
                written_data = dest.getvalue()

        assert result == (hash_, size)
        assert written_data == data


class TestScript:
    @pytest.mark.parametrize(
        ("data", "expected"),
        [
            (
                b"#!python\ntest",
                b"#!/my/python\ntest",
            ),
            (
                b"#!pythonw\ntest",
                b"#!/my/python\ntest",
            ),
            (
                b"#!python something\ntest",
                b"#!/my/python\ntest",
            ),
            (
                b"#!python",
                b"#!/my/python\n",
            ),
        ],
    )
    def test_replace_shebang(self, data, expected):
        with BytesIO(data) as source:
            with fix_shebang(source, "/my/python") as stream:
                result = stream.read()
        assert result == expected

    @pytest.mark.parametrize(
        "data",
        [
            b"#!py\ntest",
            b"#!something\ntest",
            b"#something\ntest",
            b"#something",
            b"something",
        ],
    )
    def test_keep_data(self, data):
        with BytesIO(data) as source:
            with fix_shebang(source, "/my/python") as stream:
                result = stream.read()
        assert result == data


class TestConstructRecord:
    def test_construct(self):
        records = [
            RecordEntry.from_elements(*elements) for elements, _, _ in SAMPLE_RECORDS
        ]
        assert construct_record_file(records).read() == (
            b"test1.py,sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4,6\n"
            b"test2.py,sha256=fW_Xd08Nh2JNptzxbQ09EEwxkedx--LznIau1LK_Gg8,6\n"
            b"test3.py,sha256=qwPDTx7OCCEf4qgDn9ZCQZmz9de1X_E7ETSzZHdsRcU,6\n"
            b"test4.py,sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4,7\n"
            b"test5.py,sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4,\n"
            b"test6.py,,\n"
        )


class TestParseEntryPoints:
    @pytest.mark.parametrize(
        ("script", "expected"),
        [
            (u"", []),
            (
                u"""
                    [console_scripts]
                    package = package.__main__:package
                """,
                [
                    ("package", "package.__main__", "package", "console"),
                ],
            ),
            (
                u"""
                    [gui_scripts]
                    package = package.__main__:package
                """,
                [
                    ("package", "package.__main__", "package", "gui"),
                ],
            ),
            (
                u"""
                    [console_scripts]
                    magic-cli = magic.cli:main

                    [gui_scripts]
                    magic-gui = magic.gui:main
                """,
                [
                    ("magic-cli", "magic.cli", "main", "console"),
                    ("magic-gui", "magic.gui", "main", "gui"),
                ],
            ),
        ],
    )
    def test_valid(self, script, expected):
        iterable = parse_entrypoints(textwrap.dedent(script))
        assert list(iterable) == expected, expected
