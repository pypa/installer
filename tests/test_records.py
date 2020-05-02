import io

import pytest
import six

from installer._compat import pathlib
from installer.exceptions import (
    RecordItemError,
    RecordItemHashMismatch,
    RecordItemSizeMismatch,
)
from installer.records import (
    Hash,
    RecordItem,
    SuperfulousRecordColumnsWarning,
    parse_record_file,
    write_record_file,
)


def _get_csv_io():
    if six.PY2:
        return io.BytesIO()
    return io.StringIO(newline="")


@pytest.fixture(scope="session")
def record_simple():
    return [
        "file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
        "distribution-1.0.dist-info/RECORD,,",
    ]


@pytest.fixture()
def record_simple_iter(record_simple):
    return iter(record_simple)


@pytest.fixture()
def record_simple_file(tmpdir, record_simple):
    p = tmpdir.join("RECORD")
    p.write("\n".join(record_simple))
    with open(str(p)) as f:
        yield f


@pytest.fixture()
def record_input(request):
    return request.getfixturevalue(request.param)


@pytest.mark.parametrize(
    "record_input",
    ["record_simple", "record_simple_iter", "record_simple_file"],
    indirect=True,
)
def test_parse_wheel_record_simple(record_input):
    """Parser accepts any iterable, e.g. container, iterator, or file object.
    """
    records = list(parse_record_file(record_input))
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
    """Parser emits warning on each row with superfulous columns.
    """
    record_lines = [
        "file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144,",
        "distribution-1.0.dist-info/RECORD,,,,",
    ]

    with pytest.warns(SuperfulousRecordColumnsWarning) as ws:
        records = list(parse_record_file(record_lines))

    assert len(ws) == 2
    assert "0" in ws[0].message.args[0]
    assert "1" in ws[1].message.args[0]

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


RECORD_LINES_INVALID_NOT_ENOUGH_COLUMNS = [
    "file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
    "distribution-1.0.dist-info/RECORD,",
]

RECORD_LINES_INVALID_SIZE_VALUE = [
    "file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
    "distribution-1.0.dist-info/RECORD,,deadbeef",
]


@pytest.mark.parametrize(
    "record_lines, invalid_row",
    [
        (
            RECORD_LINES_INVALID_NOT_ENOUGH_COLUMNS,
            ["distribution-1.0.dist-info/RECORD", ""],
        ),
        (
            RECORD_LINES_INVALID_SIZE_VALUE,
            ["distribution-1.0.dist-info/RECORD", "", "deadbeef"],
        ),
    ],
)
def test_parse_wheel_record_invalid(record_lines, invalid_row):
    """Parser raises ValueError on invalid RECORD.
    """
    with pytest.raises(ValueError) as ctx:
        list(parse_record_file(record_lines))
    assert str(ctx.value) == "invalid row 1: {!r}".format(invalid_row)


def test_write_record(record_simple):
    record_items = [RecordItem.parse(*row.split(",")) for row in record_simple]

    buffer = _get_csv_io()
    write_record_file(buffer, record_items)

    expected = "\r\n".join(sorted(record_simple)) + "\r\n"
    assert buffer.getvalue() == expected


# Record item describing a file "greeting" with content b"Hello".
HELLO_RECORD_ITEM = RecordItem(
    path=pathlib.PurePosixPath("greeting"),
    hash_=Hash(name="sha256", value="GF-NsyJx_iX1Yab8k4suJkMG7DBO2lGAB9F2SCY4GWk="),
    size=5,
)


@pytest.mark.parametrize(
    "record_item, data, exc_type",
    [
        (HELLO_RECORD_ITEM, b"Hell", RecordItemSizeMismatch),
        (HELLO_RECORD_ITEM, b"Hell!", RecordItemHashMismatch),
    ],
)
def test_record_item_validation(record_item, data, exc_type):
    with pytest.raises(RecordItemError) as ctx:
        record_item.raise_for_validation(data)
    assert ctx.type == exc_type
