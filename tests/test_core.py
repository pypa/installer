import hashlib
import textwrap
from io import BytesIO
from unittest import mock

import pytest

from installer import install
from installer.exceptions import InvalidWheelSource
from installer.records import RecordEntry
from installer.sources import WheelSource


# --------------------------------------------------------------------------------------
# Helpers
# --------------------------------------------------------------------------------------
def hash_and_size(data):
    return hashlib.sha256(data).hexdigest(), len(data)


@pytest.fixture
def mock_destination():
    retval = mock.Mock()

    # A hacky approach to making sure we got the right objects going in.
    def custom_write_file(scheme, path, stream, is_executable):
        assert isinstance(stream, BytesIO)
        return (path, scheme, 0)

    def custom_write_script(name, module, attr, section):
        return (name, module, attr, section)

    retval.write_file.side_effect = custom_write_file
    retval.write_script.side_effect = custom_write_script

    return retval


class FakeWheelSource(WheelSource):
    def __init__(self, *, distribution, version, regular_files, dist_info_files):
        super().__init__(distribution, version)

        self.dist_info_files = {
            file: textwrap.dedent(content.decode("utf-8"))
            for file, content in dist_info_files.items()
        }
        self.regular_files = {
            file: textwrap.dedent(content.decode("utf-8")).encode("utf-8")
            for file, content in regular_files.items()
        }

        # Compute RECORD file.
        _records = [record for record, _, _ in self.get_contents()]
        self.dist_info_files["RECORD"] = "\n".join(
            sorted(
                ",".join([file, "sha256=" + hash_, str(size)])
                for file, hash_, size in _records
            )
        )

    @property
    def dist_info_filenames(self):
        return list(self.dist_info_files)

    def read_dist_info(self, filename):
        return self.dist_info_files[filename]

    def validate_record(self) -> None:
        # Skip validation since the logic is different.
        return

    def get_contents(self):
        # Sort for deterministic behaviour for Python versions that do not preserve
        # insertion order for dictionaries.
        for file, content in sorted(self.regular_files.items()):
            hashed, size = hash_and_size(content)
            record = (file, f"sha256={hashed}", str(size))
            with BytesIO(content) as stream:
                yield record, stream, False

        # Sort for deterministic behaviour for Python versions that do not preserve
        # insertion order for dictionaries.
        for file, text in sorted(self.dist_info_files.items()):
            content = text.encode("utf-8")
            hashed, size = hash_and_size(content)
            record = (
                self.dist_info_dir + "/" + file,
                f"sha256={hashed}",
                str(size),
            )
            with BytesIO(content) as stream:
                yield record, stream, False


