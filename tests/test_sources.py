import posixpath
import zipfile

import pytest

from installer.records import parse_record_file
from installer.sources import WheelFile, WheelSource


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
                "entry_points.txt",
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
                if file[-1:] == "/":
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
            for record_elements, stream, is_executable in source.get_contents():
                got_records.append(record_elements)
                got_files[record_elements[0]] = stream.read()
                assert not is_executable

        assert sorted(got_records) == sorted(expected_records)
        assert got_files == files

    def test_finds_dist_info(self, fancy_wheel):
        denorm = fancy_wheel.rename(fancy_wheel.parent / "Fancy-1.0.0-py3-none-any.whl")
        # Python 3.7: rename doesn't return the new name:
        denorm = fancy_wheel.parent / "Fancy-1.0.0-py3-none-any.whl"
        with WheelFile.open(denorm) as source:
            assert source.dist_info_filenames

    def test_requires_dist_info_name_match(self, fancy_wheel):
        misnamed = fancy_wheel.rename(
            fancy_wheel.parent / "misnamed-1.0.0-py3-none-any.whl"
        )
        # Python 3.7: rename doesn't return the new name:
        misnamed = fancy_wheel.parent / "misnamed-1.0.0-py3-none-any.whl"
        with pytest.raises(AssertionError):
            with WheelFile.open(misnamed) as source:
                source.dist_info_filenames
