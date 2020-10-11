# RECORD file handling

`installer.records` provides an object-oriented model for reading and handling
{pep}`376` RECORD files.

## Usage

```pycon
>>> from installer.records import parse_record_file
>>> lines = [
...     "file.py,sha256=AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI,3144",
...     "distribution-1.0.dist-info/RECORD,,",
... ]
>>> records = parse_record_file(lines)
>>> li = list(records)
>>> len(li)
2
>>> record = li[0]
>>> record
Record(path='file.py', hash_=Hash(name='sha256', value='AVTFPZpEKzuHr7OvQZmhaU3LvwKz06AJw8mT\\_pNh2yI'), size=3144)
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
.. automodule:: installer.records

.. autofunction:: installer.records.parse_record_file

.. autoclass:: installer.records.Record()
    :special-members: __init__
    :members:

.. autoclass:: installer.records.Hash()
    :special-members: __init__
    :members:
```
