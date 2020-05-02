import re

import pytest

from installer._compat import pathlib
from installer.exceptions import MetadataNotFound
from installer.layouts import DistInfo


@pytest.mark.parametrize(
    "name",
    [
        "pytest-cov",  # Normalized.
        "Pytest-Cov",  # Different casing.
        "Pytest_cov",  # Underscore.
        "pytest.Cov",  # Dot.
    ],
)
@pytest.mark.parametrize(
    "directory_name",
    [
        "pytest_cov-2.11.2.dist-info",
        "Pytest_Cov-2.11.2.dist-info",
        "Pytest_Cov-2 11 2.dist-info",
    ],
)
def test_find_distinfo(name, directory_name):
    escaped_name = re.sub(r"[-_\.]+", "_", name)
    entries = [
        "pytest_xdist-2.8.1.dist-info",
        "pytest-2.8.1.dist-info",
        "{}-2.8.1.egg-info".format(escaped_name),
        "{}-2.8.2.dist-info".format(escaped_name),
        "pytest_cov",
        directory_name,
    ]
    distinfo = DistInfo.find(name, "2.11.2", entries)
    assert distinfo.directory_name == directory_name


@pytest.mark.parametrize(
    "directory_name",
    [
        "pytest_cov-2.8.1.egg-info",  # Wrong extension.
        "pytest_cov.dist-info",  # No version.
        "pytest_coverage-2.8.1.dist-info",  # Wrong name.
        "pytest_cov-2.8.2.dist-info",  # Wrong version.
        "pytest-cov-2.8.1.dist-info",  # Wrong name format.
    ],
)
def test_find_distinfo_error(directory_name):
    entries = [
        "pytest_xdist-2.8.1.dist-info",
        "pytest-2.8.1.dist-info",
        "pytest_cov",
        directory_name,
    ]
    with pytest.raises(MetadataNotFound) as ctx:
        DistInfo.find("pytest-cov", "2.8.1", entries)
    assert str(ctx.value) == "pytest_cov-2.8.1.dist-info"


@pytest.mark.parametrize(
    "attr, value",
    [
        ("record", "pytest_cov-2.8.1.dist-info/RECORD"),
        ("installer", "pytest_cov-2.8.1.dist-info/INSTALLER"),
        ("direct_url_json", "pytest_cov-2.8.1.dist-info/direct_url.json"),
    ],
)
def test_distinfo_property(attr, value):
    distinfo = DistInfo("pytest_cov-2.8.1.dist-info")
    assert getattr(distinfo, attr) == pathlib.PurePosixPath(value)
