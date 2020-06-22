====================
Welcome to installer
====================

.. note::

    This package is currently a work-in-progress, and not ready for production
    use.

``installer`` is a library that provides basic functionality and abstractions
for installing a Python package from a `Wheel distribution`_.

.. _`Wheel distribution`: https://packaging.python.org/glossary/#term-wheel


Example
=======

Installing a local wheel file into the current interpreter, using ``sysconfig``
for getting relevant locations, can be done as follows:

.. code-block:: python

    import sysconfig

    from installer import Installer
    from installer.destinations import DictDestination
    from installer.sources import WheelFile

    source = WheelFile("sampleproject-1.3.1-py2.py3-none-any.whl")
    destination = SchemeDictDestination(sysconfig.get_config_vars())

    example_installer = Installer(name="example")
    example_installer.install(source, destination)

.. toctree::
    :maxdepth: 2
    :hidden:

    api/index
