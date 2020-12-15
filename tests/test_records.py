import pytest

from installer.records import Hash, InvalidRecord, Record, parse_record_file


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


SAMPLE_RECORDS = [
    (
        ("test1.py", "sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4", 6),
        b"test1\n",
        True,
    ),
    (
        ("test2.py", "sha256=fW_Xd08Nh2JNptzxbQ09EEwxkedx--LznIau1LK_Gg8", 6),
        b"test2\n",
        True,
    ),
    (
        ("test3.py", "sha256=qwPDTx7OCCEf4qgDn9ZCQZmz9de1X_E7ETSzZHdsRcU", 6),
        b"test3\n",
        True,
    ),
    (
        ("test4.py", "sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4", 7),
        b"test1\n",
        False,
    ),
    (
        (
            "test5.py",
            "sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4",
            None,
        ),
        b"test1\n",
        True,
    ),
    (("test6.py", None, None), b"test1\n", True),
]


#
# Actual Tests
#
class TestRecord:
    @pytest.mark.parametrize(
        "path, hash_, size, caused_by",
        [
            ("", "", "", ["path"]),
            ("", "", "non-int", ["path", "size"]),
            ("a.py", "", "non-int", ["size"]),
            # Notice that we're explicitly allowing non-compliant hash values
            ("a.py", "some-random-value", "non-int", ["size"]),
        ],
    )
    def test_invalid_elements(self, path, hash_, size, caused_by):
        with pytest.raises(InvalidRecord) as exc_info:
            Record.from_elements(path, hash_, size)

        assert exc_info.value.elements == (path, hash_, size)
        for word in caused_by:
            assert word in str(exc_info.value)

    @pytest.mark.parametrize(
        "path, hash_, size",
        [
            ("a.py", "", ""),
            ("a.py", "", "3144"),
            ("a.py", "sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI", ""),
            ("a.py", "sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI", "3144"),
        ],
    )
    def test_valid_elements(self, path, hash_, size):
        Record.from_elements(path, hash_, size)

    @pytest.mark.parametrize(("elements", "data", "passes_validation"), SAMPLE_RECORDS)
    def test_populates_attributes_correctly(self, elements, data, passes_validation):
        path, hash_string, size = elements

        record = Record.from_elements(path, hash_string, size)

        assert record.path == path
        assert record.size == size

        if record.hash_ is not None:
            assert isinstance(record.hash_, Hash)
            assert record.hash_.name == "sha256"
            assert record.hash_.value == hash_string[len("sha256=") :]

    @pytest.mark.parametrize(("elements", "data", "passes_validation"), SAMPLE_RECORDS)
    def test_validation(self, elements, data, passes_validation):
        record = Record.from_elements(*elements)
        assert record.validate(data) == passes_validation

    @pytest.mark.parametrize(("elements", "data", "passes_validation"), SAMPLE_RECORDS)
    def test_string_representation(self, elements, data, passes_validation):
        record = Record.from_elements(*elements)

        expected_string_value = ",".join(
            [(str(elem) if elem is not None else "") for elem in elements]
        )
        assert str(record) == expected_string_value

    def test_eq(self):
        assert Record("a.py", "sha256=foobar", "3144") == Record(
            "a.py", "sha256=foobar", "3144"
        )

    def test_eq_with_other_type(self):
        assert not Record("a.py", "sha256=foobar", "3144") == object

    @pytest.mark.parametrize(
        "a,b",
        [
            [
                Record("a.py", "sha256=foobar", "100"),
                Record("b.py", "sha256=foobar", "100"),
            ],
            [
                Record("a.py", "sha256=foobar", "100"),
                Record("a.py", "sha256=foobar", "200"),
            ],
            [
                Record("a.py", "sha256=foobar", "100"),
                Record("a.py", "sha256=baz", "100"),
            ],
            [Record("a.py", "sha256=foobar", "100"), object],
        ],
    )
    def test_neq(self, a, b):
        assert a != b


class TestParseRecordFile:
    def test_accepts_empty_iterable(self):
        list(parse_record_file([]))

    @pytest.mark.parametrize(
        "record_input",
        ["record_simple_list", "record_simple_iter", "record_simple_file"],
        indirect=True,
    )
    def test_accepts_all_kinds_of_iterables(self, record_input):
        """Should accepts any iterable, e.g. container, iterator, or file object."""
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


class TestHash:
    def test_eq(self):
        assert Hash(name="sha256", value="somehash") == Hash(
            name="sha256", value="somehash"
        )

    def test_eq_with_other_type(self):
        assert not Hash(name="sha256", value="somehash") == object

    @pytest.mark.parametrize(
        "a,b",
        [
            [
                Hash(name="sha256", value="somehash"),
                Hash(name="sha256", value="someotherhash"),
            ],
            [
                Hash(name="sha256", value="somehash"),
                Hash(name="sha1", value="somehash"),
            ],
            [
                Hash(name="sha256", value="somehash"),
                Hash(name="sha1", value="someotherhash"),
            ],
            [Hash(name="sha256", value="somehash"), object],
        ],
    )
    def test_neq(self, a, b):
        assert a != b
