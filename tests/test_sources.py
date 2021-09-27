import posixpath
import sys
import textwrap
import zipfile

import pytest

from installer.records import parse_record_file
from installer.sources import WheelFile, WheelSource


@pytest.fixture
def fancy_wheel(tmp_path):
    path = tmp_path / "fancy-1.0.0-py2.py3-none-any.whl"
    files = {
        "fancy/": b"""""",
        "fancy/__init__.py": b"""\
            def main():
                print("I'm fancy.")
        """,
        "fancy/__main__.py": b"""\
            if __name__ == "__main__":
                from . import main
                main()
        """,
        "fancy-1.0.0.data/data/fancy/": b"""""",
        "fancy-1.0.0.data/data/fancy/data.py": b"""\
            # put me in data
        """,
        "fancy-1.0.0.dist-info/": b"""""",
        "fancy-1.0.0.dist-info/top_level.txt": b"""\
            fancy
        """,
        "fancy-1.0.0.dist-info/entry-points.txt": b"""\
            [console_scripts]
            fancy = fancy:main

            [gui_scripts]
            fancy-gui = fancy:main
        """,
        "fancy-1.0.0.dist-info/WHEEL": b"""\
            Wheel-Version: 1.0
            Generator: magic (1.0.0)
            Root-Is-Purelib: true
            Tag: py3-none-any
        """,
        "fancy-1.0.0.dist-info/METADATA": b"""\
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
        # The RECORD file is indirectly validated by the WheelFile, since it only
        # provides the items that are a part of the wheel.
        "fancy-1.0.0.dist-info/RECORD": b"""\
            fancy/__init__.py,,
            fancy/__main__.py,,
            fancy-1.0.0.data/data/fancy/data.py,,
            fancy-1.0.0.dist-info/top_level.txt,,
            fancy-1.0.0.dist-info/entry-points.txt,,
            fancy-1.0.0.dist-info/WHEEL,,
            fancy-1.0.0.dist-info/METADATA,,
            fancy-1.0.0.dist-info/RECORD,,
        """,
    }

    if sys.version_info <= (3, 6):
        path = str(path)

    with zipfile.ZipFile(path, "w") as archive:
        for name, indented_content in files.items():
            archive.writestr(
                name,
                textwrap.dedent(indented_content.decode("utf-8")).encode("utf-8"),
            )

    return path


class TestWheelSource:
    def test_takes_two_arguments(self):
        WheelSource("distribution", "version")
        WheelSource(distribution="distribution", version="version")

    def test_correctly_computes_properties(self):
        source = WheelSource(distribution="distribution", version="version")

        assert source.data_dir == "distribution-version.data"
        assert source.dist_info_dir == "distribution-version.dist-info"

    def test_raises_not_implemented_error(self):
        source = WheelSource(distribution="distribution", version="version")

        with pytest.raises(NotImplementedError):
            source.dist_info_filenames

        with pytest.raises(NotImplementedError):
            source.read_dist_info("METADATA")

        with pytest.raises(NotImplementedError):
            source.get_contents()


class TestWheelFile:
    def test_rejects_not_okay_name(self, tmp_path):
        # Create an empty zipfile
        path = tmp_path / "not_a_valid_name.whl"
        with zipfile.ZipFile(str(path), "w"):
            pass

        with pytest.raises(ValueError, match="Not a valid wheel filename: .+"):
            with WheelFile.open(str(path)):
                pass

    def test_provides_correct_dist_info_filenames(self, fancy_wheel):
        with WheelFile.open(fancy_wheel) as source:
            assert sorted(source.dist_info_filenames) == [
                "METADATA",
                "RECORD",
                "WHEEL",
                "entry-points.txt",
                "top_level.txt",
            ]

    def test_correctly_reads_from_dist_info_files(self, fancy_wheel):
        files = {}
        with zipfile.ZipFile(fancy_wheel) as archive:
            for file in archive.namelist():
                if ".dist-info" not in file:
                    continue
                files[posixpath.basename(file)] = archive.read(file).decode("utf-8")

        got_files = {}
        with WheelFile.open(fancy_wheel) as source:
            for file in files:
                got_files[file] = source.read_dist_info(file)

        assert got_files == files

    def test_provides_correct_contents(self, fancy_wheel):
        # Know the contents of the wheel
        files = {}
        with zipfile.ZipFile(fancy_wheel) as archive:
            for file in archive.namelist():
                if file[-1] == "/":
                    continue
                files[file] = archive.read(file)

        expected_record_lines = (
            files["fancy-1.0.0.dist-info/RECORD"].decode("utf-8").splitlines()
        )
        expected_records = list(parse_record_file(expected_record_lines))

        # Check that the object's output is appropriate
        got_records = []
        got_files = {}
        with WheelFile.open(fancy_wheel) as source:
            for record_elements, stream in source.get_contents():
                got_records.append(record_elements)
                got_files[record_elements[0]] = stream.read()

        assert sorted(got_records) == sorted(expected_records)
        assert got_files == files
