.. _installer.records:

===============
RECORD handling
===============

An important part of handling wheels is reading and (re)generating :pep:`376`
RECORD files. The ``installer.records`` module provides an object-oriented
model for the same.

.. autofunction:: installer.records.parse_record_file

.. autoclass:: installer.records.Record()
    :special-members: __init__
    :members:

.. autoclass:: installer.records.Hash()
    :special-members: __init__
    :members:
