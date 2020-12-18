import pytest

from installer.sources import WheelSource


class TestWheelSource:
    def test_takes_two_arguments(self):
        WheelSource("distribution", "version")
        WheelSource(distribution="distribution", version="version")

    def test_correctly_computes_properties(self):
        source = WheelSource(distribution="distribution", version="version")

        assert source.data_dir == "distribution-version.data"
        assert source.dist_info_dir == "distribution-version.dist-info"

    def test_raises_not_implemented_error(self):
        source = WheelSource(distribution="distribution", version="version")

        with pytest.raises(NotImplementedError):
            source.dist_info_filenames

        with pytest.raises(NotImplementedError):
            source.read_dist_info("METADATA")

        with pytest.raises(NotImplementedError):
            source.get_contents()
