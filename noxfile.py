"""Development automation
"""
import os

import nox

nox.options.sessions = ["lint", "test"]
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


@nox.session(python="3.8")
def lint(session):
    session.install("pre-commit")

    if session.posargs:
        args = session.posargs
    elif "CI" in os.environ:
        args = ["--show-diff-on-failure"]
    else:
        args = []

    session.run("pre-commit", "run", "--all-files", *args)


@nox.session(python=["2.7", "3.5", "3.6", "3.7", "3.8", "pypy2", "pypy3"])
def test(session):
    session.install(".[test]")

    htmlcov_output = os.path.join(session.virtualenv.location, "htmlcov")

    session.run(
        "pytest",
        "--cov=installer",
        "--cov-fail-under=100",
        "--cov-report=term-missing",
        "--cov-report=html:{}".format(htmlcov_output),
        "--cov-context=test",
        "-n",
        "auto",
        *session.posargs
    )


@nox.session(python="3.8")
def update_launchers(session):
    session.install("httpx")
    session.run("python", "tools/update_launchers.py")


#
# Documentation
#
@nox.session(python="3.8")
def docs(session):
    _install_this_project_with_flit(session, extras=["doc"])

    # Generate documentation into `build/docs`
    session.run("sphinx-build", "-W", "-b", "html", "docs/", "build/docs")


@nox.session(name="docs-live", python="3.8")
def docs_live(session):
    _install_this_project_with_flit(session, extras=["doc"], editable=True)
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
