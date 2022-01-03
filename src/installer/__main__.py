import argparse

from . import install
from .destinations import SchemeDictionaryDestination
from .sources import WheelFile

def main():
    ap = argparse.ArgumentParser("python -m installer")
    ap.add_argument("wheel_file", help="Path to a .whl file to install")

    ap.add_argument(
        "--interpreter", required=True,
        help="Interpreter path to be used in scripts"
    )
    ap.add_argument(
        "--script-kind", required=True, choices=[
            "posix", "win-ia32", "win-amd64", "win-arm", "win-arm64"
        ], help="Kind of launcher to create for each script"
    )

    dest_args = ap.add_argument_group("Destination directories")
    dest_args.add_argument(
        '--purelib', required=True,
        help="Directory for platform-independent Python modules"
    )
    dest_args.add_argument(
        '--platlib', required=True,
        help="Directory for platform-dependent Python modules"
    )
    dest_args.add_argument(
        '--headers', required=True, help="Directory for C header files"
    )
    dest_args.add_argument(
        '--scripts',  required=True, help="Directory for executable scripts"
    )
    dest_args.add_argument(
        '--data', required=True, help="Directory for external data files"
    )
    args = ap.parse_args()

    destination = SchemeDictionaryDestination({
            'purelib': args.purelib,
            'platlib': args.platlib,
            'headers': args.headers,
            'scripts': args.scripts,
            'data': args.data,
        },
        interpreter=args.interpreter,
        script_kind=args.script_kind,
    )

    with WheelFile.open(args.wheel_file) as source:
        install(
            source=source,
            destination=destination,
            additional_metadata={},
        )

if __name__ == '__main__':
    main()
