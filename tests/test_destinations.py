import pytest

from installer.destinations import WheelDestination


class TestWheelDestination:
    def test_takes_no_arguments(self):
        WheelDestination()

    def test_raises_not_implemented_error(self):
        destination = WheelDestination()

        with pytest.raises(NotImplementedError):
            destination.write_script(name=None, module=None, attr=None, section=None)

        with pytest.raises(NotImplementedError):
            destination.write_file(scheme=None, path=None, stream=None)

        with pytest.raises(NotImplementedError):
            destination.finalize_installation(scheme=None, records=None)
