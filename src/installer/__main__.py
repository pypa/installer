"""Installer CLI."""

import argparse
import compileall
import distutils.dist
import pathlib
import platform
import sys
import sysconfig
import warnings
from email.message import Message
from typing import TYPE_CHECKING, Collection, Dict, Iterable, Optional, Sequence, Tuple

import installer
import installer.destinations
import installer.sources
import installer.utils
from installer.records import RecordEntry
from installer.utils import Scheme

if TYPE_CHECKING:
    from installer.scripts import LauncherKind


class InstallerCompatibilityError(Exception):
    """Error raised when the install target is not compatible with the environment."""


class _MainDestination(installer.destinations.SchemeDictionaryDestination):
    destdir: Optional[pathlib.Path]

    def __init__(
        self,
        scheme_dict: Dict[str, str],
        interpreter: str,
        script_kind: "LauncherKind",
        hash_algorithm: str = "sha256",
        optimization_levels: Collection[int] = (0, 1),
        destdir: Optional[str] = None,
    ) -> None:
        if destdir:
            self.destdir = pathlib.Path(destdir).absolute()
            self.destdir.mkdir(exist_ok=True, parents=True)
            scheme_dict = {
                name: self._destdir_path(value) for name, value in scheme_dict.items()
            }
        else:
            self.destdir = None
        super().__init__(scheme_dict, interpreter, script_kind, hash_algorithm)
        self.optimization_levels = optimization_levels

    def _destdir_path(self, file: str) -> str:
        assert self.destdir
        file_path = pathlib.Path(file)
        rel_path = file_path.relative_to(file_path.anchor)
        return str(self.destdir.joinpath(*rel_path.parts))

    def _compile_record(self, scheme: Scheme, record: RecordEntry) -> None:
        if scheme not in ("purelib", "platlib"):
            return
        for level in self.optimization_levels:
            target_path = pathlib.Path(self.scheme_dict[scheme], record.path)
            if sys.version_info < (3, 9):
                compileall.compile_file(target_path, optimize=level)
            else:
                compileall.compile_file(
                    target_path,
                    optimize=level,
                    stripdir=str(self.destdir),
                )

    def finalize_installation(
        self,
        scheme: Scheme,
        record_file_path: str,
        records: Iterable[Tuple[Scheme, RecordEntry]],
    ) -> None:
        record_list = list(records)
        super().finalize_installation(scheme, record_file_path, record_list)
        for scheme, record in record_list:
            self._compile_record(scheme, record)


def main_parser() -> argparse.ArgumentParser:
    """Construct the main parser."""
    parser = argparse.ArgumentParser()
    parser.add_argument("wheel", type=str, help="wheel file to install")
    parser.add_argument(
        "--destdir",
        "-d",
        metavar="/",
        type=str,
        default="/",
        help="destination directory (prefix to prepend to each file)",
    )
    parser.add_argument(
        "--optimize",
        "-o",
        nargs="*",
        metavar="level",
        type=int,
        default=(0, 1),
        help="generate bytecode for the specified optimization level(s) (default=0, 1)",
    )
    parser.add_argument(
        "--skip-dependency-check",
        "-s",
        action="store_true",
        help="don't check if the wheel dependencies are met",
    )
    return parser


def get_scheme_dict(distribution_name: str) -> Dict[str, str]:
    """Calculate the scheme disctionary for the current Python environment."""
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


def check_python_version(metadata: Message) -> None:
    """Check if the project support the current interpreter."""
    try:
        import packaging.specifiers
    except ImportError:
        warnings.warn(
            "'packaging' module not available, "
            "skipping python version compatibility check"
        )
        return

    requirement = metadata["Requires-Python"]
    if not requirement:
        return

    versions = requirement.split(",")
    for version in versions:
        specifier = packaging.specifiers.Specifier(version)
        if platform.python_version() not in specifier:
            raise InstallerCompatibilityError(
                "Incompatible python version, needed: {}".format(version)
            )


def check_dependencies(metadata: Message) -> None:
    """Check if the project dependencies are met."""
    try:
        import packaging  # noqa: F401

        import build
    except ModuleNotFoundError as e:
        warnings.warn(f"'{e.name}' module not available, skipping dependency check")
        return

    missing = {
        unmet
        for requirement in metadata.get_all("Requires-Dist") or []
        for unmet_list in build.check_dependency(requirement)
        for unmet in unmet_list
    }
    if missing:
        missing_list = ", ".join(missing)
        raise InstallerCompatibilityError(
            "Missing requirements: {}".format(missing_list)
        )


def main(cli_args: Sequence[str], program: Optional[str] = None) -> None:
    """Process arguments and perform the install."""
    parser = main_parser()
    if program:
        parser.prog = program
    args = parser.parse_args(cli_args)

    with installer.sources.WheelFile.open(args.wheel) as source:
        # compability checks
        metadata_contents = source.read_dist_info("METADATA")
        metadata = installer.utils.parse_metadata_file(metadata_contents)
        check_python_version(metadata)
        if not args.skip_dependency_check:
            check_dependencies(metadata)

        destination = _MainDestination(
            get_scheme_dict(source.distribution),
            sys.executable,
            installer.utils.get_launcher_kind(),
            optimization_levels=args.optimize,
            destdir=args.destdir,
        )
        installer.install(source, destination, {})


def entrypoint() -> None:
    """CLI entrypoint."""
    main(sys.argv[1:])


if __name__ == "__main__":
    main(sys.argv[1:], "python -m installer")
