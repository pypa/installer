import hashlib
import textwrap
from io import BytesIO

import mock

from installer import install
from installer.sources import WheelSource


def hash_and_size(data):
    return hashlib.sha256(data).digest(), len(data)


class FakeWheelSource(WheelSource):
    # NOTE: For Python 2 compatibility, this doesn't use keyword only arguments.
    #       Change that once the support is dropped.
    def __init__(self, distribution, version, regular_files, dist_info_files):
        super(FakeWheelSource, self).__init__(distribution, version)

        self.dist_info_files = {
            file: textwrap.dedent(content.decode("utf-8"))
            for file, content in dist_info_files.items()
        }
        self.regular_files = {
            file: textwrap.dedent(content.decode("utf-8")).encode("utf-8")
            for file, content in regular_files.items()
        }

        # Compute RECORD file.
        _records = [record for record, _ in self.get_contents()]
        self.dist_info_files["RECORD"] = "\n".join(
            sorted(
                ",".join([file, "sha256=" + hash_, str(size)])
                for file, hash_, size in _records
            )
        )

    @property
    def dist_info_filenames(self):
        return [
            file
            for file in self.regular_files
            if file.startswith(self.dist_info_dir + "/")
        ]

    def read_dist_info(self, filename):
        return self.dist_info_files[filename]

    def get_contents(self):
        for file, content in self.regular_files.items():
            hashed, size = hash_and_size(content)
            record = (file, "sha256={}".format(hashed), str(size))
            with BytesIO(content) as stream:
                yield record, stream

        for file, text in self.dist_info_files.items():
            content = text.encode()
            hashed, size = hash_and_size(content)
            record = (
                self.dist_info_dir + "/" + file,
                "sha256={}".format(hashed),
                str(size),
            )
            with BytesIO(content) as stream:
                yield record, stream


class TestInstall:
    def test_calls_destination_correctly(self):
        # Create a fake wheel
        source = FakeWheelSource(
            distribution="fancy",
            version="1.0.0",
            regular_files={
                "fancy/__init__.py": b"""\
                    def main():
                        print("I'm a fancy package")
                """,
                "fancy/__main__.py": b"""\
                    if __name__ == "__main__":
                        from . import main
                        main()
                """,
            },
            dist_info_files={
                "top_level.txt": b"""\
                    fancy
                """,
                "entry-points.txt": b"""\
                    [console_scripts]
                    fancy = fancy:main

                    [gui_scripts]
                    fancy-gui = fancy:main
                """,
                "WHEEL": b"""\
                    Wheel-Version: 1.0
                    Generator: magic (1.0.0)
                    Root-Is-Purelib: true
                    Tag: py3-none-any
                """,
                "METADATA": b"""\
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
            },
        )

        mock_destination = mock.Mock()
        # A hacky approach to making sure we got the right objects going in.
        mock_destination.write_file.side_effect = lambda scheme, path, stream: (path, scheme, 0)

        # Run the install
        install(
            source=source,
            destination=mock_destination,
            additional_metadata={
                "fun_file.txt": b"this should be in dist-info!",
            },
        )

        mock_destination.assert_has_calls([
            mock.call.write_script(name='fancy', module='fancy', attr='main', section='console'),
            mock.call.write_script(name='fancy-gui', module='fancy', attr='main', section='gui'),
            mock.call.write_file(scheme='purelib', path='fancy/__init__.py', stream=mock.ANY),
            mock.call.write_file(scheme='purelib', path='fancy/__main__.py', stream=mock.ANY),
            mock.call.write_file(scheme='purelib', path='fancy-1.0.0.dist-info/top_level.txt', stream=mock.ANY),
            mock.call.write_file(scheme='purelib', path='fancy-1.0.0.dist-info/entry-points.txt', stream=mock.ANY),
            mock.call.write_file(scheme='purelib', path='fancy-1.0.0.dist-info/WHEEL', stream=mock.ANY),
            mock.call.write_file(scheme='purelib', path='fancy-1.0.0.dist-info/METADATA', stream=mock.ANY),
            mock.call.write_file(scheme='purelib', path='fancy-1.0.0.dist-info/fun_file.txt', stream=mock.ANY),
            mock.call.finalize_installation(scheme='purelib', record_file_path='fancy-1.0.0.dist-info/RECORD', records=[
                ("fancy/__init__.py", "purelib", 0),
                ("fancy/__main__.py", "purelib", 0),
                ("fancy-1.0.0.dist-info/top_level.txt", "purelib", 0),
                ("fancy-1.0.0.dist-info/entry-points.txt", "purelib", 0),
                ("fancy-1.0.0.dist-info/WHEEL", "purelib", 0),
                ("fancy-1.0.0.dist-info/METADATA", "purelib", 0),
                ("fancy-1.0.0.dist-info/fun_file.txt", "purelib", 0),
            ]),
        ])
