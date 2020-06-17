import pytest

from installer.records import InvalidRecord, parse_record_file


#
# pytest fixture witchcraft
#
@pytest.fixture()
def record_simple_list():
    return [
        "file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
        "distribution-1.0.dist-info/RECORD,,",
    ]


@pytest.fixture()
def record_simple_iter(record_simple_list):
    return iter(record_simple_list)


@pytest.fixture()
def record_simple_file(tmpdir, record_simple_list):
    p = tmpdir.join("RECORD")
    p.write("\n".join(record_simple_list))
    with open(str(p)) as f:
        yield f


@pytest.fixture()
def record_input(request):
    return request.getfixturevalue(request.param)


#
# Actual Tests
#
class TestParseRecordFile:
    def test_accepts_empty_iterable(self):
        list(parse_record_file([]))

    @pytest.mark.parametrize(
        "record_input",
        ["record_simple_list", "record_simple_iter", "record_simple_file"],
        indirect=True,
    )
    def test_accepts_all_kinds_of_iterables(self, record_input):
        """Should accepts any iterable, e.g. container, iterator, or file object.
        """
        records = list(parse_record_file(record_input))
        assert len(records) == 2

        r0 = records[0]
        assert r0.path == "file.py"
        assert r0.hash_.name == "sha256"
        assert r0.hash_.value == "AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI"
        assert r0.size == 3144

        r1 = records[1]
        assert r1.path == "distribution-1.0.dist-info/RECORD"
        assert r1.hash_ is None
        assert r1.size is None

    @pytest.mark.parametrize(
        "line, element_count",
        [
            ("file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144,", 4),
            ("distribution-1.0.dist-info/RECORD,,,,", 5),
        ],
    )
    def test_rejects_wrong_element_count(self, line, element_count):
        with pytest.raises(InvalidRecord) as exc_info:
            list(parse_record_file([line]))

        message = "expected 3 elements, got {}".format(element_count)
        assert message in str(exc_info.value)

    def test_shows_correct_row_number(self):
        record_lines = [
            "file1.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
            "file2.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
            "file3.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
            "distribution-1.0.dist-info/RECORD,,,,",
        ]
        with pytest.raises(InvalidRecord) as exc_info:
            list(parse_record_file(record_lines))

        assert "Row Index 3" in str(exc_info.value)
