"""Development automation
"""
import os

import nox

nox.options.sessions = ["lint", "test", "doctest"]
nox.options.reuse_existing_virtualenvs = True


def _install_this_project_with_flit(session, *, extras=None, editable=False):
    session.install("flit")
    args = []
    if extras:
        args.append("--extras")
        args.append(",".join(extras))
    if editable:
        args.append("--pth-file" if os.name == "nt" else "--symlink")

    session.run("flit", "install", "--deps=production", *args, silent=True)


@nox.session(python="3.11")
def lint(session):
    session.install("pre-commit")

    if session.posargs:
        args = session.posargs
    elif "CI" in os.environ:
        args = ["--show-diff-on-failure"]
    else:
        args = []

    session.run("pre-commit", "run", "--all-files", *args)


@nox.session(python=["3.7", "3.8", "3.9", "3.10", "3.11", "pypy3"])
def test(session):
    _install_this_project_with_flit(session, editable=True)
    session.install("-r", "tests/requirements.txt")

    htmlcov_output = os.path.join(session.virtualenv.location, "htmlcov")

    session.run(
        "pytest",
        "--cov=installer",
        "--cov-fail-under=100",
        "--cov-report=term-missing",
        f"--cov-report=html:{htmlcov_output}",
        "--cov-context=test",
        "-n",
        "auto",
        *session.posargs,
    )


@nox.session(python=["3.7", "3.8", "3.9", "3.10", "3.11", "pypy3"])
def doctest(session):
    session.install(".")
    session.install("-r", "docs/requirements.txt")

    session.run("sphinx-build", "-b", "doctest", "docs/", "build/doctest")


@nox.session(python="3.11", name="update-launchers")
def update_launchers(session):
    session.install("httpx")
    session.run("python", "tools/update_launchers.py")


#
# Documentation
#
@nox.session(python="3.11")
def docs(session):
    _install_this_project_with_flit(session)
    session.install("-r", "docs/requirements.txt")

    # Generate documentation into `build/docs`
    session.run("sphinx-build", "-W", "-b", "html", "docs/", "build/docs")


@nox.session(name="docs-live", python="3.11")
def docs_live(session):
    _install_this_project_with_flit(session, editable=True)
    session.install("-r", "docs/requirements.txt")
    session.install("sphinx-autobuild")

    # fmt: off
    session.run(
        "sphinx-autobuild", "docs/", "build/docs",
        # Rebuild all files when rebuilding
        "-a",
        # Trigger rebuilds on code changes (for autodoc)
        "--watch", "src/installer",
        # Use a not-common high-numbered port
        "--port", "8765",
    )
    # fmt: on
