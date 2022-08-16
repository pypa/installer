import json
import posixpath
import zipfile
from base64 import urlsafe_b64encode
from hashlib import sha256

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

    def test_finds_dist_info(self, fancy_wheel):
        denorm = fancy_wheel.rename(fancy_wheel.parent / "Fancy-1.0.0-py3-none-any.whl")
        with WheelFile.open(denorm) as source:
            assert source.dist_info_filenames

    def test_requires_dist_info_name_match(self, fancy_wheel):
        misnamed = fancy_wheel.rename(
            fancy_wheel.parent / "misnamed-1.0.0-py3-none-any.whl"
        )
        with pytest.raises(AssertionError):
            with WheelFile.open(misnamed) as source:
                source.dist_info_filenames


def replace_file_in_zip(path: str, filename: str, content: "bytes | None") -> None:
    """Helper function for replacing a file in the zip.

    Exists because ZipFile doesn't support remove.
    """
    files = {}
    # Copy everything except `filename`, and replace it with `content`.
    with zipfile.ZipFile(path) as archive:
        for file in archive.namelist():
            if file == filename:
                if content is None:
                    continue  # Remove the file
                files[file] = content
            else:
                files[file] = archive.read(file)
    # Replace original archive
    with zipfile.ZipFile(path, mode="w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


def test_rejects_no_record_on_validate(fancy_wheel):
    # Remove RECORD
    replace_file_in_zip(
        fancy_wheel,
        filename="fancy-1.0.0.dist-info/RECORD",
        content=None,
    )
    with WheelFile.open(fancy_wheel) as source:
        with pytest.raises(
            WheelFile.validation_error, match="Unable to retrieve `RECORD`"
        ):
            source.validate_record()


def test_rejects_record_missing_file_on_validate(fancy_wheel):
    with zipfile.ZipFile(fancy_wheel) as archive:
        with archive.open("fancy-1.0.0.dist-info/RECORD") as f:
            record_file_contents = f.read()

    # Remove the first two entries from the RECORD file
    new_record_file_contents = b"\n".join(record_file_contents.split(b"\n")[2:])
    replace_file_in_zip(
        fancy_wheel,
        filename="fancy-1.0.0.dist-info/RECORD",
        content=new_record_file_contents,
    )
    with WheelFile.open(fancy_wheel) as source:
        with pytest.raises(WheelFile.validation_error, match="not mentioned in RECORD"):
            source.validate_record()


def test_rejects_record_missing_hash(fancy_wheel):
    with zipfile.ZipFile(fancy_wheel) as archive:
        with archive.open("fancy-1.0.0.dist-info/RECORD") as f:
            record_file_contents = f.read()

    new_record_file_contents = b"\n".join(
        line.split(b",")[0] + b",,"  # file name with empty size and hash
        for line in record_file_contents.split(b"\n")
    )
    replace_file_in_zip(
        fancy_wheel,
        filename="fancy-1.0.0.dist-info/RECORD",
        content=new_record_file_contents,
    )
    with WheelFile.open(fancy_wheel) as source:
        with pytest.raises(
            WheelFile.validation_error,
            match="hash / size of (.+) is not included in RECORD",
        ):
            source.validate_record()


def test_accept_record_missing_hash_on_skip_validation(fancy_wheel):
    with zipfile.ZipFile(fancy_wheel) as archive:
        with archive.open("fancy-1.0.0.dist-info/RECORD") as f:
            record_file_contents = f.read()

    new_record_file_contents = b"\n".join(
        line.split(b",")[0] + b",,"  # file name with empty size and hash
        for line in record_file_contents.split(b"\n")
    )
    replace_file_in_zip(
        fancy_wheel,
        filename="fancy-1.0.0.dist-info/RECORD",
        content=new_record_file_contents,
    )
    with WheelFile.open(fancy_wheel) as source:
        source.validate_record(validate_file=False)


def test_accept_wheel_with_signed_file(fancy_wheel):
    with zipfile.ZipFile(fancy_wheel) as archive:
        with archive.open("fancy-1.0.0.dist-info/RECORD") as f:
            record_file_contents = f.read()
            hash_b64_nopad = (
                urlsafe_b64encode(sha256(record_file_contents).digest())
                .decode("utf-8")
                .rstrip("=")
            )
            jws_content = json.dumps({"hash": f"sha256={hash_b64_nopad}"})
    with zipfile.ZipFile(fancy_wheel, "a") as archive:
        archive.writestr("fancy-1.0.0.dist-info/RECORD.jws", jws_content)
    with WheelFile.open(fancy_wheel) as source:
        source.validate_record()


def test_rejects_record_validation_failed(fancy_wheel):
    with zipfile.ZipFile(fancy_wheel) as archive:
        with archive.open("fancy-1.0.0.dist-info/RECORD") as f:
            record_file_contents = f.read()

    new_record_file_contents = b"\n".join(
        line.split(b",")[0]  # Original filename
        + b",sha256=pREiHcl39jRySUXMCOrwmSsnOay8FB7fOJP5mZQ3D3A,"
        + line.split(b",")[2]  # Original size
        for line in record_file_contents.split(b"\n")
        if line  # ignore trail endline
    )
    replace_file_in_zip(
        fancy_wheel,
        filename="fancy-1.0.0.dist-info/RECORD",
        content=new_record_file_contents,
    )
    with WheelFile.open(fancy_wheel) as source:
        with pytest.raises(
            WheelFile.validation_error,
            match="hash / size of (.+) didn't match RECORD",
        ):
            source.validate_record()
