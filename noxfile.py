"""Development automation
"""
import os

import nox

nox.options.sessions = ["lint", "test", "doctest"]
nox.options.reuse_existing_virtualenvs = True


@nox.session(python="3.12")
def lint(session):
    session.install("pre-commit")

    if session.posargs:
        args = session.posargs
    elif "CI" in os.environ:
        args = ["--show-diff-on-failure"]
    else:
        args = []

    session.run("pre-commit", "run", "--all-files", *args)


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12", "pypy3"])
def test(session):
    session.install(".")
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


@nox.session(python=["3.8", "3.9", "3.10", "3.11", "3.12", "pypy3"])
def doctest(session):
    session.install(".")
    session.install("-r", "docs/requirements.txt")

    session.run("sphinx-build", "-b", "doctest", "docs/", "build/doctest")


@nox.session(python="3.12", name="update-launchers")
def update_launchers(session):
    session.install("httpx")
    session.run("python", "tools/update_launchers.py")


#
# Documentation
#
@nox.session(python="3.12")
def docs(session):
    session.install(".")
    session.install("-r", "docs/requirements.txt")

    # Generate documentation into `build/docs`
    session.run("sphinx-build", "-W", "-b", "html", "docs/", "build/docs")


@nox.session(name="docs-live", python="3.12")
def docs_live(session):
    session.install("-e", ".")
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
