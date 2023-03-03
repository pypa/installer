import json
import posixpath
import zipfile
from base64 import urlsafe_b64encode
from hashlib import sha256

import pytest

from installer.exceptions import InstallerError
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


def replace_file_in_zip(path: str, filename: str, content: "str | None") -> None:
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
                files[file] = content.encode()
            else:
                files[file] = archive.read(file)
    # Replace original archive
    with zipfile.ZipFile(path, mode="w") as archive:
        for name, content in files.items():
            archive.writestr(name, content)


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
        with pytest.raises(InstallerError) as ctx:
            with WheelFile.open(misnamed) as source:
                source.dist_info_filenames

        error = ctx.value
        print(error)
        assert error.filename == str(misnamed)
        assert error.dist_info == "fancy-1.0.0.dist-info"
        assert "" in error.reason
        assert error.dist_info in str(error)

    def test_enforces_single_dist_info(self, fancy_wheel):
        with zipfile.ZipFile(fancy_wheel, "a") as archive:
            archive.writestr(
                "name-1.0.0.dist-info/random.txt",
                b"This is a random file.",
            )

        with pytest.raises(InstallerError) as ctx:
            with WheelFile.open(fancy_wheel) as source:
                source.dist_info_filenames

        error = ctx.value
        print(error)
        assert error.filename == str(fancy_wheel)
        assert error.dist_info == str(["fancy-1.0.0.dist-info", "name-1.0.0.dist-info"])
        assert "exactly one .dist-info" in error.reason
        assert error.dist_info in str(error)

    def test_rejects_no_record_on_validate(self, fancy_wheel):
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
                source.validate_record(validate_contents=False)

    def test_rejects_invalid_record_entry(self, fancy_wheel):
        with WheelFile.open(fancy_wheel) as source:
            record_file_contents = source.read_dist_info("RECORD")

        replace_file_in_zip(
            fancy_wheel,
            filename="fancy-1.0.0.dist-info/RECORD",
            content="\n".join(
                line.replace("sha256=", "") for line in record_file_contents
            ),
        )
        with WheelFile.open(fancy_wheel) as source:
            with pytest.raises(
                WheelFile.validation_error,
                match="Unable to retrieve `RECORD`",
            ):
                source.validate_record()

    def test_rejects_record_missing_file_on_validate(self, fancy_wheel):
        with WheelFile.open(fancy_wheel) as source:
            record_file_contents = source.read_dist_info("RECORD")

        # Remove the first two entries from the RECORD file
        new_record_file_contents = "\n".join(record_file_contents.split("\n")[2:])
        replace_file_in_zip(
            fancy_wheel,
            filename="fancy-1.0.0.dist-info/RECORD",
            content=new_record_file_contents,
        )
        with WheelFile.open(fancy_wheel) as source:
            with pytest.raises(
                WheelFile.validation_error, match="not mentioned in RECORD"
            ):
                source.validate_record(validate_contents=False)

    def test_rejects_record_missing_hash(self, fancy_wheel):
        with WheelFile.open(fancy_wheel) as source:
            record_file_contents = source.read_dist_info("RECORD")

        new_record_file_contents = "\n".join(
            line.split(",")[0] + ",,"  # file name with empty size and hash
            for line in record_file_contents.split("\n")
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
                source.validate_record(validate_contents=False)

    def test_accept_wheel_with_signature_file(self, fancy_wheel):
        with WheelFile.open(fancy_wheel) as source:
            record_file_contents = source.read_dist_info("RECORD")
        hash_b64_nopad = (
            urlsafe_b64encode(sha256(record_file_contents.encode()).digest())
            .decode("utf-8")
            .rstrip("=")
        )
        jws_content = json.dumps({"hash": f"sha256={hash_b64_nopad}"})
        with zipfile.ZipFile(fancy_wheel, "a") as archive:
            archive.writestr("fancy-1.0.0.dist-info/RECORD.jws", jws_content)
        with WheelFile.open(fancy_wheel) as source:
            source.validate_record()

    def test_reject_signature_file_in_record(self, fancy_wheel):
        with WheelFile.open(fancy_wheel) as source:
            record_file_contents = source.read_dist_info("RECORD")
        record_hash_nopad = (
            urlsafe_b64encode(sha256(record_file_contents.encode()).digest())
            .decode("utf-8")
            .rstrip("=")
        )
        jws_content = json.dumps({"hash": f"sha256={record_hash_nopad}"})
        with zipfile.ZipFile(fancy_wheel, "a") as archive:
            archive.writestr("fancy-1.0.0.dist-info/RECORD.jws", jws_content)

        # Add signature file to RECORD
        jws_content = jws_content.encode()
        jws_hash_nopad = (
            urlsafe_b64encode(sha256(jws_content).digest()).decode("utf-8").rstrip("=")
        )
        replace_file_in_zip(
            fancy_wheel,
            filename="fancy-1.0.0.dist-info/RECORD",
            content=record_file_contents.rstrip("\n")
            + f"\nfancy-1.0.0.dist-info/RECORD.jws,sha256={jws_hash_nopad},{len(jws_content)}\n",
        )
        with WheelFile.open(fancy_wheel) as source:
            with pytest.raises(
                WheelFile.validation_error,
                match="digital signature file (.+) is incorrectly contained in RECORD.",
            ):
                source.validate_record(validate_contents=False)

    def test_rejects_record_contain_self_hash(self, fancy_wheel):
        with WheelFile.open(fancy_wheel) as source:
            record_file_contents = source.read_dist_info("RECORD")

        new_record_file_lines = []
        for line in record_file_contents.split("\n"):
            if not line:
                continue
            filename, hash_, size = line.split(",")
            if filename.split("/")[-1] == "RECORD":
                hash_ = "sha256=pREiHcl39jRySUXMCOrwmSsnOay8FB7fOJP5mZQ3D3A"
                size = str(len(record_file_contents))
            new_record_file_lines.append(",".join((filename, hash_, size)))

        replace_file_in_zip(
            fancy_wheel,
            filename="fancy-1.0.0.dist-info/RECORD",
            content="\n".join(new_record_file_lines),
        )
        with WheelFile.open(fancy_wheel) as source:
            with pytest.raises(
                WheelFile.validation_error,
                match="RECORD file incorrectly contains hash / size.",
            ):
                source.validate_record(validate_contents=False)

    def test_rejects_record_validation_failed(self, fancy_wheel):
        with WheelFile.open(fancy_wheel) as source:
            record_file_contents = source.read_dist_info("RECORD")

        new_record_file_lines = []
        for line in record_file_contents.split("\n"):
            if not line:
                continue
            filename, hash_, size = line.split(",")
            if filename.split("/")[-1] != "RECORD":
                hash_ = "sha256=pREiHcl39jRySUXMCOrwmSsnOay8FB7fOJP5mZQ3D3A"
            new_record_file_lines.append(",".join((filename, hash_, size)))

        replace_file_in_zip(
            fancy_wheel,
            filename="fancy-1.0.0.dist-info/RECORD",
            content="\n".join(new_record_file_lines),
        )
        with WheelFile.open(fancy_wheel) as source:
            with pytest.raises(
                WheelFile.validation_error,
                match="hash / size of (.+) didn't match RECORD",
            ):
                source.validate_record()
