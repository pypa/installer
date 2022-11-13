import posixpath
import zipfile

import pytest

from installer.records import parse_record_file
from installer.sources import WheelFile, WheelSource, WheelValidationError


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

        with pytest.raises(NotImplementedError):
            source.validate_record()


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

    def modify_wheel_record(self, fancy_wheel, manipulation_func):
        """Helper function for modifying RECORD in the wheel file.

        Exists because ZipFile doesn't support remove.
        """
        files = {}
        # Read everything except RECORD and add it back immediately
        with zipfile.ZipFile(fancy_wheel) as archive:
            for file in archive.namelist():
                # Call manipulation function so that we can add RECORD back.
                if file.endswith("RECORD"):
                    manipulation_func(files, file, archive.read(file))
                    continue

                files[file] = archive.read(file)
        # Replace original archive
        with zipfile.ZipFile(fancy_wheel, mode="w") as archive:
            for name, content in files.items():
                archive.writestr(name, content)

    def test_validation_error_no_record(self, fancy_wheel):
        # Replace the wheel without adding RECORD
        self.modify_wheel_record(fancy_wheel, lambda *_: None)
        with WheelFile.open(fancy_wheel) as w:
            with pytest.raises(
                WheelValidationError, match="Unable to retrieve `RECORD`"
            ):
                w.validate_record()

    def test_validation_error_record_missing_file(self, fancy_wheel):
        def modifier(file_dict, file_name, data):
            # Throw away first two entries
            file_dict[file_name] = b"\n".join(data.split(b"\n")[2:])

        self.modify_wheel_record(fancy_wheel, modifier)
        with WheelFile.open(fancy_wheel) as w:
            with pytest.raises(WheelValidationError, match="not mentioned in RECORD"):
                w.validate_record()

    def test_validation_error_record_missing_hash(self, fancy_wheel):
        def modifier(file_dict, file_name, data):
            # Extract filename and write back without hash or size
            file_dict[file_name] = b"\n".join(
                line.split(b",")[0] + b",," for line in data.split(b"\n")[2:]
            )

        self.modify_wheel_record(fancy_wheel, modifier)
        with WheelFile.open(fancy_wheel) as w:
            with pytest.raises(
                WheelValidationError, match="hash of (.+) is not included in RECORD"
            ):
                w.validate_record()
