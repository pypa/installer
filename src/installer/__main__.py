"""Installer CLI."""

import argparse
import os.path
import sys
import sysconfig
from typing import Dict, Optional, Sequence

import installer
from installer.destinations import SchemeDictionaryDestination
from installer.sources import WheelFile
from installer.utils import get_launcher_kind


def _get_main_parser() -> argparse.ArgumentParser:
    """Construct the main parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=str, help="wheel file to install")
    parser.add_argument(
        "--destdir",
        "-d",
        metavar="path",
        type=str,
        help="destination directory (prefix to prepend to each file)",
    )
    parser.add_argument(
        "--compile-bytecode",
        action="append",
        metavar="level",
        type=int,
        choices=[0, 1, 2],
        help="generate bytecode for the specified optimization level(s) (default=0, 1)",
    )
    parser.add_argument(
        "--no-compile-bytecode",
        action="store_true",
        help="don't generate bytecode for installed modules",
    )
    return parser


def _get_scheme_dict(distribution_name: str) -> Dict[str, str]:
    """Calculate the scheme dictionary for the current Python environment."""
    scheme_dict = sysconfig.get_paths()

    installed_base = sysconfig.get_config_var("base")
    assert installed_base

    # calculate 'headers' path, not currently in sysconfig - see
    # https://bugs.python.org/issue44445. This is based on what distutils does.
    # TODO: figure out original vs normalised distribution names
    scheme_dict["headers"] = os.path.join(
        sysconfig.get_path("include", vars={"installed_base": installed_base}),
        distribution_name,
    )

    return scheme_dict


def _main(cli_args: Sequence[str], program: Optional[str] = None) -> None:
    """Process arguments and perform the install."""
    parser = _get_main_parser()
    if program:
        parser.prog = program
    args = parser.parse_args(cli_args)

    bytecode_levels = args.compile_bytecode
    if args.no_compile_bytecode:
        bytecode_levels = []
    elif not bytecode_levels:
        bytecode_levels = [0, 1]

    with WheelFile.open(args.wheel) as source:
        destination = SchemeDictionaryDestination(
            scheme_dict=_get_scheme_dict(source.distribution),
            interpreter=sys.executable,
            script_kind=get_launcher_kind(),
            bytecode_optimization_levels=bytecode_levels,
            destdir=args.destdir,
        )
        installer.install(source, destination, {})


if __name__ == "__main__":  # pragma: no cover
    _main(sys.argv[1:], "python -m installer")
