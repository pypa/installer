import textwrap
import zipfile

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
        "fancy-1.0.0.dist-info/RECORD": b"""\
            fancy/__init__.py,sha256=qZ2qq7xVBAiUFQVv-QBHhdtCUF5p1NsWwSOiD7qdHN0,36
            fancy/__main__.py,sha256=Wd4SyWJOIMsHf_5-0oN6aNFwen8ehJnRo-erk2_K-eY,61
            fancy-1.0.0.data/data/fancy/data.py,sha256=nuFRUNQF5vP7FWE-v5ysyrrfpIaAvfzSiGOgfPpLOeI,17
            fancy-1.0.0.dist-info/top_level.txt,sha256=SW-yrrF_c8KlserorMw54inhLjZ3_YIuLz7fYT4f8ao,6
            fancy-1.0.0.dist-info/entry_points.txt,sha256=AxJl21_zgoNWjCfvSkC9u_rWSzGyCtCzhl84n979jCc,75
            fancy-1.0.0.dist-info/WHEEL,sha256=1DrXMF1THfnBjsdS5sZn-e7BKcmUn7jnMbShGeZomgc,84
            fancy-1.0.0.dist-info/METADATA,sha256=hRhZavK_Y6WqKurFFAABDnoVMjZFBH0NJRjwLOutnJI,236
            fancy-1.0.0.dist-info/RECORD,,
        """,
    }

    with zipfile.ZipFile(path, "w") as archive:
        for name, indented_content in files.items():
            archive.writestr(
                name,
                textwrap.dedent(indented_content.decode("utf-8")).encode("utf-8"),
            )

    return path
