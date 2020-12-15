import io
import shutil

import pytest

from installer.iohandler import IOHandler
from installer.records import Hash, Record


class TestWriter:
    def test_simple_copy(self, tmp_path):
        """Test a simple operation with defaults and validate the returned record and
        whether the file got correctly copied."""
        writer = IOHandler({"purelib": str(tmp_path)})

        contents = b"'hello world"
        file_name = "foo/__init__.py"
        record = writer.copy_file("purelib", file_name, io.BytesIO(contents))
        expected = Record(
            path=file_name,
            hash_=Hash(
                name="sha256",
                value="f4dd7a70487757553a54b8176ab03265d1035f000411eddfa7c9001b3eca99c6",
            ),
            size=len(contents),
        )
        assert record == expected
        assert (tmp_path / file_name).exists()

    def test_unknown_scheme(self):
        writer = IOHandler({})

        with pytest.raises(ValueError):
            writer.copy_file("purelib", "foo/__init__.py", io.BytesIO(b""))

    def test_override_hash_algo(self, tmp_path):
        """Check that overriding the hashing function generates the correct hash."""
        writer = IOHandler({"purelib": str(tmp_path)}, hash_algorithm="sha1")

        contents = b"'hello world"
        file_name = "foo/__init__.py"
        record = writer.copy_file("purelib", file_name, io.BytesIO(contents))
        expected = Record(
            path=file_name,
            hash_=Hash(name="sha256", value="02e9f641dc760be300f25a2ed00678057d238760"),
            size=len(contents),
        )
        assert record == expected
        assert (tmp_path / file_name).exists()

    def test_override_copy_handler(self, tmp_path):
        """Pass a different copy handler which uses shutil to copy the file and returns
        dummy data for the hash and file size."""

        def my_copy_handler(source, dest, hash_algorithm):
            assert hash_algorithm == "sha256"
            shutil.copyfileobj(source, dest)
            return 100, Hash(name="foo", value="8")

        writer = IOHandler({"purelib": str(tmp_path)}, copy_handler=my_copy_handler)

        file_name = "foo/__init__.py"
        record = writer.copy_file("purelib", file_name, io.BytesIO(b"'hello world"))
        expected = Record(path=file_name, hash_=Hash(name="foo", value="8"), size=100)
        assert record == expected
        assert (tmp_path / file_name).exists()
