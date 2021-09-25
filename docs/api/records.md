```{caution}
This API is not finalised, and may change in a patch version.
```

# `installer.records`

```{eval-rst}
.. automodule:: installer.records
```

## Example

```{doctest} pycon
>>> from installer.records import parse_record_file, RecordEntry
>>> lines = [
...     "file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
...     "distribution-1.0.dist-info/RECORD,,",
... ]
>>> records = parse_record_file(lines)
>>> li = list(records)
>>> len(li)
2
>>> record_tuple = li[0]
>>> record_tuple
('file.py', 'sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI', '3144')
>>> record = RecordEntry.from_elements(*record_tuple)
>>> record
RecordEntry(path='file.py', hash_=Hash(name='sha256', value='AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI'), size=3144)
>>> record.path
'file.py'
>>> record.hash_
Hash(name='sha256', value='AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI')
>>> record.size
3144
>>> record.validate(b"...")
False
```

## Reference

```{eval-rst}
.. autofunction:: installer.records.parse_record_file

.. autoclass:: installer.records.RecordEntry()
    :special-members: __init__
    :members:

.. autoclass:: installer.records.Hash()
    :special-members: __init__
    :members:
```
