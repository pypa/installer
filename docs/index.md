---
hide-toc: true
---

# Welcome to installer's documentation

This is a low-level library for installing a Python package from a
[wheel distribution](Wheel). It provides basic functionality and
abstractions for handling wheels and installing packages from wheels.

- Logic for "unpacking" a wheel (i.e. installation).
- Abstractions for various parts of the unpacking process.
- Extensible simple implementations of the abstractions.
- Platform-independent Python script wrapper generation.

```{toctree}
:hidden:

concepts
```

```{toctree}
:caption: API reference
:hidden:
:glob:

api/*
```

```{toctree}
:caption: Project
:hidden:

development/index
changelog
license
GitHub <https://github.com/pradyunsg/installer>
PyPI <https://pypi.org/project/installer>
```

## Basic Usage

```python
import sysconfig

from installer import install
from installer.destinations import SchemeDictDestination
from installer.sources import WheelFile

# This represents the wheel file, and handle reading from it.
source = WheelFile("sampleproject-1.3.1-py2.py3-none-any.whl")

# This represents the installation directories, and writes to them.
destination = SchemeDictDestination(sysconfig.get_config_vars())

# This is the additional metadata, generated during installation.
additional_metadata = {
    "INSTALLER": b"amazing-installer 0.1.0",
}

install(
    source=source,
    destination=destination,
    additional_metadata=additional_metadata,
)
```

```{attention}
The `WheelFile` class mentioned above has not been implemented yet.
Contributions are welcome!
```
