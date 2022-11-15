import textwrap
import zipfile
from base64 import urlsafe_b64encode
from hashlib import sha256

import pytest


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
        "fancy-1.0.0.dist-info/entry_points.txt": b"""\
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
    }

    record_name = "fancy-1.0.0.dist-info/RECORD"
    record_lines = []

    with zipfile.ZipFile(path, "w") as archive:
        for name, indented_content in files.items():
            data = textwrap.dedent(indented_content.decode("utf-8")).encode("utf-8")
            archive.writestr(name, data)
            if name[-1:] != "/":  # Only files go into RECORD
                digest = sha256(data).digest()
                value = urlsafe_b64encode(digest).decode("ascii").rstrip("=")
                record_lines.append(f"{name},sha256={value},{len(data)}")

        record_lines.append(f"{record_name},,")
        archive.writestr(record_name, "\n".join(record_lines).encode("utf-8"))

    return path
