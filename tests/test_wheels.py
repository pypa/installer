import io
import textwrap

import pytest

from installer.wheels import SuperfulousRecordColumnsWarning, parse_record_file


def test_parse_wheel_record_simple():
    record_content = textwrap.dedent(
        """\
        file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144
        distribution-1.0.dist-info/RECORD,,
        """
    )
    records = list(parse_record_file(io.StringIO(record_content)))
    assert len(records) == 2

    r0 = records[0]
    assert r0.path.as_posix() == "file.py"
    assert r0.hash_.name == "sha256"
    assert r0.hash_.value == "AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI"
    assert r0.size == 3144

    r1 = records[1]
    assert r1.path.as_posix() == "distribution-1.0.dist-info/RECORD"
    assert r1.hash_ is None
    assert r1.size is None


def test_parse_wheel_record_drop_superfulous():
    record_content = textwrap.dedent(
        """\
        file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144,
        distribution-1.0.dist-info/RECORD,,
        """
    )
    record_io = io.StringIO(record_content)

    with pytest.warns(SuperfulousRecordColumnsWarning) as ws:
        records = list(parse_record_file(record_io))

    assert len(ws) == 1
    assert ws[0].message.args[0] == "Dropping columns [3:] from row 0"

    assert len(records) == 2

    r0 = records[0]
    assert r0.path.as_posix() == "file.py"
    assert r0.hash_.name == "sha256"
    assert r0.hash_.value == "AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI"
    assert r0.size == 3144

    r1 = records[1]
    assert r1.path.as_posix() == "distribution-1.0.dist-info/RECORD"
    assert r1.hash_ is None
    assert r1.size is None


RECORD_CONTENT_NOT_ENOUGH_COLUMNS = """\
file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144
distribution-1.0.dist-info/RECORD,
"""

RECORD_CONTENT_INVALID_SIZE = """\
file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144
distribution-1.0.dist-info/RECORD,,deadbeef
"""


@pytest.mark.parametrize(
    "record_content, invalid_row",
    [
        (
            RECORD_CONTENT_NOT_ENOUGH_COLUMNS,
            ["distribution-1.0.dist-info/RECORD", ""],
        ),
        (
            RECORD_CONTENT_INVALID_SIZE,
            ["distribution-1.0.dist-info/RECORD", "", "deadbeef"],
        ),
    ],
)
def test_parse_wheel_record_invalid(record_content, invalid_row):
    record_io = io.StringIO(record_content)
    with pytest.raises(ValueError) as ctx:
        list(parse_record_file(record_io))
    assert str(ctx.value) == f"invalid row 1: {invalid_row!r}"