# --------------------------------------------------------------------------------------
# Actual Tests
# --------------------------------------------------------------------------------------
class TestInstall:
    def test_calls_destination_correctly(self, mock_destination):
        # Create a fake wheel
        source = FakeWheelSource(
            distribution="fancy",
            version="1.0.0",
            regular_files={
                "fancy/__init__.py": b"""\
                    def main():
                        print("I'm a fancy package")
                """,
                "fancy/__main__.py": b"""\
                    if __name__ == "__main__":
                        from . import main
                        main()
                """,
            },
            dist_info_files={
                "top_level.txt": b"""\
                    fancy
                """,
                "entry_points.txt": b"""\
                    [console_scripts]
                    fancy = fancy:main

                    [gui_scripts]
                    fancy-gui = fancy:main
                """,
                "WHEEL": b"""\
                    Wheel-Version: 1.0
                    Generator: magic (1.0.0)
                    Root-Is-Purelib: true
                    Tag: py3-none-any
                """,
                "METADATA": b"""\
                    Metadata-Version: 2.1
                    Name: fancy
                    Version: 1.0.0
                    Summary: A fancy package
                    Author: Agendaless Consulting
                    Author-email: nobody@example.com
                    License: MIT
                    Keywords: fancy amazing
                    Platform: UNKNOWN
                    Classifier: Intended Audience :: Developers
                """,
            },
        )

        install(
            source=source,
            destination=mock_destination,
            additional_metadata={
                "fun_file.txt": b"this should be in dist-info!",
            },
        )

        mock_destination.assert_has_calls(
            [
                mock.call.write_script(
                    name="fancy",
                    module="fancy",
                    attr="main",
                    section="console",
                ),
                mock.call.write_script(
                    name="fancy-gui",
                    module="fancy",
                    attr="main",
                    section="gui",
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy/__init__.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy/__main__.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/METADATA",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/WHEEL",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/entry_points.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/top_level.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/fun_file.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.finalize_installation(
                    scheme="purelib",
                    record_file_path="fancy-1.0.0.dist-info/RECORD",
                    records=[
                        ("scripts", ("fancy", "fancy", "main", "console")),
                        ("scripts", ("fancy-gui", "fancy", "main", "gui")),
                        ("purelib", ("fancy/__init__.py", "purelib", 0)),
                        ("purelib", ("fancy/__main__.py", "purelib", 0)),
                        ("purelib", ("fancy-1.0.0.dist-info/METADATA", "purelib", 0)),
                        ("purelib", ("fancy-1.0.0.dist-info/WHEEL", "purelib", 0)),
                        (
                            "purelib",
                            ("fancy-1.0.0.dist-info/entry_points.txt", "purelib", 0),
                        ),
                        (
                            "purelib",
                            ("fancy-1.0.0.dist-info/top_level.txt", "purelib", 0),
                        ),
                        (
                            "purelib",
                            ("fancy-1.0.0.dist-info/fun_file.txt", "purelib", 0),
                        ),
                        (
                            "purelib",
                            RecordEntry("fancy-1.0.0.dist-info/RECORD", None, None),
                        ),
                    ],
                ),
            ]
        )

    def test_no_entrypoints_is_ok(self, mock_destination):
        # Create a fake wheel
        source = FakeWheelSource(
            distribution="fancy",
            version="1.0.0",
            regular_files={
                "fancy/__init__.py": b"""\
                    def main():
                        print("I'm a fancy package")
                """,
                "fancy/__main__.py": b"""\
                    if __name__ == "__main__":
                        from . import main
                        main()
                """,
            },
            dist_info_files={
                "top_level.txt": b"""\
                    fancy
                """,
                "WHEEL": b"""\
                    Wheel-Version: 1.0
                    Generator: magic (1.0.0)
                    Root-Is-Purelib: true
                    Tag: py3-none-any
                """,
                "METADATA": b"""\
                    Metadata-Version: 2.1
                    Name: fancy
                    Version: 1.0.0
                    Summary: A fancy package
                    Author: Agendaless Consulting
                    Author-email: nobody@example.com
                    License: MIT
                    Keywords: fancy amazing
                    Platform: UNKNOWN
                    Classifier: Intended Audience :: Developers
                """,
            },
        )

        install(
            source=source,
            destination=mock_destination,
            additional_metadata={
                "fun_file.txt": b"this should be in dist-info!",
            },
        )

        mock_destination.assert_has_calls(
            [
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy/__init__.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy/__main__.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/METADATA",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/WHEEL",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/top_level.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/fun_file.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.finalize_installation(
                    scheme="purelib",
                    record_file_path="fancy-1.0.0.dist-info/RECORD",
                    records=[
                        ("purelib", ("fancy/__init__.py", "purelib", 0)),
                        ("purelib", ("fancy/__main__.py", "purelib", 0)),
                        ("purelib", ("fancy-1.0.0.dist-info/METADATA", "purelib", 0)),
                        ("purelib", ("fancy-1.0.0.dist-info/WHEEL", "purelib", 0)),
                        (
                            "purelib",
                            ("fancy-1.0.0.dist-info/top_level.txt", "purelib", 0),
                        ),
                        (
                            "purelib",
                            ("fancy-1.0.0.dist-info/fun_file.txt", "purelib", 0),
                        ),
                        (
                            "purelib",
                            RecordEntry("fancy-1.0.0.dist-info/RECORD", None, None),
                        ),
                    ],
                ),
            ]
        )

    def test_handles_platlib(self, mock_destination):
        # Create a fake wheel
        source = FakeWheelSource(
            distribution="fancy",
            version="1.0.0",
            regular_files={
                "fancy/__init__.py": b"""\
                    def main():
                        print("I'm a fancy package")
                """,
                "fancy/__main__.py": b"""\
                    if __name__ == "__main__":
                        from . import main
                        main()
                """,
            },
            dist_info_files={
                "top_level.txt": b"""\
                    fancy
                """,
                "entry_points.txt": b"""\
                    [console_scripts]
                    fancy = fancy:main

                    [gui_scripts]
                    fancy-gui = fancy:main
                """,
                "WHEEL": b"""\
                    Wheel-Version: 1.0
                    Generator: magic (1.0.0)
                    Root-Is-Purelib: false
                    Tag: py3-none-any
                """,
                "METADATA": b"""\
                    Metadata-Version: 2.1
                    Name: fancy
                    Version: 1.0.0
                    Summary: A fancy package
                    Author: Agendaless Consulting
                    Author-email: nobody@example.com
                    License: MIT
                    Keywords: fancy amazing
                    Platform: UNKNOWN
                    Classifier: Intended Audience :: Developers
                """,
            },
        )

        install(
            source=source,
            destination=mock_destination,
            additional_metadata={
                "fun_file.txt": b"this should be in dist-info!",
            },
        )

        mock_destination.assert_has_calls(
            [
                mock.call.write_script(
                    name="fancy",
                    module="fancy",
                    attr="main",
                    section="console",
                ),
                mock.call.write_script(
                    name="fancy-gui",
                    module="fancy",
                    attr="main",
                    section="gui",
                ),
                mock.call.write_file(
                    scheme="platlib",
                    path="fancy/__init__.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="platlib",
                    path="fancy/__main__.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="platlib",
                    path="fancy-1.0.0.dist-info/METADATA",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="platlib",
                    path="fancy-1.0.0.dist-info/WHEEL",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="platlib",
                    path="fancy-1.0.0.dist-info/entry_points.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="platlib",
                    path="fancy-1.0.0.dist-info/top_level.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="platlib",
                    path="fancy-1.0.0.dist-info/fun_file.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.finalize_installation(
                    scheme="platlib",
                    record_file_path="fancy-1.0.0.dist-info/RECORD",
                    records=[
                        ("scripts", ("fancy", "fancy", "main", "console")),
                        ("scripts", ("fancy-gui", "fancy", "main", "gui")),
                        ("platlib", ("fancy/__init__.py", "platlib", 0)),
                        ("platlib", ("fancy/__main__.py", "platlib", 0)),
                        ("platlib", ("fancy-1.0.0.dist-info/METADATA", "platlib", 0)),
                        ("platlib", ("fancy-1.0.0.dist-info/WHEEL", "platlib", 0)),
                        (
                            "platlib",
                            ("fancy-1.0.0.dist-info/entry_points.txt", "platlib", 0),
                        ),
                        (
                            "platlib",
                            ("fancy-1.0.0.dist-info/top_level.txt", "platlib", 0),
                        ),
                        (
                            "platlib",
                            ("fancy-1.0.0.dist-info/fun_file.txt", "platlib", 0),
                        ),
                        (
                            "platlib",
                            RecordEntry("fancy-1.0.0.dist-info/RECORD", None, None),
                        ),
                    ],
                ),
            ]
        )

    def test_accepts_newer_minor_wheel_versions(self, mock_destination):
        # Create a fake wheel
        source = FakeWheelSource(
            distribution="fancy",
            version="1.0.0",
            regular_files={
                "fancy/__init__.py": b"""\
                    def main():
                        print("I'm a fancy package")
                """,
                "fancy/__main__.py": b"""\
                    if __name__ == "__main__":
                        from . import main
                        main()
                """,
            },
            dist_info_files={
                "top_level.txt": b"""\
                    fancy
                """,
                "entry_points.txt": b"""\
                    [console_scripts]
                    fancy = fancy:main

                    [gui_scripts]
                    fancy-gui = fancy:main
                """,
                "WHEEL": b"""\
                    Wheel-Version: 1.1
                    Generator: magic (1.0.0)
                    Root-Is-Purelib: true
                    Tag: py3-none-any
                """,
                "METADATA": b"""\
                    Metadata-Version: 2.1
                    Name: fancy
                    Version: 1.0.0
                    Summary: A fancy package
                    Author: Agendaless Consulting
                    Author-email: nobody@example.com
                    License: MIT
                    Keywords: fancy amazing
                    Platform: UNKNOWN
                    Classifier: Intended Audience :: Developers
                """,
            },
        )

        install(
            source=source,
            destination=mock_destination,
            additional_metadata={
                "fun_file.txt": b"this should be in dist-info!",
            },
        )

        # no assertions necessary, since we want to make sure this test didn't
        # raises errors.
        assert True

    def test_rejects_newer_major_wheel_versions(self, mock_destination):
        # Create a fake wheel
        source = FakeWheelSource(
            distribution="fancy",
            version="1.0.0",
            regular_files={
                "fancy/__init__.py": b"""\
                    def main():
                        print("I'm a fancy package")
                """,
                "fancy/__main__.py": b"""\
                    if __name__ == "__main__":
                        from . import main
                        main()
                """,
            },
            dist_info_files={
                "top_level.txt": b"""\
                    fancy
                """,
                "entry_points.txt": b"""\
                    [console_scripts]
                    fancy = fancy:main

                    [gui_scripts]
                    fancy-gui = fancy:main
                """,
                "WHEEL": b"""\
                    Wheel-Version: 2.0
                    Generator: magic (1.0.0)
                    Root-Is-Purelib: true
                    Tag: py3-none-any
                """,
                "METADATA": b"""\
                    Metadata-Version: 2.1
                    Name: fancy
                    Version: 1.0.0
                    Summary: A fancy package
                    Author: Agendaless Consulting
                    Author-email: nobody@example.com
                    License: MIT
                    Keywords: fancy amazing
                    Platform: UNKNOWN
                    Classifier: Intended Audience :: Developers
                """,
            },
        )

        with pytest.raises(InvalidWheelSource) as ctx:
            install(
                source=source,
                destination=mock_destination,
                additional_metadata={
                    "fun_file.txt": b"this should be in dist-info!",
                },
            )

        assert "Incompatible Wheel-Version" in str(ctx.value)

    def test_handles_data_properly(self, mock_destination):
        # Create a fake wheel
        source = FakeWheelSource(
            distribution="fancy",
            version="1.0.0",
            regular_files={
                "fancy/__init__.py": b"""\
                    # put me in purelib
                """,
                "fancy-1.0.0.data/purelib/fancy/purelib.py": b"""\
                    # put me in purelib
                """,
                "fancy-1.0.0.data/platlib/fancy/platlib.py": b"""\
                    # put me in platlib
                """,
                "fancy-1.0.0.data/scripts/fancy/scripts.py": b"""\
                    # put me in scripts
                """,
                "fancy-1.0.0.data/headers/fancy/headers.py": b"""\
                    # put me in headers
                """,
                "fancy-1.0.0.data/data/fancy/data.py": b"""\
                    # put me in data
                """,
            },
            dist_info_files={
                "top_level.txt": b"""\
                    fancy
                """,
                "entry_points.txt": b"""\
                    [console_scripts]
                    fancy = fancy:main

                    [gui_scripts]
                    fancy-gui = fancy:main
                """,
                "WHEEL": b"""\
                    Wheel-Version: 1.0
                    Generator: magic (1.0.0)
                    Root-Is-Purelib: true
                    Tag: py3-none-any
                """,
                "METADATA": b"""\
                    Metadata-Version: 2.1
                    Name: fancy
                    Version: 1.0.0
                    Summary: A fancy package
                    Author: Agendaless Consulting
                    Author-email: nobody@example.com
                    License: MIT
                    Keywords: fancy amazing
                    Platform: UNKNOWN
                    Classifier: Intended Audience :: Developers
                """,
            },
        )

        install(
            source=source,
            destination=mock_destination,
            additional_metadata={},
        )

        mock_destination.assert_has_calls(
            [
                mock.call.write_script(
                    name="fancy",
                    module="fancy",
                    attr="main",
                    section="console",
                ),
                mock.call.write_script(
                    name="fancy-gui",
                    module="fancy",
                    attr="main",
                    section="gui",
                ),
                mock.call.write_file(
                    scheme="data",
                    path="fancy/data.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="headers",
                    path="fancy/headers.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="platlib",
                    path="fancy/platlib.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy/purelib.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="scripts",
                    path="fancy/scripts.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy/__init__.py",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/METADATA",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/WHEEL",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/entry_points.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/top_level.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
                mock.call.finalize_installation(
                    scheme="purelib",
                    record_file_path="fancy-1.0.0.dist-info/RECORD",
                    records=[
                        ("scripts", ("fancy", "fancy", "main", "console")),
                        ("scripts", ("fancy-gui", "fancy", "main", "gui")),
                        ("data", ("fancy/data.py", "data", 0)),
                        ("headers", ("fancy/headers.py", "headers", 0)),
                        ("platlib", ("fancy/platlib.py", "platlib", 0)),
                        ("purelib", ("fancy/purelib.py", "purelib", 0)),
                        ("scripts", ("fancy/scripts.py", "scripts", 0)),
                        ("purelib", ("fancy/__init__.py", "purelib", 0)),
                        ("purelib", ("fancy-1.0.0.dist-info/METADATA", "purelib", 0)),
                        ("purelib", ("fancy-1.0.0.dist-info/WHEEL", "purelib", 0)),
                        (
                            "purelib",
                            ("fancy-1.0.0.dist-info/entry_points.txt", "purelib", 0),
                        ),
                        (
                            "purelib",
                            ("fancy-1.0.0.dist-info/top_level.txt", "purelib", 0),
                        ),
                        (
                            "purelib",
                            RecordEntry("fancy-1.0.0.dist-info/RECORD", None, None),
                        ),
                    ],
                ),
            ]
        )

    def test_errors_out_when_given_invalid_scheme_in_data(self, mock_destination):
        # Create a fake wheel
        source = FakeWheelSource(
            distribution="fancy",
            version="1.0.0",
            regular_files={
                "fancy/__init__.py": b"""\
                    # put me in purelib
                """,
                "fancy-1.0.0.data/purelib/fancy/purelib.py": b"""\
                    # put me in purelib
                """,
                "fancy-1.0.0.data/invalid/fancy/invalid.py": b"""\
                    # i am invalid
                """,
            },
            dist_info_files={
                "top_level.txt": b"""\
                    fancy
                """,
                "entry_points.txt": b"""\
                    [console_scripts]
                    fancy = fancy:main

                    [gui_scripts]
                    fancy-gui = fancy:main
                """,
                "WHEEL": b"""\
                    Wheel-Version: 1.0
                    Generator: magic (1.0.0)
                    Root-Is-Purelib: true
                    Tag: py3-none-any
                """,
                "METADATA": b"""\
                    Metadata-Version: 2.1
                    Name: fancy
                    Version: 1.0.0
                    Summary: A fancy package
                    Author: Agendaless Consulting
                    Author-email: nobody@example.com
                    License: MIT
                    Keywords: fancy amazing
                    Platform: UNKNOWN
                    Classifier: Intended Audience :: Developers
                """,
            },
        )

        with pytest.raises(InvalidWheelSource) as ctx:
            install(
                source=source,
                destination=mock_destination,
                additional_metadata={},
            )

        assert "fancy-1.0.0.data/invalid/fancy/invalid.py" in str(ctx.value)

    def test_ensure_non_executable_for_additional_metadata(self, mock_destination):
        # Create a fake wheel
        source = FakeWheelSource(
            distribution="fancy",
            version="1.0.0",
            regular_files={
                "fancy/__init__.py": b"""\
                    # put me in purelib
                """,
            },
            dist_info_files={
                "top_level.txt": b"""\
                    fancy
                """,
                "WHEEL": b"""\
                    Wheel-Version: 1.0
                    Generator: magic (1.0.0)
                    Root-Is-Purelib: true
                    Tag: py3-none-any
                """,
                "METADATA": b"""\
                    Metadata-Version: 2.1
                    Name: fancy
                    Version: 1.0.0
                    Summary: A fancy package
                    Author: Agendaless Consulting
                    Author-email: nobody@example.com
                    License: MIT
                    Keywords: fancy amazing
                    Platform: UNKNOWN
                    Classifier: Intended Audience :: Developers
                """,
            },
        )
        all_contents = list(source.get_contents())
        source.get_contents = lambda: (
            (*contents, True) for (*contents, _) in all_contents
        )
        install(
            source=source,
            destination=mock_destination,
            additional_metadata={
                "fun_file.txt": b"this should be in dist-info!",
            },
        )

        mock_destination.assert_has_calls(
            [
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy/__init__.py",
                    stream=mock.ANY,
                    is_executable=True,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/METADATA",
                    stream=mock.ANY,
                    is_executable=True,
                ),
                mock.call.write_file(
                    scheme="purelib",
                    path="fancy-1.0.0.dist-info/fun_file.txt",
                    stream=mock.ANY,
                    is_executable=False,
                ),
            ],
            any_order=True,
        )
