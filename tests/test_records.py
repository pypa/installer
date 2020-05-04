import pytest

from installer.records import SuperfluousRecordColumnsWarning, parse_record_file


@pytest.fixture()
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

    with pytest.warns(SuperfluousRecordColumnsWarning) as ws:
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
