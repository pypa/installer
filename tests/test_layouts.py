import re

import pytest

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
    entries = [
        "pytest_xdist-2.8.1.dist-info",
        "pytest-2.8.1.dist-info",
        "pytest_cov",
        "{}-2.8.2.dist-info".format(re.sub(r"[-_\.]+", "_", name)),
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
