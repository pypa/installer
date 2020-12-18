---
hide-toc: true
---

# Welcome to installer

This is a low-level library for installing a Python package from a
[wheel distribution]. It provides basic functionality and abstractions
for handling wheels and installing packages from wheels.

```{toctree}
:caption: API documentation
:hidden:

api/core
api/sources
api/destinations
api/records
api/scripts
api/utils
```

```{caution}
This project is still a work in progress, so the API is not stabilised yet.
```

## Example

Installing a local wheel file into the current interpreter, using ``sysconfig``
for getting relevant locations, can be done as follows:

```python
import sysconfig

from installer import Installer
from installer.destinations import DictDestination
from installer.sources import WheelFile

source = WheelFile("sampleproject-1.3.1-py2.py3-none-any.whl")
destination = SchemeDictDestination(sysconfig.get_config_vars())

amazing_installer = Installer(name="amazing-installer")
amazing_installer.install(source, destination)
```

All these objects implement specific abstractions, which are described in
this documentation.

[Wheel distribution]: https://packaging.python.org/glossary/#term-wheel
