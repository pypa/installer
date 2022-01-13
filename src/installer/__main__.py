"""Installer CLI."""

import argparse
import distutils.dist
import sys
import sysconfig
from typing import Dict, Optional, Sequence

import installer
import installer.destinations
import installer.sources
import installer.utils


def main_parser() -> argparse.ArgumentParser:
    """Construct the main parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=str, help="wheel file to install")
    parser.add_argument(
        "--destdir",
        "-d",
        metavar="/",
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


def get_scheme_dict(distribution_name: str) -> Dict[str, str]:
    """Calculate the scheme dictionary for the current Python environment."""
    scheme_dict = sysconfig.get_paths()

    # calculate 'headers' path, sysconfig does not have an equivalent
    # see https://bugs.python.org/issue44445
    dist_dict = {
        "name": distribution_name,
    }
    distribution = distutils.dist.Distribution(dist_dict)
    install_cmd = distribution.get_command_obj("install")
    assert install_cmd
    install_cmd.finalize_options()
    # install_cmd.install_headers is not type hinted
    scheme_dict["headers"] = install_cmd.install_headers  # type: ignore

    return scheme_dict


def main(cli_args: Sequence[str], program: Optional[str] = None) -> None:
    """Process arguments and perform the install."""
    parser = main_parser()
    if program:
        parser.prog = program
    args = parser.parse_args(cli_args)

    bytecode_levels = args.compile_bytecode
    if args.no_compile_bytecode:
        bytecode_levels = []
    elif not bytecode_levels:
        bytecode_levels = [0, 1]

    with installer.sources.WheelFile.open(args.wheel) as source:
        destination = installer.destinations.SchemeDictionaryDestination(
            get_scheme_dict(source.distribution),
            sys.executable,
            installer.utils.get_launcher_kind(),
            bytecode_optimization_levels=bytecode_levels,
            destdir=args.destdir,
        )
        installer.install(source, destination, {})


if __name__ == "__main__":  # pragma: no cover
    main(sys.argv[1:], "python -m installer")
