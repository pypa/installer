import io
from pathlib import Path

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

    @pytest.fixture()
    def destination_overwrite_existing(self, tmp_path):
        scheme_dict = {}
        for scheme in SCHEME_NAMES:
            full_path = tmp_path / scheme
            if not full_path.exists():
                full_path.mkdir()
            scheme_dict[scheme] = str(full_path)
        return SchemeDictionaryDestination(
            scheme_dict, "/my/python", "posix", overwrite_existing=True
        )

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
        file_data = (Path(destination.scheme_dict[scheme]) / path).read_bytes()
        assert file_data == expected
        assert record.path == path

    def test_write_record_duplicate(self, destination):
        destination.write_file("data", "my_data.bin", io.BytesIO(b"my data"), False)
        with pytest.raises(FileExistsError):
            destination.write_file("data", "my_data.bin", io.BytesIO(b"my data"), False)

    def test_write_record_duplicate_with_overwrite_existing(
        self, destination_overwrite_existing
    ):
        destination_overwrite_existing.write_file(
            "data", "my_data.bin", io.BytesIO(b"my data"), False
        )
        destination_overwrite_existing.write_file(
            "data", "my_data.bin", io.BytesIO(b"my data"), False
        )

    def test_write_script(self, destination):
        script_args = ("my_entrypoint", "my_module", "my_function", "console")
        record = destination.write_script(*script_args)
        file_path = Path(destination.scheme_dict["scripts"]) / "my_entrypoint"

        assert file_path.is_file()

        file_data = file_path.read_bytes()
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
                    "my_data3,my_data4.bin",
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
        file_path = Path(destination.scheme_dict["purelib"]) / "RECORD"

        expected_data = (
            b"RECORD,,\n"
            b"data/my_data1.bin,sha256=NV0A-M4OPuqTsHjeD6Wth_-UqrpAAAdyplcustFZ8s4,9\n"
            b"data/my_data2.bin,sha256=lP7V8oWLqgyXCbdASNiPdsUogzPUZhht_7F8T5bC3eQ,9\n"
            b'data/my_data3,my_data4.bin",sha256=18krruu1gr01x-WM_9ChSASoHv0mfRAV6-B2bd9sxpo,9\n'
            b"scripts/my_entrypoint,sha256=_p_9nwmeIeoMBfQ0akhr1KbKn3laDydg0J7cy0Fs6JI,216\n"
            b"scripts/my_script,sha256=M60fWvUSMJkPtw2apUvjWWwOcnRPcVy_zO4-4lpH08o,9\n"
            b"scripts/my_script2,sha256=k9_997kTbTYQm7EXFLclVZL1m2N98rU90QX46XeMvjY,22\n"
        )
        assert all(
            real.endswith(expected)
            for real, expected in zip(data.split(b"\n"), expected_data.split(b"\n"))
        )
