"""Errors raised from this package."""


class InstallerError(Exception):
    """All exceptions raised from this package's code."""


class InvalidWheelSource(InstallerError):  # noqa: N818
    """When a wheel source violates a contract, or is not supported."""
