import pytest

from installer.records import Hash, InvalidRecordEntry, RecordEntry, parse_record_file


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
        "purelib",
        ("test1.py", "sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4", 6),
        b"test1\n",
        True,
    ),
    (
        "purelib",
        ("test2.py", "sha256=fW_Xd08Nh2JNptzxbQ09EEwxkedx--LznIau1LK_Gg8", 6),
        b"test2\n",
        True,
    ),
    (
        "purelib",
        ("test3.py", "sha256=qwPDTx7OCCEf4qgDn9ZCQZmz9de1X_E7ETSzZHdsRcU", 6),
        b"test3\n",
        True,
    ),
    (
        "purelib",
        ("test4.py", "sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4", 7),
        b"test1\n",
        False,
    ),
    (
        "purelib",
        (
            "test5.py",
            "sha256=Y0sCextp4SQtQNU-MSs7SsdxD1W-gfKJtUlEbvZ3i-4",
            None,
        ),
        b"test1\n",
        True,
    ),
    ("purelib", ("test6.py", None, None), b"test1\n", True),
]


#
# Actual Tests
#
class TestRecordEntry:
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
        with pytest.raises(InvalidRecordEntry) as exc_info:
            RecordEntry.from_elements(path, hash_, size)

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
        RecordEntry.from_elements(path, hash_, size)

    @pytest.mark.parametrize(
        ("scheme", "elements", "data", "passes_validation"), SAMPLE_RECORDS
    )
    def test_populates_attributes_correctly(
        self, scheme, elements, data, passes_validation
    ):
        path, hash_string, size = elements

        record = RecordEntry.from_elements(path, hash_string, size)

        assert record.path == path
        assert record.size == size

        if record.hash_ is not None:
            assert isinstance(record.hash_, Hash)
            assert record.hash_.name == "sha256"
            assert record.hash_.value == hash_string[len("sha256=") :]

    @pytest.mark.parametrize(
        ("scheme", "elements", "data", "passes_validation"), SAMPLE_RECORDS
    )
    def test_validation(self, scheme, elements, data, passes_validation):
        record = RecordEntry.from_elements(*elements)
        assert record.validate(data) == passes_validation

    @pytest.mark.parametrize(
        ("scheme", "elements", "data", "passes_validation"), SAMPLE_RECORDS
    )
    def test_string_representation(self, scheme, elements, data, passes_validation):
        record = RecordEntry.from_elements(*elements)

        expected_row = tuple(
            [(str(elem) if elem is not None else "") for elem in elements]
        )
        assert record.to_row() == expected_row

    @pytest.mark.parametrize(
        ("scheme", "elements", "data", "passes_validation"), SAMPLE_RECORDS
    )
    def test_string_representation_with_prefix(
        self, scheme, elements, data, passes_validation
    ):
        record = RecordEntry.from_elements(*elements)

        expected_row = tuple(
            [
                (str(elem) if elem is not None else "")
                for elem in ("prefix/" + elements[0], elements[1], elements[2])
            ]
        )
        assert record.to_row("prefix/") == expected_row

    def test_equality(self):
        record = RecordEntry.from_elements(
            "file.py",
            "sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI",
            "3144",
        )
        record_same = RecordEntry.from_elements(
            "file.py",
            "sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI",
            "3144",
        )
        record_different_name = RecordEntry.from_elements(
            "file2.py",
            "sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI",
            "3144",
        )
        record_different_hash_name = RecordEntry.from_elements(
            "file.py",
            "md5=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI",
            "3144",
        )
        record_different_hash_value = RecordEntry.from_elements(
            "file.py",
            "sha256=qwertyuiodfdsflkgshdlkjghrefawrwerwffsdfflk29",
            "3144",
        )
        record_different_size = RecordEntry.from_elements(
            "file.py",
            "sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI",
            "10",
        )

        assert record == record_same

        assert record != "random string"
        assert record != record_different_name
        assert record != record_different_hash_name
        assert record != record_different_hash_value
        assert record != record_different_size

        # Ensure equality is based on current state
        record_same.hash_ = None
        assert record != record_same


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

        assert records == [
            (
                "file.py",
                "sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI",
                "3144",
            ),
            ("distribution-1.0.dist-info/RECORD", "", ""),
        ]

    @pytest.mark.parametrize(
        "line, element_count",
        [
            pytest.param(
                "file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144,",
                4,
                id="four",
            ),
            pytest.param(
                "distribution-1.0.dist-info/RECORD,,,,",
                5,
                id="five",
            ),
        ],
    )
    def test_rejects_wrong_element_count(self, line, element_count):
        with pytest.raises(InvalidRecordEntry) as exc_info:
            list(parse_record_file([line]))

        message = f"expected 3 elements, got {element_count}"
        assert message in str(exc_info.value)

    def test_shows_correct_row_number(self):
        record_lines = [
            "file1.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
            "file2.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
            "file3.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
            "distribution-1.0.dist-info/RECORD,,,,",
        ]
        with pytest.raises(InvalidRecordEntry) as exc_info:
            list(parse_record_file(record_lines))

        assert "Row Index 3" in str(exc_info.value)

    def test_parse_record_entry_with_comma(self):
        record_lines = [
            '"file1,file2.txt",sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144',
            "distribution-1.0.dist-info/RECORD,,",
        ]
        records = list(parse_record_file(record_lines))
        assert records == [
            (
                "file1,file2.txt",
                "sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI",
                "3144",
            ),
            ("distribution-1.0.dist-info/RECORD", "", ""),
        ]

    def test_parse_record_entry_with_backslash_path(self):
        record_lines = [
            "distribution-1.0.dist-info\\RECORD,,",
        ]
        records = list(parse_record_file(record_lines))
        assert records == [
            ("distribution-1.0.dist-info/RECORD", "", ""),
        ]
