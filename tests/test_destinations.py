import io
import os.path

import pytest

from installer.destinations import SchemeDictionaryDestination, WheelDestination
from installer.records import RecordEntry
from installer.scripts import Script
from installer.utils import SCHEME_NAMES


class TestWheelDestination:
    def test_takes_no_arguments(self):
        WheelDestination()

    def test_raises_not_implemented_error(self):
        destination = WheelDestination()

        with pytest.raises(NotImplementedError):
            destination.write_script(name=None, module=None, attr=None, section=None)

        with pytest.raises(NotImplementedError):
            destination.write_file(
                scheme=None, path=None, stream=None, is_executable=False
            )

        with pytest.raises(NotImplementedError):
            destination.finalize_installation(
                scheme=None,
                record_file_path=None,
                records=None,
            )


class TestSchemeDictionaryDestination:
    @pytest.fixture()
    def destination(self, tmp_path):
        scheme_dict = {}
        for scheme in SCHEME_NAMES:
            full_path = tmp_path / scheme
            if not full_path.exists():
                full_path.mkdir()
            scheme_dict[scheme] = str(full_path)
        return SchemeDictionaryDestination(scheme_dict, "/my/python", "posix")

    @pytest.mark.parametrize(
        ("scheme", "path", "data", "expected"),
        [
            pytest.param(
                "data", "my_data.bin", b"my data", b"my data", id="normal file"
            ),
            pytest.param(
                "data",
                "data_folder/my_data.bin",
                b"my data",
                b"my data",
                id="normal file in subfolder",
            ),
            pytest.param(
                "scripts",
                "my_script.py",
                b"#!python\nmy script",
                b"#!/my/python\nmy script",
                id="script file",
            ),
            pytest.param(
                "scripts",
                "script_folder/my_script.py",
                b"#!python\nmy script",
                b"#!/my/python\nmy script",
                id="script file in subfolder",
            ),
        ],
    )
    def test_write_file(self, destination, scheme, path, data, expected):
        record = destination.write_file(scheme, path, io.BytesIO(data), False)
        file_path = os.path.join(destination.scheme_dict[scheme], path)
        with open(file_path, "rb") as f:
            file_data = f.read()

        assert file_data == expected
        assert record.path == path

    def test_write_record_duplicate(self, destination):
        destination.write_file("data", "my_data.bin", io.BytesIO(b"my data"), False)
        with pytest.raises(FileExistsError):
            destination.write_file("data", "my_data.bin", io.BytesIO(b"my data"), False)

    def test_write_script(self, destination):
        script_args = ("my_entrypoint", "my_module", "my_function", "console")
        record = destination.write_script(*script_args)
        file_path = os.path.join(destination.scheme_dict["scripts"], "my_entrypoint")

        assert os.path.isfile(file_path)

        with open(file_path, "rb") as f:
            file_data = f.read()
        name, expected_data = Script(*script_args).generate("/my/python", "posix")

        assert file_data == expected_data
        assert record.path == "my_entrypoint"

    def test_finalize_write_record(self, destination):
        records = [
            (
                "data",
                destination.write_file(
                    "data",
                    "my_data1.bin",
                    io.BytesIO(b"my data 1"),
                    is_executable=False,
                ),
            ),
            (
                "data",
                destination.write_file(
                    "data",
                    "my_data2.bin",
                    io.BytesIO(b"my data 2"),
                    is_executable=False,
                ),
            ),
            (
                "data",
                destination.write_file(
                    "data",
                    "my_data3.bin",
                    io.BytesIO(b"my data 3"),
                    is_executable=False,
                ),
            ),
            (
                "scripts",
                destination.write_file(
                    "scripts",
                    "my_script",
                    io.BytesIO(b"my script"),
                    is_executable=True,
                ),
            ),
            (
                "scripts",
                destination.write_file(
                    "scripts",
                    "my_script2",
                    io.BytesIO(b"#!python\nmy script"),
                    is_executable=False,
                ),
            ),
            (
                "scripts",
                destination.write_script(
                    "my_entrypoint", "my_module", "my_function", "console"
                ),
            ),
            ("purelib", RecordEntry("RECORD", None, None)),
        ]

        destination.finalize_installation("purelib", "RECORD", records)
        file_path = os.path.join(destination.scheme_dict["purelib"], "RECORD")

        with open(file_path, "rb") as f:
            data = f.read()

        assert data == (
            b"../data/my_data1.bin,sha256=355d00f8ce0e3eea93b078de0fa5ad87ff94aaba40000772a6572eb2d159f2ce,9\n"
            b"../data/my_data2.bin,sha256=94fed5f2858baa0c9709b74048d88f76c5288333d466186dffb17c4f96c2dde4,9\n"
            b"../data/my_data3.bin,sha256=d7c92baeebb582bd35c7e58cffd0a14804a81efd267d1015ebe0766ddf6cc69a,9\n"
            b"../scripts/my_script,sha256=33ad1f5af51230990fb70d9aa54be3596c0e72744f715cbfccee3ee25a47d3ca,9\n"
            b"../scripts/my_script2,sha256=93dffdf7b9136d36109bb11714b7255592f59b637df2b53dd105f8e9778cbe36,22\n"
            b"../scripts/my_entrypoint,sha256=fe9ffd9f099e21ea0c05f4346a486bd4a6ca9f795a0f2760d09edccb416ce892,216\n"
            b"RECORD,,\n"
        )
